import os
import subprocess
import time
from datetime import datetime, timedelta
from smtplib import SMTPRecipientsRefused

from celery.utils.log import get_task_logger
from celery.utils.time import maybe_iso8601
from django.conf import settings
from django.db import transaction, connection
from django.db.models import Q, Count
from django.utils import timezone

from guru3.celery_app import app
from core.utils import retry_on_db_deadlock, batched
from core.models import AudioFile, Extension, ExtensionClaim, CallGroupInvite, WireMessage, Event, InventoryLend, InventoryItemRecallStatus
from core import messaging

logger = get_task_logger(__name__)

RINGBACK_STARTER_SCRIPT = os.path.join(settings.BASE_DIR, "audio_tools", "start_sandbox_processing.sh")
AUDIO_INPUT_DIR = os.path.join(settings.MEDIA_ROOT, "audio")


@app.task(ignore_result=True)
def process_ringback_file(ringback_id):
    try:
        audio = AudioFile.objects.get(pk=ringback_id)
    except AudioFile.DoesNotExist:
        logger.error(f"Should process audio file with id={ringback_id} but wasn't found in DB.")
        return

    audio_filename = os.path.basename(audio.file.name)
    try:
        result = subprocess.run([RINGBACK_STARTER_SCRIPT,
                                 AUDIO_INPUT_DIR, settings.RINGBACK_OUTPUT_DIR, settings.PLAIN_AUDIO_OUTPUT_DIR,
                                 audio_filename],
                                capture_output=True, timeout=40)

        if result.returncode != 0:
            logger.error(f"Processing of file {audio_filename} failed:\n"
                         f"Process returncode: {result.returncode}\n"
                         f"Stdout: {result.stdout}\n"
                         f"Stderr: {result.stderr}")
        else:
            audio.processed = True
            audio.save()
            return
    except subprocess.TimeoutExpired:
        logger.error(f"Timeout when waiting for {audio_filename} to be processed.")

    audio.processing_error = True
    audio.save()


@app.task
def create_event_invites(from_event, event, deadline):
    deadline = maybe_iso8601(deadline)
    invited_extensions = Extension.objects.filter(event=from_event, owner__isnull=False)
    existing_claims = ExtensionClaim.objects.filter(event=event).values_list("extension", flat=True)
    with transaction.atomic():
        for ext in invited_extensions:
            # if there is already an invite, we ignore it
            if ext.extension in existing_claims:
                continue
            claim = ExtensionClaim.generate(user=ext.owner, extension=ext.extension, event_id=event,
                                            valid_until=deadline)
            claim.save()


@app.task(bind=True)
def send_claim_emails(self, event):
    existing_claims = ExtensionClaim.objects.select_related().filter(event=event, mail_sent=False)

    email_count = len(existing_claims)
    self.update_state(state="PROGRESS", meta={"total": email_count, "done": 0})
    refused_recipients = []
    for idx, claim in enumerate(existing_claims):
        with transaction.atomic():
            try:
                claim.send_invite_email()
            except SMTPRecipientsRefused:
                refused_recipients.append([str(claim.extension), claim.user.email])
            claim.mail_sent = True
            claim.save()

        if idx % 10 == 0:
            self.update_state(state="PROGRESS", meta={"total": email_count, "done": idx})
    return refused_recipients


