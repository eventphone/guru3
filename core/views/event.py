from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction, connection
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, Http404, JsonResponse
from django.urls import reverse
from django.utils.functional import cached_property
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.views.generic import FormView

from core import messaging
from core.forms.event import EventInviteForm
from core.models import Event, Extension, CallGroupInvite, ExtensionClaim, WireMessage
from core.session import setCurrentEvent, getCurrentEvent
from core.tasks import create_event_invites, send_claim_emails, sync_event_to_mgr
from core.utils import retry_on_db_deadlock, task_url
from gcontrib.views.list import SearchView
from gcontrib.views.mixins import FormHelperMixin
from gcontrib.views.task import JobProcessingView


@csrf_exempt
def eventSelectionView(request, pk):
    try:
        event = Event.objects.get(pk=pk)
        setCurrentEvent(request, event)
    except Event.DoesNotExist:
        pass

    old_path = request.POST.get("path", "/")
    return HttpResponseRedirect(old_path)


def eventImportFunction(request, cls, pk):
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        raise Http404

    results = []
    extensions = Extension.objects.filter(event=settings.PERMANENT_EVENT_ID).order_by("extension")
    for extension in extensions:
        conflicts = event.getConflictingExtensions(extension.extension)
        if len(conflicts) == 0:
            extension.copyToEvent(event)
            results.append({
                "extension": extension,
                "status": "OK",
            })
        else:
            results.append({
                "extension": extension,
                "status": "CONFLICT",
                "conflict": conflicts,
            })

    groups = Extension.objects.filter(event=settings.PERMANENT_EVENT_ID, type="GROUP").order_by("extension")
    for group in groups:
        group.syncGroupToEvent(event)

    cls.add_context("results", results)
    cls.add_context("event", event)
    return cls.render_template()

@require_POST
def eventSyncView(request, pk):
    try:
        event =  Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        raise Http404
    task = sync_event_to_mgr.delay(pk)
    return JsonResponse({
        "task_url": task_url(task),
        "next_view": reverse("event.list"),
    })


class CurrentEventMixin(object):
    event = None

    def get_event(self):
        if self.event is not None:
            return self.event
        self.event = getCurrentEvent(self.request)
        if self.event is None:
            raise Http404
        return self.event


class EventInviteView(FormHelperMixin, FormView):
    form_class = EventInviteForm
    form_submit_button_text = "Create invites"

    @cached_property
    def event(self):
        try:
            return Event.objects.get(pk=self.kwargs["pk"])
        except Event.DoesNotExist:
            raise Http404

    def get_context_data(self, **kwargs):
        event = self.event
        kwargs["event"] = event
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        event = self.event
        from_event = form.cleaned_data["from_event"]
        deadline = form.cleaned_data["deadline"]
        task = create_event_invites.delay(from_event.pk, event.pk, deadline.isoformat())

        return JsonResponse({
            "task_url": task_url(task),
            "next_view": reverse("event.list")
        })


class ClaimEmailSendView(JobProcessingView):
    @cached_property
    def event(self):
        try:
            return Event.objects.get(pk=self.kwargs["pk"])
        except Event.DoesNotExist:
            raise Http404

    def post(self, request, *args, **kwargs):
        event = self.event
        task = send_claim_emails.delay(event.pk)
        return JsonResponse({
            "task_url": task_url(task),
        })

    def get(self, request, *args, **kwargs):
        self.add_context("event", self.event)
        self.add_context("num_claims", ExtensionClaim.objects.filter(event=self.event, mail_sent=False).count())
        return self.render_template()


class OrgaUpgradeView(JobProcessingView):
    @cached_property
    def event(self):
        try:
            return Event.objects.get(orgaKey=self.kwargs.get("orga_key", None))
        except Event.DoesNotExist:
            raise PermissionDenied

    def post(self, request, *args, **kwargs):
        event = self.event
        event.organizers.add(request.user)
        event.save()
        setCurrentEvent(request, event)
        return self.redirect_to(reverse("event.orga_phonebook"))

    def get(self, request, *args, **kwargs):
        event = self.event
        self.add_context("isAlreadyOrganizer", event.organizers.filter(pk=request.user.pk).exists())

        self.add_context("event", self.event)
        return self.render_template()


class MgrKeyCreationView(JobProcessingView):
    def get_event(self):
        try:
            return Event.objects.get(pk=self.kwargs.get("pk", ""))
        except Event.DoesNotExist:
            raise Http404

    def get(self, request, *args, **kwargs):
        event = self.get_event()
        self.add_context("event", event)
        return self.render_template()

    def post(self, request, *args, **kwargs):
        event = self.get_event()
        mgr_key = event.regenerate_mgr_key()
        self.add_context("event", event)
        self.add_context("mgr_key", mgr_key)
        self.add_context("new_key", True)
        return self.render_template()

class GelbeSeitenView(SearchView):
    @xframe_options_exempt
    def get(self, request, *args, **kwargs):
        return super().get(self, request, args, kwargs)