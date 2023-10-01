from django.db import models
from django.utils.translation import gettext_lazy as _

from core.models import InventoryItem
from core.utils import generateRandomPassword
import grandstream.inventory


class GrandstreamPhone(models.Model):
    mac = models.CharField(max_length=12, verbose_name=_("MAC address"))
    preSharedPassword = models.CharField(max_length=64, verbose_name=_("Pre shared password"))
    userPassword = models.CharField(max_length=64, verbose_name=_("User password"), default="eventphone")
    adminPassword = models.CharField(max_length=64, verbose_name=_("Admin password"), default="eventphone")
    userAgent = models.CharField(max_length=512, verbose_name=_("User Agent"), null=True)

    @classmethod
    def createForMac(cls, mac):
        return cls(mac=mac, preSharedPassword=generateRandomPassword(16),
                   userPassword=generateRandomPassword(10), adminPassword=generateRandomPassword(10))

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
        grandstreams = cls.objects.filter(mac__iexact=mac_plain)
        if len(grandstreams) != 1:
            return None
        else:
            return grandstreams[0]
