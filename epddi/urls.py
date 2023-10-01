from django.contrib.auth.decorators import login_required
from django.urls import path, include, reverse_lazy
from django.utils.timezone import now

from core.decorators import user_is_current_event_admin
from core.session import getCurrentEvent
from epddi.decorators import user_is_staff_or_epddi_apikey
from epddi.models import EPDDIClient
from epddi.views import (query_dect_network, reset_online_state, download_crl, EPDDIClientCreateView,
                         EPDDIClientUpdateView, EPDDIClientDeleteView, EPDDIClientInfoView, EPDDIClientManualCertView)
from gcontrib.views.edit import MultiPropertySetterView
from gcontrib.views.meta import FlexibleTemplateView

urlpatterns = [
    path('mikrotik/', include('epddi.urls_mikrotik')),
    path('crl',
         download_crl,
         name="epddi.crl"
         ),
    path("query_dect_network/<name>", # depricated URL
            query_dect_network,
            name="epddi.query_dect_network"),
    path("client/<str:name>/dect_network",
         user_is_staff_or_epddi_apikey(query_dect_network),
         name="epddi.query_dect_network"),
    path("client/<str:hostname>/online",
         user_is_staff_or_epddi_apikey(MultiPropertySetterView.as_view(
             model=EPDDIClient,
             slug_url_kwarg="hostname",
             slug_field="hostname",
             properties={
                 "is_connected": True,
                 "last_connected": lambda _req, _kwargs: now()
             }
         )),
         name="epddi.client.online"),
    path("client/<str:hostname>/offline",
         user_is_staff_or_epddi_apikey(MultiPropertySetterView.as_view(
             model=EPDDIClient,
             slug_url_kwarg="hostname",
             slug_field="hostname",
             properties={
                 "is_connected": False,
                 "last_connected": lambda _req, _kwargs: now()
             }
         )),
         name="epddi.client.offline"),
    path("reset_clients",
         user_is_staff_or_epddi_apikey(reset_online_state),
         name="epddi.reset_clients"),
    path("my",
         login_required(FlexibleTemplateView.as_view(
             template_name="epddi/client_list.html",
             template_params={
                 "object_list":
                     lambda req, _: EPDDIClient.objects.select_related()
                                                       .filter(owner=req.user, event=getCurrentEvent(req))
                                                       .order_by("hostname"),
                 "user_list": lambda _req, _: 1,
             },
         )),
         name="epddi.my"),
    path("<int:pk>/info",
         login_required(EPDDIClientInfoView.as_view(
             template_name="epddi/info.html")),
         name="epddi.info"),
    path("<int:pk>/get_certificate",
         login_required(EPDDIClientManualCertView.as_view(
             template_name="epddi/cert.html")),
         name="epddi.cert"),
    path("list",
         user_is_current_event_admin(FlexibleTemplateView.as_view(
             template_name="epddi/client_list.html",
             template_params={
                 "object_list":
                     lambda req, param: EPDDIClient.objects.select_related().filter(event=getCurrentEvent(req))
                                                           .order_by("hostname"),
             },
         )),
         name="epddi.list"),
    path("new",
         user_is_current_event_admin(EPDDIClientCreateView.as_view(
             template_name="epddi/update.html",
             success_url=reverse_lazy("epddi.list"),
         )),
         name = "epddi.new"),
    path("<int:pk>",
         user_is_current_event_admin(EPDDIClientUpdateView.as_view(
             template_name ="epddi/update.html",
             success_url=reverse_lazy("epddi.list"),
         )),
         name="epddi.edit"),
    path("<int:pk>/delete",
         login_required(EPDDIClientDeleteView.as_view(
             template_name="epddi/delete.html",
             with_next=True,
             success_url=reverse_lazy("epddi.list"),
         )),
         name="epddi.delete"),
]
