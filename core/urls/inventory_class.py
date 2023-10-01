from django.urls import path, reverse_lazy
from django.views.generic import DeleteView, ListView

from gcontrib.decorators import user_is_staff
from gcontrib.views.edit import CrispyCreateView, CrispyUpdateView
from core.models import RentalDeviceClassification

urlpatterns = [
    path("new",
         user_is_staff(CrispyCreateView.as_view(
             model=RentalDeviceClassification,
             fields=["name"],
             form_submit_button_text="Save",
             template_name="inventory/class/update.html",
             success_url=reverse_lazy("inventory.class.list"),
         )),
         name="inventory.class.new"),
    path("<int:pk>",
         user_is_staff(CrispyUpdateView.as_view(
             model=RentalDeviceClassification,
             fields=["name"],
             form_submit_button_text="Save",
             template_name="inventory/class/update.html",
             success_url=reverse_lazy("inventory.type.list"),
         )),
         name="inventory.class.edit"),
    path("<int:pk>/delete",
         user_is_staff(DeleteView.as_view(
             model=RentalDeviceClassification,
             template_name="inventory/type/delete.html",
             success_url=reverse_lazy("inventory.class.list"),
         )),
         name="inventory.class.delete"),
    path("list",
         user_is_staff(ListView.as_view(
             model=RentalDeviceClassification,
             template_name="inventory/class/list.html",
         )),
         name="inventory.class.list"),
]