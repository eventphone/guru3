from django.template.loader import get_template
from django.utils.html import mark_safe

from core.inventory import registry, InventoryHookType
from core.models import InventoryLend, InventoryItem
from grandstream import models


def _prepare_context(grandstream, item, lending=None):
    return {
        "grandstream": grandstream,
        "inventory_item": item,
        "lending": lending,
    }


@registry.register("gxp", InventoryHookType.EXTENSION_DISPLAY)
def extension_display_hook(item: InventoryItem, lending: InventoryLend):
    grandstream = models.GrandstreamPhone.get_from_inventory_item(item)
    if grandstream is None:
        return None
    template = get_template("grandstream/extension.html")
    res = template.render(_prepare_context(grandstream, item, lending))
    return mark_safe(res)


@registry.register("gxp", InventoryHookType.ITEM_DISPLAY)
def inventory_display_hook(item: InventoryItem):
    grandstream = models.GrandstreamPhone.get_from_inventory_item(item)
    if grandstream is None:
        return None
    template = get_template("grandstream/inventory.html")
    res = template.render(_prepare_context(grandstream, item))
    return mark_safe(res)
