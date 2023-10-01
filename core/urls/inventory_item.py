import functools
from django.contrib.auth.decorators import login_required
from django.urls import path, reverse_lazy
from django.views.generic import DeleteView

from gcontrib.decorators import user_is_staff
from gcontrib.views.edit import CrispyCreateView, CrispyUpdateView
from gcontrib.views.task import CSVExportView
from gcontrib.views.list import JsonListView
from gcontrib.crispy_forms import defaultLayout
from core.decorators import user_is_current_event_admin
from core.models import InventoryItem, InventoryLend
from core.forms.inventory import InventoryItemForm
from core.views.inventory import (InventoryLendingView, InventoryReturnView, InventoryLendEditView, InventoryListView,
                                  InventoryLendListView, inventorySearch, lentInventorySearch, InventoryEditView,
                                  lentCSV, itemCSV, rental_recall_transform)

urlpatterns = [
    path("new",
         user_is_staff(CrispyCreateView.as_view(
             model=InventoryItem,
             form_class=InventoryItemForm,
             form_helper=defaultLayout(InventoryItemForm, "Save"),
             template_name="inventory/item/update.html",
             success_url=reverse_lazy("inventory.item.list"),
         )),
         name="inventory.item.new"),
    path("<int:pk>",
         user_is_current_event_admin(InventoryEditView.as_view(
             model=InventoryItem,
             form_class=InventoryItemForm,
             form_helper=defaultLayout(InventoryItemForm, "Save"),
             template_name="inventory/item/update.html",
             success_url=reverse_lazy("inventory.item.list"),
         )),
         name="inventory.item.edit"),
    path("<int:pk>/delete",
         user_is_staff(DeleteView.as_view(
             model=InventoryItem,
             template_name="inventory/item/delete.html",
             success_url=reverse_lazy("inventory.item.list"),
         )),
         name="inventory.item.delete"),
    path("list",
         user_is_current_event_admin(InventoryListView.as_view(
             search_function=inventorySearch,
             template_name="inventory/item/list.html",
         )),
         name="inventory.item.list"),
    path("list+csv",
         user_is_current_event_admin(CSVExportView.as_view(
             csv_function=itemCSV,
             filename="itemlist.csv",
         )),
         name="inventory.item.list.csv"),
    path("lent",
         user_is_current_event_admin(InventoryLendListView.as_view(
             search_function=functools.partial(lentInventorySearch, False),
             template_name="inventory/item/lentlist.html",
         )),
         name="inventory.item.lent"),
    path("lent+csv",
         user_is_current_event_admin(CSVExportView.as_view(
             csv_function=lentCSV,
             filename="lentlist.csv",
         )),
         name="inventory.item.lent.csv"),
    path("lent+all",
         user_is_staff(InventoryLendListView.as_view(
             search_function=functools.partial(lentInventorySearch, True),
             template_name="inventory/item/lentlist+all.html",
         )),
         name="inventory.item.lent.all"),
    path("lend/<int:pk>",
         user_is_current_event_admin(InventoryLendingView.as_view(
             template_name="inventory/item/lend.html",
             success_url=reverse_lazy("inventory.item.list"),
         )),
         name="inventory.item.lend"),
    path("return/<int:pk>",
         login_required(InventoryReturnView.as_view(
             template_name="inventory/item/return.html",
             success_url=reverse_lazy("inventory.item.list")
         )),
         name="inventory.item.return"),
    path("lend/edit/<int:pk>",
         login_required(InventoryLendEditView.as_view(
             template_name="inventory/item/lend_edit.html",
         )),
         name="inventory.item.lend_edit"),
    path("api/recall/<int:event>",
         user_is_current_event_admin(JsonListView.as_view(
            queryset=lambda _, kwargs : InventoryLend.objects.select_related("item", "item__itemType") \
                                                     .filter(event=kwargs["event"], backDate__isnull=True,
                                                             item__itemType__auto_recall=True),
             object_transform = rental_recall_transform,
         )),
         name="inventory.item.recall"),

]
