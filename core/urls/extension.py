from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import path, re_path, reverse_lazy
from django.views.generic import TemplateView

from gcontrib.decorators import user_is_staff
from gcontrib.views.detail import PermCheckFlexibleTemplateDetailView
from gcontrib.views.edit import PermCheckDeleteView
from gcontrib.views.list import SearchView
from gcontrib.views.meta import FlexibleTemplateView
from core.decorators import user_is_current_event_admin
from core.models import Extension, Event, CallGroupInvite
from core.views.extension import ExtensionCreateView, ExtensionUpdateView, extensionListSearch, dectUnsubscribe, \
    rentalDeviceApprove, regenerateSipPassword
from core.views.callgroup import MultiringMembershipView

urlpatterns = [
    path("new",
        login_required(ExtensionCreateView.as_view(
            template_name ="extension/update.html",
            my_list_path = reverse_lazy("extension.my"),
        )),
        name = "extension.new"),
    path("<int:pk>",
        login_required(ExtensionUpdateView.as_view(
            template_name ="extension/update.html",
            my_list_path = reverse_lazy("extension.my"),
        )),
        name = "extension.edit"),
    path("<int:pk>/multiring",
         login_required(MultiringMembershipView.as_view(
             template_name="extension/multiring_editor.html",
         )),
         name="extension.multiring"),
    path("<int:pk>/references",
         login_required(PermCheckFlexibleTemplateDetailView.as_view(
             model=Extension,
             queryset=Extension.objects.select_related().prefetch_related("forwards_here"),
             template_params={
                "invites": lambda _, kwargs: CallGroupInvite.objects.select_related()
                                                                    .filter(extension=kwargs["pk"])
                                                                    .order_by("group__extension")
             },
             template_name="extension/references.html",
         )),
         name="extension.references"),
    path("<int:pk>/delete",
        login_required(PermCheckDeleteView.as_view(
            model = Extension,
            template_name ="extension/delete.html",
            with_next = True,
            success_url = lambda self : self.get_next_view_path(),
        )),
        name = "extension.delete"),
    path("<int:pk>/unsubscribe",
         login_required(dectUnsubscribe),
         name = "extension.unsubscribe"),
    path("<int:pk>/regeneratesippw",
         login_required(regenerateSipPassword),
         name="extension.regeneratesippassword"),
    path("<int:pk>/rental_approve",
         user_is_current_event_admin(rentalDeviceApprove),
         name="extension.rental_approve"),
    path("list",
        user_is_current_event_admin(SearchView.as_view(
            search_function = extensionListSearch,
            allowed_ordering_keys = ["extension", "name", "type", "location", "owner"],
            ordering_map = {
                "owner" : "owner__username",
            },
            default_ordering_key = "extension",
            paginate_by = 20,
            template_name ="phonebook/list.html",
        )),
        name = "extension.list"),
    path("my",
        login_required(FlexibleTemplateView.as_view(
            template_name ="extension/user_list.html",
            template_params = {
                "object_list" :
                lambda req, _ : Extension.objects.filter(owner=req.user).exclude(type="GROUP").select_related("event")
                                                 .order_by("-event__isPermanentAndPublic","-event__end", "event__pk", "extension"),
            },
         )),
        name = "extension.my"),
    path("user/<int:pk>",
         user_is_current_event_admin(FlexibleTemplateView.as_view(
            template_name ="extension/user_list.html",
            template_params = {
                "object_list" :
                lambda req, param : Extension.objects.filter(owner=param.get('pk')).select_related("event")
                                                     .order_by("-event__end", "event__pk", "extension"),
                "list_user" :
                lambda req, param: User.objects.filter(id=param.get('pk')).first()
            },
         )),
        name = "extension.user"),
    path("unused/<int:event>",
         login_required(FlexibleTemplateView.as_view(
             template_name="extension/unused.html",
             template_params={
                 "event": lambda _, param : Event.objects.filter(id=param.get("event")).first()
             }
         )),
         name="extension.unused"),
    path("history/<int:ext>",
         user_is_staff(FlexibleTemplateView.as_view(
             template_name="extension/history.html",
             template_params={
                 "extension": lambda _, param: param.get("ext"),
                 "history_list": lambda _, param: Extension.objects.select_related("owner", "event")
                                                                   .filter(extension=param.get("ext"))
                                                                   .order_by("event__start")
             }
         )),
         name="extension.history"),
]
