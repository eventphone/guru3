from core.inventory import registry, InventoryHookType
from core import models


@registry.register("dect", InventoryHookType.ITEM_HAND_OUT)
def dect_hand_out_hook(item, lending):
    extension = lending.extension
    if not item.mac or extension is None or extension.type != "DECT" or extension.handset is not None:
        return
    try:
        handset = models.DECTHandset.objects.get(ipei=item.mac)
    except models.DECTHandset.DoesNotExist:
        return
    extension.handset = handset
    extension.save(no_transaction_modify=True)


@registry.register("dect", InventoryHookType.ITEM_RETURN)
def dect_return_hook(item, lending):
    extension = lending.extension
    if extension is not None and extension.type == "DECT" and extension.handset is not None:
        extension.handset = None
        extension.save(no_messaging=True)
        extension.unsubscribe_device()


@registry.register("dect", InventoryHookType.ITEM_SAVE)
def dect_item_save_hook(item):
    if item.mac:
        try:
            handset = models.DECTHandset.objects.get(ipei=item.mac)
        except models.DECTHandset.DoesNotExist:
            return
        handset.owner = None
        handset.description = item.description + " [" + item.barcode + "]"
        handset.save()


def check_for_inventory_ipei_suggestion(extension, handset):
    dect_rentals = models.InventoryLend.objects.select_related().filter(backDate__isnull=True,
                                                                        extension=extension,
                                                                        item__itemType__magic="dect",
                                                                        item__mac="")
    if len(dect_rentals) != 1:
        return
    inventory_item = dect_rentals[0].item
    if inventory_item.dectinventorysuggestion_set.count() == 0:
        suggestion = models.DECTInventorySuggestion(item=inventory_item, extension=extension, handset=handset)
        suggestion.save()

