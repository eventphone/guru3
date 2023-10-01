from django.urls import path, re_path, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView, TemplateView

from gcontrib.decorators import user_is_staff, login_required
from gcontrib.views.edit import CrispyCreateView, CrispyUpdateView, CrispyManyToManyListAddView, ManyToManyDeleteView
from gcontrib.views.list import SearchView, SearchViewWithExtraParams
from gcontrib.views.task import JobProcessingView
from core.decorators import can_access_phonebook, user_is_current_event_admin_or_orga
from core.forms.event import createEventFormhelper, EventForm
from core.forms.extension import generateExtensionForm
from core.models import Event, RentalDeviceClassification, PERM_ORGA, PERM_USER, PERM_USER_READ
from core.session import getCurrentEvent
from core.views.common import phonebookSearch, wireMessageView, orga_phonebook_search, gelbeseitenSearch
from core.views.event import eventSelectionView, eventImportFunction, eventSyncView, EventInviteView,\
                             OrgaUpgradeView, MgrKeyCreationView, ClaimEmailSendView, GelbeSeitenView
from core.views.extension import randomExtensionView

from dal.autocomplete import ModelSelect2


def calculate_rental_device_usage(req, _):
    event = getCurrentEvent(req)
    if not event.isEventAdmin(req.user):
        return []
    else:
        return RentalDeviceClassification.get_event_usage_statistics(event)


urlpatterns = [
    path("new",
         user_is_staff(CrispyCreateView.as_view(
             model=Event,
             form_class=EventForm,
             template_name="event/update.html",
             form_helper=createEventFormhelper(),
             success_url=reverse_lazy("event.list"),
         )),
         name="event.new"),
    path("<int:pk>",
         user_is_staff(CrispyUpdateView.as_view(
             model=Event,
             form_class=EventForm,
             template_name="event/update.html",
             form_helper=createEventFormhelper(),
             success_url=reverse_lazy("event.list"),
         )),
         name="event.edit"),
    path("<int:pk>/delete",
         user_is_staff(DeleteView.as_view(
             model=Event,
             template_name="event/delete.html",
             success_url=reverse_lazy("event.list"),
         )),
         name="event.delete"),
    path("list",
         user_is_staff(TemplateView.as_view(
             template_name="event/list.html",
         )),
         name="event.list"),
    path("<int:pk>/select.exe",
         eventSelectionView,
         name="event.select"),
    path("<int:pk>/import",
         user_is_staff(JobProcessingView.as_view(
             job_function=eventImportFunction,
             template_name="event/import.html",
         )),
         name="event.import"),
    path("<int:pk>/invite",
         user_is_staff(EventInviteView.as_view(
             template_name="event/invite.html",
         )),
         name="event.invite"),
    path("<int:pk>/claim-email",
         user_is_staff(ClaimEmailSendView.as_view(
             template_name="event/claim_email.html",
         )),
         name="event.claim_email"),
    path("<int:pk>/sync-confirm",
         user_is_staff(TemplateView.as_view(
             template_name="event/sync-confirm.html",
         )),
         name="event.sync-confirm"),
    path("<int:pk>/sync",
         user_is_staff(eventSyncView),
         name="event.sync"),
    path("<int:pk>/apikeygen",
         user_is_staff(MgrKeyCreationView.as_view(
             template_name="event/mgr_token.html",
         )),
         name="event.apikeygen"),
    path("<int:pk>/orga/",
         user_is_staff(CrispyManyToManyListAddView.as_view(
             model=Event,
             attribute="organizers",
             template_name="event/orga_helpdesk_list.html",
             extra_form_field_params={
                 "label": _("New organizer"),
                 "widget": ModelSelect2(url="user.autocomplete"),
             }
         )),
         name="event.orga"),
    path("<int:pk>/orga/<int:related_pk>/delete",
         user_is_staff(ManyToManyDeleteView.as_view(
             model=Event,
             attribute="organizers",
             template_name="event/orga_helpdesk_delete.html",
             success_url="../",
         )),
         name="event.orga.delete"),
    path("<int:pk>/helpdesk/",
         user_is_staff(CrispyManyToManyListAddView.as_view(
             model=Event,
             attribute="pocHelpdesk",
             template_name="event/orga_helpdesk_list.html",
             extra_form_field_params={
                 "label": _("New helpdesk person"),
                 "widget": ModelSelect2(url="user.autocomplete"),
             }
         )),
         name="event.helpdesk"),
    path("<int:pk>/helpdesk/<int:related_pk>/delete",
         user_is_staff(ManyToManyDeleteView.as_view(
             model=Event,
             attribute="pocHelpdesk",
             template_name="event/orga_helpdesk_delete.html",
             success_url="../",
         )),
         name="event.helpdesk.delete"),
    path("phonebook",
         can_access_phonebook(SearchView.as_view(
             search_function=phonebookSearch,
             allowed_ordering_keys=["extension", "name", "type", "location"],
             default_ordering_key="extension",
             paginate_by=20,
             template_name="phonebook/list.html",
         )),
         name="event.phonebook"),
    path("orga_phonebook",
         user_is_current_event_admin_or_orga(SearchViewWithExtraParams.as_view(
             search_function=orga_phonebook_search,
             allowed_ordering_keys=["extension", "name", "type", "location", "owner"],
             ordering_map={
                 "owner": "owner__username",
             },
             default_ordering_key="extension",
             paginate_by=20,
             template_name="phonebook/list.html",
             filters=[
                 ("only_open_requests", "assignedRentalDevice__isnull", lambda x: True),
                 ("only_open_requests", "requestedRentalDevice__isnull", lambda x: False),
             ],
             template_params={
                 "quick_create_form": lambda req, _:
                 generateExtensionForm(PERM_ORGA | PERM_USER | PERM_USER_READ, quick_create=True)(
                     event=getCurrentEvent(req), user=req.user, next_url=req.get_full_path()),
                 "rental_usage_statistics": calculate_rental_device_usage,
             }
         )),
         name="event.orga_phonebook"),

    re_path("orga_upgrade/(?P<orga_key>[a-zA-Z0-9]{32})",
            login_required(OrgaUpgradeView.as_view(
                template_name="event/orga_upgrade.html"
            )),
            name="event.orga_upgrade"),
    path("<int:pk>/random",
         randomExtensionView,
         name="event.random"),
    path("gelbeseiten",
         can_access_phonebook(GelbeSeitenView.as_view(
             search_function=gelbeseitenSearch,
             default_ordering_key="name",
             allowed_ordering_keys=["extension", "name", "type", "location"],
             template_name="phonebook/gelbeseiten.html",
         )),
         name="event.gelbeseiten"),
]

