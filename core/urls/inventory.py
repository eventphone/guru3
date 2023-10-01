from django.urls import path, include
from django.views.generic import ListView

from core.models import DECTInventorySuggestion
from core.views.inventory import process_dect_inventory_suggestions

from gcontrib.decorators import user_is_staff


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
]