from django.urls import path, reverse_lazy
from django.views.generic import DeleteView, ListView

from gcontrib.decorators import user_is_staff
from gcontrib.views.edit import CrispyCreateView, CrispyUpdateView
from core.models import InventoryType

urlpatterns = [
    path("new",
         user_is_staff(CrispyCreateView.as_view(
             model=InventoryType,
             fields=["name", "classification", "magic", "auto_recall"],
             form_submit_button_text="Save",
             template_name="inventory/type/update.html",
             success_url=reverse_lazy("inventory.type.list"),
         )),
         name="inventory.type.new"),
    path("<int:pk>",
         user_is_staff(CrispyUpdateView.as_view(
             model=InventoryType,
             fields=["name", "classification", "magic", "auto_recall"],
             form_submit_button_text="Save",
             template_name="inventory/type/update.html",
             success_url=reverse_lazy("inventory.type.list"),
         )),
         name="inventory.type.edit"),
    path("<int:pk>/delete",
         user_is_staff(DeleteView.as_view(
             model=InventoryType,
             template_name="inventory/type/delete.html",
             success_url=reverse_lazy("inventory.type.list"),
         )),
         name="inventory.type.delete"),
    path("list",
         user_is_staff(ListView.as_view(
             model=InventoryType,
             template_name="inventory/type/list.html",
         )),
         name="inventory.type.list"),
]