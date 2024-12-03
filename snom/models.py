from django.db import models
from django.utils.translation import gettext_lazy as _
import zoneinfo

from core.models import InventoryItem
from core.utils import generateRandomPassword

from snom.xmlconfig import render_xml_config
import snom.inventory

class DummyProvEvent:
    def __init__(self):
        self.timezone = zoneinfo.ZoneInfo("Europe/Berlin")
        self.name = "No event"

DUMMY_PROVISIONING_EVENT = DummyProvEvent()
DUMMY_PROVISIONING_LENDING = {
    "extension": {
        "announcement_language": "de-de",
        "extension": "0000",
        "name": "PoC unprovisioned",
        "sip_server": "dummy.eventphone.de",
        "sipPassword": "NotProvisionedPassw0rd",
        "event": {
            "name": "No event",
        }
    },
}

class SnomPhone(models.Model):
    mac = models.CharField(max_length=12, verbose_name=_("MAC address"))
    httpServerPassword = models.CharField(max_length=64, verbose_name=_("HTTP server password"), default="eventphone")
    adminPassword = models.CharField(max_length=64, verbose_name=_("Admin password"), default="eventphone")
    userAgent = models.CharField(max_length=512, verbose_name=_("User Agent"), null=True)
    model = models.CharField(max_length=16, verbose_name=_("Snom phone model"), default="")
    no_firmware_update = models.BooleanField(verbose_name=_("Do not push firmware updates to this phone."), blank=True,
                                             default=False)

    def __str__(self):
        return f"{self.mac} - {self.model}"

    @classmethod
    def create_for_mac(cls, mac):
        return cls(mac=mac.upper(), httpServerPassword=generateRandomPassword(10),
                   adminPassword=generateRandomPassword(10))

    @classmethod
    def get_by_mac(cls, mac):
        return cls.objects.get(mac=mac.upper())

    def get_formatted_mac(self):
        return "{}:{}:{}:{}:{}:{}".format(self.mac[0:2], self.mac[2:4], self.mac[4:6],
                                          self.mac[6:8], self.mac[8:10], self.mac[10:12]).upper()

    def get_inventory_item(self):
        items = InventoryItem.objects.filter(mac__iexact=self.get_formatted_mac())
        if items.count() == 0:
            return None
        return items.first()

    @classmethod
    def get_from_inventory_item(cls, item: InventoryItem):
        mac_plain = item.mac.replace(":", "")
        snoms = cls.objects.filter(mac__iexact=mac_plain)
        if len(snoms) != 1:
            return None
        else:
            return snoms[0]

    def get_xml_config(self, prov_url, firmware_url):
        inventory = self.get_inventory_item()
        if inventory is None:
            return None
        current_lending = inventory.getCurrentLending()
        if current_lending:
            event = current_lending.event
        else:
            # We provide a dummy config to show that the phone is not provisioned
            current_lending = DUMMY_PROVISIONING_LENDING
            event = DUMMY_PROVISIONING_EVENT

        return render_xml_config(self, inventory, current_lending, prov_url, firmware_url, event)


class SnomFirmware(models.Model):
    model = models.CharField(max_length=16, verbose_name=_("Phone model name"))
    download_url = models.CharField(max_length=512, verbose_name=_("Firmware download URI"))

    def __str__(self):
        return self.model