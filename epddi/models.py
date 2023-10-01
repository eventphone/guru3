from collections import OrderedDict
import enum
import uuid
import math

import django
from django.contrib.auth.models import User
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.db import models, transaction
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from OpenSSL import crypto
from OpenSSL.crypto import FILETYPE_PEM

from core.models import Event
from core.utils import generateRandomPassword
from epddi.utils import get_new_router_name
from epddi.ca import CertificateAuthority

from netaddr import IPNetwork, IPAddress


class DECTIPNetwork(models.Model):
    network_address = models.GenericIPAddressField(protocol='IPv4', verbose_name=_("Network address"))
    network_mask = models.PositiveSmallIntegerField(validators=[MinValueValidator(16), MaxValueValidator(30)],
                                                    verbose_name=_("Network mask"))

    def __str__(self):
        return f"{self.network_address}/{self.network_mask}"

    @property
    def as_netaddr(self):
        return IPNetwork(f"{self.network_address}/{self.network_mask}")

    @property
    def client_count(self):
        return 2**(32-self.network_mask)-2

    def get_network_address(self):
        return str(self)

    def get_router_ip(self):
        network = IPNetwork(self.get_network_address())
        return str(network.ip+1)

    @classmethod
    def allocate_network(cls, client_count):
        with transaction.atomic():
            # retrieve and lock all networks. According to the documentation of mariadb
            # SELECT … FOR UPDATE will acquire a read/write lock on all selected rows and
            # all transactions that want to read need to wait until this transaction finishes
            # unless they're READ UNCOMMITTED (which we don't have)
            current_networks = cls.objects.select_for_update().all()
            dect_networks = sorted([network.as_netaddr for network in current_networks])

            network_masksize = 32 - math.ceil(math.log2(client_count+2))

            epddi_network = IPNetwork(settings.EPDDI_NETWORK)
            if epddi_network.size <= client_count+2:
                return None  # this would take more than we have, so it can't be served

            next_start_ip = epddi_network.ip
            next_net = IPNetwork(f"{str(next_start_ip)}/{network_masksize}")
            while next_net.broadcast < epddi_network.broadcast:
                # check if this network can be allocated
                if len(dect_networks) == 0 or next_net.broadcast < dect_networks[0].ip:
                    # the next network is far enough away, we can allocate it
                    net = cls(network_address=str(next_net.ip), network_mask=network_masksize)
                    net.save()
                    return net

                # well, didn't work, so let's try after this dect network
                blocking_network = dect_networks.pop(0)
                next_start_ip = blocking_network.broadcast+1
                next_net = IPNetwork(f"{str(next_start_ip)}/{network_masksize}")
                # now check if this is a valid starting point for the desired network size
                if IPAddress(next_net.first) != next_net.ip:
                    next_net = next_net.next()

            return None  # nothing left :(


class EPDDIClientStatus:
    DISABLED = -1
    NEW = 1
    PROVISIONING = 2
    PROVISIONED = 3


class EPDDIDeviceType:
    MANUAL = 0
    MIKROTIK = 1


class EPDDIClient(models.Model):
    STATUS_CHOICES = [
        (EPDDIClientStatus.DISABLED, _("Disabled")),
        (EPDDIClientStatus.NEW, _("New")),
        (EPDDIClientStatus.PROVISIONING, _("Provisioning")),
        (EPDDIClientStatus.PROVISIONED, _("Provisioned")),
    ]
    DEVICE_CHOICES = [
        (EPDDIDeviceType.MANUAL, _("Manual")),
        (EPDDIDeviceType.MIKROTIK, _("Mikrotik")),
    ]
    owner = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    description = models.CharField(max_length=64, verbose_name=_("Name"), blank=True, null=True)
    location = models.CharField(max_length=32, verbose_name=_("Location"), blank=True, null=True)
    hostname = models.CharField(max_length=32, verbose_name=_("Hostname"), unique=True, default=get_new_router_name,
                                validators=[RegexValidator(regex="^[a-zA-Z0-9._-]+$",
                                                           message=_("Valid hostnames are alphanumeric plus _ - and ."))])
    device_type = models.IntegerField(choices=DEVICE_CHOICES, verbose_name=_("Device type"))
    device_state = models.IntegerField(choices=STATUS_CHOICES, default=EPDDIClientStatus.NEW, verbose_name=_("Status"))

    vpn_certificate_pem = models.TextField(verbose_name=_("VPN Certificate"), blank=True)

    dect_network = models.OneToOneField(DECTIPNetwork, on_delete=models.SET_NULL, null=True, verbose_name=_("DECT network"))

    is_connected = models.BooleanField(verbose_name=_("The client is currently connected to our VPN"), default=False)
    last_connected = models.DateTimeField(verbose_name=_("Last connection of this client to our VPN"), null=True,
                                          blank=True)

    def __str__(self):
        if self.description:
            return self.description
        else:
            return "(Unnamed - EPDDI Client {})".format(self.hostname)

    def device_init(self):
        if self.device_type == EPDDIDeviceType.MIKROTIK:
            mikrotik = MikrotikRouter(client=self)
            mikrotik.save()

    def delete(self, *args, **kwargs):
        with transaction.atomic():
            # also delete the dect network and the router (if present)
            if self.dect_network is not None:
                self.dect_network.delete()
            if self.device_type == EPDDIDeviceType.MIKROTIK and self.mikrotikrouter is not None:
                self.mikrotikrouter.delete()

            self.revoke_certificate(RevocationReason.AFFILIATION_CHANGED)
            super().delete(*args, **kwargs)

    def has_read_permission(self, user):
        return user == self.owner or (self.event.isEventAdmin(user))

    def has_write_permission(self, user):
        return self.event.isEventAdmin(user)

    def has_delete_permission(self, user):
        return self.has_write_permission(user)

    def issue_certificate(self, certification_request):
        ca = CertificateAuthority(settings.EPDDI_CA_CERT, settings.EPDDI_CA_KEY)
        cert = ca.issue_router_cert(certification_request, subject_override=OrderedDict([
            ("commonName", self.hostname),
            ("emailAddress", "poc@eventphone.de"),
            ("organizationName", "Eventphone"),
            ("organizationalUnitName", "EPDDI"),
            ("stateOrProvinceName", "NRW"),
            ("countryName", "DE"),
        ]))
        self.vpn_certificate_pem = crypto.dump_certificate(FILETYPE_PEM, cert).decode("ascii")
        self.save()
        return self.vpn_certificate_pem

    def revoke_certificate(self, reason: 'RevocationReason'):
        if self.vpn_certificate_pem == "":
            return
        cert = crypto.load_certificate(FILETYPE_PEM, self.vpn_certificate_pem.encode("ascii"))
        serial = f"{cert.get_serial_number():x}"
        revocation_entry = ClientCertRevocation(cert_serial_hex=serial, revocation_reason=reason.value)
        revocation_entry.save()
        return revocation_entry


