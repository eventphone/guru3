from django.contrib.auth.decorators import login_required
from django.urls import path

from epddi.views import cert_enroll, deploy_config, MikrotikDownloadInitialView, MikrotikProvisionView, MikrotikProvisionRunscriptView

urlpatterns = [
    path("download_inital/<uuid:token>",
         MikrotikDownloadInitialView.as_view(),
         name="mikrotik.download_inital"),
    path("download_provision_runscript/<uuid:token>",
         MikrotikProvisionRunscriptView.as_view(),
         name="mikrotik.download_provision_runscript"),
    path("provision_userpart/<int:pk>",
         login_required(MikrotikProvisionView.as_view(
             template_name="mikrotik_provision.html"
         )),
         name="mikrotik.provision_userpart"),
    path("deploy_config/<uuid:token>",
         deploy_config,
         name="mikrotik.deploy_config"),
    path("cert_enroll/<uuid:token>",
         cert_enroll,
         name="mikrotik.cert_enroll"),
]
