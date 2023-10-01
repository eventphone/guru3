from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.urls import path, reverse_lazy
from django.utils.translation import gettext_lazy as _

from core.decorators import user_is_current_event_admin
from core.forms.handset import HandsetEditForm
from core.models import DECTHandset

from gcontrib.views.edit import PermCheckCrispyUpdateView, PermCheckDeleteView
from gcontrib.views.meta import FlexibleTemplateView


urlpatterns = [
    path("<int:pk>",
         login_required(PermCheckCrispyUpdateView.as_view(
             model=DECTHandset,
             form_class=HandsetEditForm,
             template_name="handset/update.html",
             form_submit_button_text=_("Save"),
             success_url=reverse_lazy("handset.my"),
         )),
         name="handset.edit"),
    path("my",
         login_required(FlexibleTemplateView.as_view(
             template_name="handset/list.html",
             template_params={
                 "object_list": lambda req, _: DECTHandset.get_user_handset_history(req.user)
             }
         )),
         name="handset.my"),
    path("user/<int:pk>",
         user_is_current_event_admin(FlexibleTemplateView.as_view(
             template_name="handset/list.html",
             template_params={
                 "object_list": lambda _, kwargs: DECTHandset.get_user_handset_history(
                     get_object_or_404(User, pk=kwargs["pk"])),
                 "list_user": lambda _, kwargs: get_object_or_404(User, pk=kwargs["pk"])
             }
         )),
         name="handset.user"),
    path("<int:pk>/delete",
         login_required(PermCheckDeleteView.as_view(
             model=DECTHandset,
             template_name="handset/delete.html",
             with_next=True,
             success_url=lambda self: self.get_next_view_path(),
         )),
         name="handset.delete"),
]
