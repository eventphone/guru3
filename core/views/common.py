import json

import celery.exceptions
from celery.result import AsyncResult
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Prefetch
from django.http import Http404, JsonResponse, HttpResponseBadRequest, HttpResponse
from django.template.response import TemplateResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

from core import messaging
from core.models import PERM_ORGA, Event, Extension, WireMessage, IncomingWireMessage, InventoryLend
from core.session import getCurrentEvent
from guru3.consumers import notify_clients


def phonebookSearch(query, request):
    event = getCurrentEvent(request)
    if event is None:
        raise Http404
    if not event.isPhonebookPublic() and not request.user.is_authenticated:
        raise PermissionDenied

    results = event.searchExtensions(query)
    return results.filter(inPhonebook=True)

def gelbeseitenSearch(query, request):
    results = phonebookSearch(query, request)
    return results.exclude(name__isnull=True).exclude(name__exact='')

def orga_phonebook_search(query, request):
    event = getCurrentEvent(request)
    if event is None:
        raise Http404

    extensionResults = event.searchExtensions(query)    
    ownerResults = Extension.objects.filter(event=event, owner__username__icontains=query)
    return (extensionResults | ownerResults)\
        .distinct()\
        .filter(owner__organizedEvents=event).prefetch_related(
        Prefetch("inventorylend_set", queryset=InventoryLend.objects.filter(backDate__isnull=True)
                                                                    .select_related("item", "item__itemType"),
                 to_attr="active_lendings")
    )


def celery_task_status_view(request, taskid):
    result = AsyncResult(taskid)
    if not result.ready():
        try:
            result.get(timeout=0.5, propagate=False)
        except celery.exceptions.TimeoutError:
            pass
    response_data = {
        "status": result.status,
    }
    if result.info is not None:
        if isinstance(result.info, Exception):
            response_data["info"] = f"{result.info.__class__.__name__}: {str(result.info)}"
        else:
            response_data["info"] = result.info if isinstance(result.info, dict) or isinstance(result.info, list) \
                else str(result.info)

    return JsonResponse(response_data)


def vacationView(request):
    vr = TemplateResponse(request, "vacation.html", {})
    return vr


@csrf_exempt
@require_http_methods(["GET", "POST"])
def wireMessageView(request, pk, event=None):
    mgr_key_event = event
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        raise Http404
    if mgr_key_event is not None and mgr_key_event != event:
        raise PermissionDenied

    if request.method == "GET":
        max_messages = request.GET.get("max_messages", "10")
        if not max_messages.isnumeric():
            return HttpResponseBadRequest()
        max_messages = int(max_messages)
        msgs = WireMessage.objects.filter(event=event, delivered=False).order_by("timestamp", "pk")[:max_messages]
        data = [msg.getWireData() for msg in msgs]
        return JsonResponse(data, safe=False)
    elif request.method == "POST":
        acklistStr = request.POST.get("acklist", "")
        messagesStr = request.POST.get("messages")
        try:
            acklist = json.loads(acklistStr)
            if messagesStr is not None:
                messages = json.loads(messagesStr)
            else:
                messages = []
        except json.decoder.JSONDecodeError as e:
            print(str(e))
            return HttpResponseBadRequest()
        if type(acklist) != list:
            return HttpResponseBadRequest()
        if type(messages) != list:
            return HttpResponseBadRequest()
        if any([type(e) != int for e in acklist]):
            return HttpResponseBadRequest()

        WireMessage.objects.filter(pk__in=acklist).update(delivered=True)
        notify_clients(pk,{"action": "messagecount",
                           "queuelength": WireMessage.objects.filter(event=pk, delivered=False).count()})

        message_results = []
        for message in messages:
            remote_id, status, msg = process_incoming_message(message, event)
            message_results.append({
                "id": remote_id,
                "status": status,
                "text": msg,
            })

        result = {
            "messages": message_results,
        }

        return JsonResponse(result)


def process_incoming_message(message_data, event):
    remote_id = message_data.get("id")
    try:
        with transaction.atomic():
            wm = IncomingWireMessage.parse_from(message_data)
            wm.event = event
            wm.save()

            msg = messaging.parse_incoming_wiremessage(wm)
            msg.process()
            wm.processed = True
            wm.save()
    except messaging.MessageParsingError as e:
        return remote_id, "NAK", "Parsing error: " + str(e)
    except messaging.MessageProcessingError as e:
        return remote_id, "NAK", "Processing error: " + str(e)

    return remote_id, "OK", ""


class SupportView(TemplateView):
    pass
