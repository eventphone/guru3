import datetime

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_http_methods
from django.views.generic import UpdateView, CreateView, FormView

from core.forms.extension import generateExtensionForm
from core.models import InventoryLend, Extension, ExtensionClaim, Event, PERM_ORGA
from core.session import getCurrentEvent, extract_signed_url
from core.views.event import CurrentEventMixin
from gcontrib.views.mixins import FormViewPresaveHookMixin, ObjectPermCheckMixin, FormHelperMixin


class ExtensionViewMixin(FormViewPresaveHookMixin):
    my_list_path = None
    admin_list_path = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @cached_property
    def perms(self):
        return self.get_event().getUserPermissions(self.request.user, orga_key=self.kwargs.get("orga_key"))

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["event"] = self.get_event()
        form_kwargs["user"] = self.request.user
        next_url_obj = self.request.GET.get("next_url", None)
        if next_url_obj is not None:
            next_url = extract_signed_url(self.request, next_url_obj)
            if next_url is not None:
                form_kwargs["next_url"] = next_url
        return form_kwargs

    def get_form(self, form_class=None):
        event = self.get_event()
        form_class = generateExtensionForm(self.perms)
        form_kwargs = self.get_form_kwargs()
        return form_class(**form_kwargs)

    def get_success_url(self):
        return self.my_list_path

    def form_valid(self, form):
        result = super().form_valid(form)
        object = form.instance
        # manage lending field is needed as a post save hook, as the extension should be stored first
        if "lending" in form.fields:
            initial = form.fields["lending"].initial
            current = form.cleaned_data["lending"]

            if current is not None and initial != current.barcode:
                # the lending was changed
                with transaction.atomic():
                    if initial is not None:
                        # end old lending
                        lending = object.getCurrentLending()
                        lending.backDate = datetime.datetime.now()
                        lending.save()
                    newLending = InventoryLend(event=object.event,
                                               extension=object,
                                               item=current,
                                               lender=object.name)
                    newLending.save()
            elif initial is not None and current is None:
                lending = object.getCurrentLending()
                lending.backDate = datetime.datetime.now()
                lending.save()

        next_url = form.cleaned_data.get("next_url")
        if next_url is not None and next_url != "":
            return HttpResponseRedirect(next_url)

        return result


class ExtensionUpdateView(ExtensionViewMixin, ObjectPermCheckMixin, UpdateView):
    model = Extension

    def get_event(self):
        return self.get_object().event


class ExtensionCreateView(ExtensionViewMixin, CurrentEventMixin, CreateView):
    model = Extension

    @cached_property
    def claim(self):
        if "claim" in self.request.GET:
            try:
                claim = ExtensionClaim.objects.get(token=self.request.GET["claim"])
                if claim.user != self.request.user:
                    raise PermissionDenied
                return claim
            except ExtensionClaim.DoesNotExist:
                pass
        return None

    def get_form_kwargs(self, form_class=None):
        form_kwargs = super().get_form_kwargs()
        if self.claim is not None:
            form_kwargs["initial"] = {"extension": self.claim.extension}
        return form_kwargs

    def get_event(self):
        if self.claim is not None:
            return self.claim.event
        elif "orga_key" in self.kwargs and self.kwargs["orga_key"] != "":
            try:
                return Event.objects.get(orgaKey=self.kwargs["orga_key"])
            except Event.DoesNotExist:
                pass

        return super().get_event()

    def pre_save_hook(self, object, form):
        # Set owner and event from environment
        if object.owner is None and not self.request.user.is_staff:
            object.owner = self.request.user
        object.event = self.get_event()

        return super(ExtensionCreateView, self).pre_save_hook(object, form)


@require_http_methods(["POST"])
def dectUnsubscribe(request, pk):
    extension = get_object_or_404(Extension, pk=pk)
    if not extension.has_write_permission(request.user):
        raise PermissionDenied
    extension.handset = None
    extension.save(no_messaging=True)
    extension.unsubscribe_device()
    return HttpResponseRedirect(reverse("extension.my"))


@require_http_methods(["POST"])
def rentalDeviceApprove(request, pk):
    extension = get_object_or_404(Extension, pk=pk)
    extension.assignedRentalDevice = extension.requestedRentalDevice
    extension.save()
    return HttpResponseRedirect(request.POST.get("next_url", "/"))

def extensionListSearch(query, request):
    event = getCurrentEvent(request)
    if event is None:
        raise Http404

    extensionResults = event.searchExtensions(query)
    ownerResults = Extension.objects.filter(event=event, owner__username__icontains=query)
    return (extensionResults | ownerResults).distinct()


@require_http_methods(["GET"])
def randomExtensionView(request, pk):
    try:
        event = Event.objects.get(pk=pk)
    except Event.DoesNotExist:
        raise Http404
    free = event.getRandomFreeExtension()

    return HttpResponse(free)


@require_http_methods(["POST"])
def regenerateSipPassword(request, pk):
    extension = get_object_or_404(Extension, pk=pk)
    if extension.type != "SIP":
        raise Http404
    if not extension.has_write_permission(request.user):
        raise PermissionDenied
    extension.generateSipPassword()
    extension.save()
    return HttpResponseRedirect(reverse("extension.my"))
