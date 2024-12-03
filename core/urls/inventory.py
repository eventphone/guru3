from django.urls import path, include
from django.views.generic import ListView

from core.decorators import user_is_current_event_admin
from core.models import DECTInventorySuggestion, InventoryItemRecallStatus
from core.session import getCurrentEvent
from core.views.inventory import process_dect_inventory_suggestions, trigger_rental_recall, InventoryPackBox, InventoryBoxEventAssignment

from gcontrib.decorators import user_is_staff
from gcontrib.views.meta import FlexibleTemplateView


urlpatterns = [
    path('type/', include('core.urls.inventory_type')),
    path('class/', include('core.urls.inventory_class')),
    path('item/', include('core.urls.inventory_item')),
    path('dect_suggestions',
         user_is_staff(ListView.as_view(
             queryset=DECTInventorySuggestion.objects.select_related("handset", "item", "extension",
                                                                     "extension__event", "item__itemType").all(),
             template_name="inventory/dect_suggestions.html",
         )),
         name="inventory.dect_suggestions"),
    path('do_dect_suggestions', user_is_staff(process_dect_inventory_suggestions),
         name="inventory.do_dect_suggestions"),
    path('recall_status',
        user_is_current_event_admin(FlexibleTemplateView.as_view(
             template_name="inventory/recall_status.html",
             template_params={
                 "objects_list": lambda req, kwargs: InventoryItemRecallStatus.objects
                                                               .select_related("lending", "lending__item", "lending__extension")
                                                               .filter(lending__event=getCurrentEvent(req),
                                                                       lending__backDate__isnull=True)
                                                               .order_by("call_attempt", "lending__extension__extension",
                                                                         "next_escalation")
             }
         )),
         name="inventory.recall_status"),
    path('do_recall',
         user_is_staff(trigger_rental_recall),
         name="inventory.do_recall"),
    path('box/pack',
         user_is_current_event_admin(InventoryPackBox.as_view()),
         name="inventory.box.pack"),
    path('box/assign_event',
         user_is_staff(InventoryBoxEventAssignment.as_view()),
         name="inventory.box.assign_event"),
]