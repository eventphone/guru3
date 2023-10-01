from functools import partial

from django.conf import settings
from django.urls import path, re_path

from core.decorators import user_is_staff_or_mgr_apikey

from core.views.callgroup import CallgroupMembershipApiView, CallgroupMemberApiView
from core.views.common import wireMessageView, celery_task_status_view
from core.views.audio import download_audio

from gcontrib.decorators import login_required
from gcontrib.views.api import StaticJsonView
from gcontrib.views.meta import FlexibleTemplateView

urlpatterns = [
    path("help",
         login_required(FlexibleTemplateView.as_view(
             template_name="api/help.html",
             template_params={
                 "guru_url": lambda r, k: settings.INSTALLATION_BASE_URL
            },
         )),
         name="api.help"),
    path("jsonschema/callgroup.json",
         login_required(StaticJsonView.as_view(
             json_data=CallgroupMembershipApiView.json_schema,
             pretty=True,
         )),
         name="callgroup.api.schema"),
    path("jsonschema/callgroup_member.json",
         login_required(StaticJsonView.as_view(
             json_data=CallgroupMemberApiView.json_schema,
             pretty=True,
         )),
         name="callgroup.member.api.schema"),
    path("event/<int:pk>/messages",
         user_is_staff_or_mgr_apikey(wireMessageView),
         name="event.messages"),
    path("event/<int:event>/callgroup/<int:extension>",
         login_required(CallgroupMembershipApiView.as_view()),
         name="callgroup.api"),
    path("event/<int:event>/callgroup/<int:extension>/member/<int:member_extension>",
         login_required(CallgroupMemberApiView.as_view()),
         name="callgroup.member.api"),

    re_path("audio/fetch/ringback/(?P<hash>[a-f0-9]{128})", user_is_staff_or_mgr_apikey(
        partial(download_audio, settings.RINGBACK_OUTPUT_DIR)),
            name="audio.fetch.ringback"),
    re_path("audio/fetch/plain/(?P<hash>[a-f0-9]{128})", user_is_staff_or_mgr_apikey(
        partial(download_audio, settings.PLAIN_AUDIO_OUTPUT_DIR)),
            name="audio.fetch.plain"),

    re_path("task-status/(?P<taskid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})",
            login_required(celery_task_status_view),
            name="celery.taskstatus")
]
