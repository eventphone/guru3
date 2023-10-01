from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import path, re_path, reverse_lazy

from core.decorators import  user_is_current_event_admin
from core.forms.audio import AudioFileForm
from core.models import AudioFile
from core.views.audio import CreateRingbackView
from gcontrib.crispy_forms import defaultLayout
from gcontrib.views.edit import PermCheckDeleteView
from gcontrib.views.meta import FlexibleTemplateView
from django.contrib.auth.models import User

urlpatterns = [
    path("new",
         login_required(CreateRingbackView.as_view(
             model=AudioFile,
             form_class=AudioFileForm,
             form_helper=defaultLayout(AudioFileForm, "Save"),
             template_name="audio/new.html",
             success_url=reverse_lazy("audio.my"),
         )),
         name="audio.new"),
    path("my",
         login_required(FlexibleTemplateView.as_view(
             template_name="audio/user_list.html",
             template_params={
                 "object_list":
                     lambda req, _: AudioFile.objects.filter(owner=req.user)
                         .order_by("name"),
             },
         )),
         name="audio.my"),
    path("user/<int:pk>",
         user_is_current_event_admin(FlexibleTemplateView.as_view(
             template_name="audio/user_list.html",
             template_params={
                 "object_list":
                     lambda req, param: AudioFile.objects.filter(owner=param.get('pk')).order_by("name"),
                 "list_user":
                     lambda req, param: get_object_or_404(User, pk=param.get('pk'))
             },
         )),
         name="audio.user"),
    path("<int:pk>/delete",
         login_required(PermCheckDeleteView.as_view(
             model=AudioFile,
             template_name="audio/delete.html",
             with_next=True,
             success_url=lambda self: self.get_next_view_path(),
         )),
         name="audio.delete"),
]