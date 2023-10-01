from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import InventoryItem
from core.utils import generateRandomPassword

from snom.xmlconfig import render_xml_config
import snom.inventory


class SnomPhone(models.Model):
    mac = models.CharField(max_length=12, verbose_name=_("MAC address"))
    httpServerPassword = models.CharField(max_length=64, verbose_name=_("HTTP server password"), default="eventphone")
    adminPassword = models.CharField(max_length=64, verbose_name=_("Admin password"), default="eventphone")
    userAgent = models.CharField(max_length=512, verbose_name=_("User Agent"), null=True)
    model = models.CharField(max_length=16, verbose_name=_("Snom phone model"), default="")

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

    def get_xml_config(self, prov_url):
        inventory = self.get_inventory_item()
        if inventory is None:
            return None
        current_lending = inventory.getCurrentLending()
        return render_xml_config(self, inventory, current_lending, prov_url, current_lending.event)
