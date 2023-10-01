from django.urls import reverse
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.base import ContextMixin
from django.views.generic.edit import FormView
from django.shortcuts import get_object_or_404

from OpenSSL import crypto
from OpenSSL.crypto import FILETYPE_PEM

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import ValidationError
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseBadRequest, FileResponse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from core.views.event import CurrentEventMixin
from gcontrib.views.edit import CrispyCreateView, CrispyUpdateView, PermCheckDeleteView
from gcontrib.views.mixins import FormHelperMixin

from epddi.decorators import json_request
from epddi.forms import EPDDIClientForm, EPDDIManualCertForm
from epddi.models import EPDDIClient, EPDDIClientStatus, MikrotikRouter, MikrotikConfigUpdate, DECTIPNetwork
from epddi.tasks import EPDDI_CRL_FILE, update_cached_epddi_crl

from gcontrib.views.mixins import ObjectPermCheckMixin


@require_GET
def query_dect_network(_request, name):
    try:
        client = EPDDIClient.objects.exclude(device_state=EPDDIClientStatus.DISABLED).get(hostname=name)
        return HttpResponse(client.dect_network.get_network_address())
    except EPDDIClient.DoesNotExist:
        return HttpResponseNotFound()


@require_GET
def download_crl(_request):
    if not EPDDI_CRL_FILE.is_file():
        return HttpResponseNotFound()
    return FileResponse(EPDDI_CRL_FILE.open("rb"))


@csrf_exempt
@require_POST
def reset_online_state(_request):
    with transaction.atomic():
        EPDDIClient.objects.filter(is_connected=True).update(last_connected=now())
        EPDDIClient.objects.update(is_connected=False)
    return HttpResponse()


def set_mikrotik_info(object, json_data):
    if 'serial' in json_data:
        object.serial = json_data['serial']
    if 'model' in json_data:
        object.model = json_data['model']
    if 'currentfw' in json_data:
        object.currentfw = json_data['currentfw']
    if 'factoryfw' in json_data:
        object.factoryfw = json_data['factoryfw']
    if 'upgradefw' in json_data:
        object.upgradefw = json_data['upgradefw']

@csrf_exempt
@require_POST
@json_request()
def deploy_config(request, token, json_data):
    try:
        mikrotik = MikrotikRouter.objects.select_related("client") \
                                 .get(token=token,
                                      client__device_state__in=
                                          [EPDDIClientStatus.PROVISIONING, EPDDIClientStatus.PROVISIONED])
    except MikrotikRouter.DoesNotExist:
        return HttpResponseNotFound()

    set_mikrotik_info(mikrotik, json_data)
    mikrotik.last_config_update = now()
    mikrotik.save()
    config = MikrotikConfigUpdate.objects.filter(mikrotik=mikrotik, delivered=None).order_by('created').first()
    if config is not None:
        config.delivered = now()
        config.save()
        return HttpResponse(config.config)
    return HttpResponse(status=204)


@csrf_exempt
@require_POST
def cert_enroll(request, token):
    if request.body is None or request.body == b"":
        return HttpResponseBadRequest()
    body_data = bytes.decode(request.body, request.encoding or settings.DEFAULT_CHARSET).replace(" ", "")\
        .replace("BEGINCERTIFICATEREQUEST", "BEGIN CERTIFICATE REQUEST")\
        .replace("ENDCERTIFICATEREQUEST", "END CERTIFICATE REQUEST")
    try:
        csr = crypto.load_certificate_request(FILETYPE_PEM, body_data)
    except crypto.Error as e:
        return HttpResponseBadRequest(f"Cannot read CSR: {e}".encode("utf8"))
    try:
        mikrotik = MikrotikRouter.objects.select_related("client")\
                                         .get(token=token, client__device_state=EPDDIClientStatus.PROVISIONING)
    except MikrotikRouter.DoesNotExist:
        return HttpResponseNotFound()

    client = mikrotik.client
    cert_pem = client.issue_certificate(csr)
    client.device_state = EPDDIClientStatus.PROVISIONED
    client.save()

    return HttpResponse(cert_pem)


class EpddiSettingsContextMixin(ContextMixin):
    def get_context_data(self, **kwargs):
        context = {
            'EPDDI_NETWORK' : settings.EPDDI_NETWORK,
            'EPDDI_YATE_RTP_ADDRESS' : settings.EPDDI_YATE_RTP_ADDRESS,
            'EPDDI_ANTENNAE_RTP_PORT_RANGE_START' : settings.EPDDI_ANTENNAE_RTP_PORT_RANGE_START,
            'EPDDI_ANTENNAE_RTP_PORT_RANGE_END' : settings.EPDDI_ANTENNAE_RTP_PORT_RANGE_END,
            'EPDDI_YATE_RTP_PORT_RANGE_START' : settings.EPDDI_YATE_RTP_PORT_RANGE_START,
            'EPDDI_YATE_RTP_PORT_RANGE_END' : settings.EPDDI_YATE_RTP_PORT_RANGE_END,
            'EPDDI_OMM_ADDRESS' : settings.EPDDI_OMM_ADDRESS,
            'EPDDI_VPN_CONCENTRATOR_ADDRESS' : settings.EPDDI_VPN_CONCENTRATOR_ADDRESS,
            'EPDDI_VPN_CONCENTRATOR_SERVER_CA_CERT_URL' : settings.EPDDI_VPN_CONCENTRATOR_SERVER_CA_CERT_URL,
            'EPDDI_VPN_CONCENTRATOR_SERVER_HOSTNAME' : settings.EPDDI_VPN_CONCENTRATOR_SERVER_HOSTNAME
        }
        return super().get_context_data(**context)