@retry_on_db_deadlock(max_retries=32, initial_backoff=None)
def attempt_to_sync_event(task_obj, event):
    with transaction.atomic():
        if connection.vendor == "mysql":
            cursor = connection.cursor()
            cursor.execute("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE")

        # mark all undelivered messages as being delivered.
        # As the search condition is the event, our transaction will acquire a record lock on the
        # wire messages of this event.
        # This prevents other transactions from inserting WireMessages while we sync the whole DB
        WireMessage.objects.filter(event=event).delete()
        msg = messaging.SyncStartMsg(event).makeWireMessage()
        msg.save(no_notify=True)
        # retrieve a lock on all relevant extensions and prevent updating/creating further
        extensions = list(Extension.objects.select_for_update().select_related()
                                                               .filter(event=event.pk)
                                                               .prefetch_related("group_members"))
        # retrieve a lock on all relevant callgroup memberships and prevent updating/creating further
        # even though we do not actually use the results
        list(CallGroupInvite.objects.select_for_update().filter(group__event=event.pk))

        # At this point all relevant DB entries and ranges are locked and we can start to sync the event
        # in an exclusive manner without any further interference.

        num_extensions = len(extensions)
        task_obj.update_state(state="PROGRESS", meta={"total": 3*num_extensions, "done": 0})

        # we first transfer all extensions
        for index, ext in enumerate(extensions):
            msg = messaging.makeExtensionUpdateMessage(ext, no_forwards=True)
            msg.save(no_notify=True)
            if index % 200 == 0:
                task_obj.update_state(state="PROGRESS", meta={"total": 3*num_extensions, "done": index})

        # now all those with forward again (to make sure that all forward targets exist as this point)
        extensions = Extension.objects.select_related().filter(event=event.pk, forward_extension__isnull=False) \
                                      .prefetch_related("group_members")
        for index, ext in enumerate(extensions):
            msg = messaging.makeExtensionUpdateMessage(ext)
            msg.save(no_notify=True)
            if index % 200 == 0:
                task_obj.update_state(state="PROGRESS", meta={"total": 3*num_extensions, "done": num_extensions+index})

        # now that all extensions are there, we sync group members / multiring / forward (if necessary)
        groups = Extension.objects.annotate(member_count=Count("group_members")) \
            .filter(event=event.pk).filter(Q(type="GROUP") | Q(member_count__gt=0)) \
            .select_related().prefetch_related("group_members").distinct()
        for index, group in enumerate(groups):
            msg = messaging.makeGroupUpdateMessage(group)
            msg.save(no_notify=True)
            if index % 200 == 0:
                task_obj.update_state(state="PROGRESS", meta={"total": 3*num_extensions,
                                                              "done": 2*num_extensions+index})

        msg = messaging.SyncEndMsg(event).makeWireMessage()
        msg.save(no_notify=True)


@app.task(bind=True)
def sync_event_to_mgr(self, event_id):
    event = Event.objects.get(id=event_id)
    attempt_to_sync_event(self, event)


@app.task
def recall_rental_devices(event_id):
    rental_device_list = InventoryLend.objects.filter(event=event_id, item__itemType__auto_recall=True,
                                                      extension__isnull=False,
                                                      backDate__isnull=True, inventoryitemrecallstatus__isnull=True)
    with transaction.atomic():
        batch_start = datetime.now()
        for batch in batched(rental_device_list, 5):
            for lending in batch:
                recaller = InventoryItemRecallStatus(lending=lending, call_attempt=0, next_escalation=batch_start)
                recaller.save()
            batch_start = batch_start + timedelta(minutes=1)

    rental_recall_do_progress.delay(event_id)


RENTAL_BASE_ESCALATION_PERIOD = timedelta(minutes=10)
RENTAL_ESCALATION_AUDIO_ARRAY = [
    "3c5902faf2257a8aa5c4e1653102fecae29b36d212d4824fc33fd2dd1290af2f6014980f5ef33b711d6a8b074d4a714e9f8a32f49c76667867735bd632c98cc7",
    "08aef0fa4dff390ac0e27dff7255b4a1c714538d08a1b5e7fc5f1c0f4b40fccbe05274ca470a2291ce541668da3b0a0fc4d970873afb1ea136761bc2b46811b5",
    "c87711cc6a173f13bd09c8fdbad82687d37bc858c8fa2b6414534e2bb343bf4e2ec5eaf59de494a2025c9060d771e436d245933e1fa3b2f38d0fca53c58100bb",
    "93a9944c5cab2fd3a4432e3de83b31a5d5b3143feb5c5762b6375ffc16306ca9e5b341ba7b375d0b47142be2d6b98ae26c182a6f50d4eeed223a4727a9a1393f",
]
RENTAL_CALLER = "999"
RENTAL_CALLER_NUMBER = "PoC"

@app.task
def rental_recall_do_progress(event_id):
    with transaction.atomic():
        todos = InventoryItemRecallStatus.objects.select_for_update() \
                                                     .select_related("lending", "lending__extension") \
                                                     .filter(lending__backDate__isnull=True,lending__event=event_id,
                                                             next_escalation__lte=datetime.now())
        for todo in todos:
            audio = RENTAL_ESCALATION_AUDIO_ARRAY[todo.call_attempt] if todo.call_attempt < len(RENTAL_ESCALATION_AUDIO_ARRAY) else RENTAL_ESCALATION_AUDIO_ARRAY[-1]
            m = messaging.CallExtensionMsg(RENTAL_CALLER_NUMBER,RENTAL_CALLER, todo.lending.extension, audio)
            m.makeWireMessage().save()
            todo.next_escalation = timezone.now() + (RENTAL_BASE_ESCALATION_PERIOD / 2**todo.call_attempt)
            todo.call_attempt += 1
            todo.save()

    ## select the time when the next task if due
    next_todos = InventoryItemRecallStatus.objects.filter(lending__backDate__isnull=True).order_by("next_escalation")
    if next_todos:
        rental_recall_do_progress.apply_async((event_id,), countdown=60)