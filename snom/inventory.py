from django.template.loader import get_template
from django.utils.html import mark_safe

from core.inventory import registry, InventoryHookType
from core.models import InventoryLend, InventoryItem
from snom import models


def _prepare_context(snom, item, lending=None):
    return {
        "snom": snom,
        "inventory_item": item,
        "lending": lending,
    }


@registry.register("snom", InventoryHookType.EXTENSION_DISPLAY)
def extension_display_hook(item: InventoryItem, lending: InventoryLend):
    snom = models.SnomPhone.get_from_inventory_item(item)
    if snom is None:
        return None
    template = get_template("snom/extension.html")
    res = template.render(_prepare_context(snom, item, lending))
    return mark_safe(res)


@registry.register("snom", InventoryHookType.ITEM_DISPLAY)
def inventory_display_hook(item: InventoryItem):
    snom = models.SnomPhone.get_from_inventory_item(item)
    if snom is None:
        return None
    template = get_template("snom/inventory.html")
    res = template.render(_prepare_context(snom, item))
    return mark_safe(res)