class MikrotikProvisionView(ObjectPermCheckMixin, EpddiSettingsContextMixin, DetailView):
    model = MikrotikRouter


class EPDDIClientInfoView(ObjectPermCheckMixin, EpddiSettingsContextMixin, DetailView):
    model = EPDDIClient
    context_object_name = "client"


class MikrotikScriptView(EpddiSettingsContextMixin, DetailView):
    content_type = "application/txt"
    device_state = None

    def get_object(self):
        token = self.kwargs.get("token")
        if token is None:
            raise AttributeError("MikrotikScriptView must be called with an mikrotik object token in the URLconf.")

        if self.device_state is None:
            return get_object_or_404(MikrotikRouter, token=token)
        else:
            return get_object_or_404(MikrotikRouter.objects.select_related("client", "client__dect_network"), \
                                     token=token, client__device_state=self.device_state)


class MikrotikProvisionRunscriptView(MikrotikScriptView):
    template_name = "mikrotik/provision_runscript.rsc"
    device_state = EPDDIClientStatus.NEW

    def get_object(self):
        mikrotik = super().get_object()
        mikrotik.client.device_state = EPDDIClientStatus.PROVISIONING
        mikrotik.client.save()
        return mikrotik


class MikrotikDownloadInitialView(MikrotikScriptView):
    template_name = "mikrotik/initial.rsc"
    device_state = EPDDIClientStatus.PROVISIONING

    def get_object(self):
        mikrotik = super().get_object()
        mikrotik.generate_admin_password()
        mikrotik.save()
        return mikrotik


class EPDDIClientViewMixin:
    model = EPDDIClient
    form_class = EPDDIClientForm

    def pre_save_hook(self, object, form):
        pass

    @transaction.atomic
    def form_valid(self, form):
        object = form.save(commit=False)
        antennae_count = form.cleaned_data["antennae_count"]

        sid = transaction.savepoint()
        if object.dect_network is None:
            object.dect_network = DECTIPNetwork.allocate_network(antennae_count+1)
        elif object.dect_network.client_count != antennae_count+1:
            object.dect_network.delete()
            object.dect_network = DECTIPNetwork.allocate_network(antennae_count+1)

        if object.dect_network is None:
            # allocation of a new DECT network failed, so we must be out of networks…
            transaction.savepoint_rollback(sid)
            form.add_error("antennae_count", ValidationError(_("A sufficiently large network cannot be allocated")))
            return self.form_invalid(form)
        transaction.savepoint_commit(sid)

        self.pre_save_hook(object, form)
        return super().form_valid(form)


class EPDDIClientUpdateView(EPDDIClientViewMixin, ObjectPermCheckMixin, CrispyUpdateView):
    form_submit_button_text = "Save"

    def get_queryset(self):
        return super().get_queryset().select_related()

    def get_form_kwargs(self, form_class=None):
        form_kwargs = super().get_form_kwargs()
        if "initial" not in form_kwargs:
            form_kwargs["initial"] = {}
        dect_network = self.get_object().dect_network
        if dect_network is not None:
            form_kwargs["initial"]["antennae_count"] = dect_network.client_count-1
        return form_kwargs

    def get_event(self):
        return self.get_object().event


class EPDDIClientCreateView(EPDDIClientViewMixin, CurrentEventMixin, CrispyCreateView):
    form_submit_button_text = "Create"

    def pre_save_hook(self, object, form):
        object.event = self.get_event()
        super().pre_save_hook(object, form)
        object.save()
        object.device_init()


class EPDDIClientDeleteView(PermCheckDeleteView):
    model = EPDDIClient

    def post(self, request, *args, **kwargs):
        """
        Hook into delete and once the deletion is complete and confirmed, trigger regeneration of
        EPDDI crl
        """
        result = super().delete(request, *args, **kwargs)
        update_cached_epddi_crl.delay()
        return result


class EPDDIClientManualCertView(FormHelperMixin, SingleObjectMixin, FormView):
    form_class = EPDDIManualCertForm
    model = EPDDIClient
    form_submit_button_text = "Issue Certificate"

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.has_read_permission(self.request.user) and not request.user.is_staff:
            raise PermissionDenied
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # end-users do not have write permission on EPDDI clients but should be able to issue a cert
        if not self.object.has_read_permission(self.request.user) and not request.user.is_staff:
            raise PermissionDenied
        return super().post(request, *args, **kwargs)

    def get_object(self):
        object = super().get_object()
        if object.device_type != 0:
            raise PermissionDenied()
        if object.device_state == EPDDIClientStatus.PROVISIONED:
            raise PermissionDenied()
        return object

    def form_valid(self, form):
        client = self.get_object()
        client.issue_certificate(form.cleaned_data["csr"])
        client.device_state = EPDDIClientStatus.PROVISIONED
        client.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("epddi.info", kwargs={"pk": self.kwargs["pk"]})