class RevocationReason(enum.Enum):
    UNSPECIFIED = 'unspecified'
    KEY_COMPROMISE = 'keyCompromise'
    CA_COMPROMISE = 'CACompromise'
    AFFILIATION_CHANGED = 'affiliationChanged'
    SUPERSEDED = 'superseded'
    CESSATION_OF_OPERATION = 'cessationOfOperation'
    CERTIFICATE_HOLD = 'certificateHold'


class ClientCertRevocation(models.Model):
    cert_serial_hex = models.CharField(max_length=64, verbose_name=_("Serial number of revoked cert in hex"))
    revocation_time = models.DateTimeField(auto_now_add=True, verbose_name=_("Revocation time"))
    revocation_reason = models.CharField(max_length=64, verbose_name=_("Reason for revocation"))


class MikrotikRouter(models.Model):
    client = models.OneToOneField(EPDDIClient, on_delete=models.CASCADE)
    model = models.CharField(max_length=250, verbose_name=_("Model"), blank=True)
    serial = models.CharField(max_length=128, verbose_name=_("Serial number"), blank=True)
    wan_dhcp = models.BooleanField(verbose_name=_("WAN DHCP enabled"), default=True)
    wan_ip = models.GenericIPAddressField(protocol='IPv4', verbose_name=_("WAN IP"), blank=True, null=True)
    wan_netmask = models.IntegerField(validators=[MinValueValidator(16), MaxValueValidator(31)],
                                      default=24, verbose_name=_("Network mask"), blank=True, null=True)
    wan_gw = models.GenericIPAddressField(protocol='IPv4', verbose_name=_("WAN Gateway"), blank=True, null=True)
    wan_dns1 = models.GenericIPAddressField(protocol='IPv4', verbose_name=_("WAN DNS1"), blank=True, null=True)
    wan_dns2 = models.GenericIPAddressField(protocol='IPv4', verbose_name=_("WAN DNS2"), blank=True, null=True)
    token = models.UUIDField(verbose_name=_("Access Token"), default=uuid.uuid4)
    admin_password = models.CharField(max_length=16, verbose_name=_("Admin User Password"), blank=True, editable=False)
    factoryfw = models.CharField(max_length=128, verbose_name=_("Factory Firmware"), blank=True)
    currentfw = models.CharField(max_length=128, verbose_name=_("Current Firmware"), blank=True)
    upgradefw = models.CharField(max_length=128, verbose_name=_("Upgrade Firmware"), blank=True)
    last_config_update = models.DateTimeField(verbose_name=_("Last config update"), default=None, null=True, blank=True)

    def __str__(self):
        if self.client.description:
            return self.client.description
        else:
            return "(Unnamed - Mikrotik {})".format(self.client.hostname)

    def __repr__(self):
        return "<MikrotikRouter serial={} hostname={}>".format(self.serial, self.client.hostname)

    def has_read_permission(self, user):
        return self.client.has_read_permission(user)

    def has_write_permission(self, user):
        return self.client.has_write_poermission(user)

    def has_delete_permission(self, user):
        return self.has_write_permission(user)

    def queue_config(self, config):
        config_update = MikrotikConfigUpdate()
        config_update.mikrotik = self
        config_update.config = config
        config_update.save()

    def provisioning_lag(self):
        return now() - self.last_config_update

    def generate_admin_password(self):
        self.admin_password = generateRandomPassword(settings.EPDDI_MIKROTIK_ADMIN_PW_LENGTH)


class MikrotikConfigUpdate(models.Model):
    mikrotik = models.ForeignKey(MikrotikRouter, on_delete=models.CASCADE)
    created = models.DateTimeField(default=django.utils.timezone.now)
    config = models.TextField(verbose_name="Configuration")
    delivered = models.DateTimeField(verbose_name="Config Delivered", default=None, null=True, blank=True)

    class Meta:
        ordering = ['id']
