import datetime

from django.db import transaction
from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView

from core.forms.inventory import InventoryLendForm, InventoryQuickAccessForm
from core.models import InventoryLend, InventoryItem, DECTInventorySuggestion
from core.session import getCurrentEvent
from core.views.event import CurrentEventMixin
from gcontrib.crispy_forms import defaultLayout
from gcontrib.views.edit import CrispyCreateView, CrispyUpdateView
from gcontrib.views.list import SearchView
from gcontrib.views.mixins import FormViewPresaveHookMixin, ObjectPermCheckMixin

# Import hooks for DECT phones
import core.inventory_dect


class InventoryLendingView(FormViewPresaveHookMixin, CurrentEventMixin, CrispyCreateView):
    model = InventoryLend
    form_class = InventoryLendForm
    form_helper = defaultLayout(InventoryLendForm, "Hand out item")

    def get_form(self, form_class=None):
        kwargs = self.get_form_kwargs()
        kwargs["event"] = self.get_event()
        return InventoryLendForm(**kwargs)

    def pre_save_hook(self, object, form):
        # Set event and item
        try:
            item = InventoryItem.objects.get(pk=self.kwargs["pk"])
        except InventoryItem.DoesNotExist:
            raise Http404
        object.item = item
        object.event = self.get_event()
        object.extension = form.cleaned_data["extension"]
        return super(InventoryLendingView, self).pre_save_hook(object, form)


class InventoryEditView(CrispyUpdateView):
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.is_staff:
            for f in form.fields.values():
                f.disabled = True
        return form


class InventoryReturnView(ObjectPermCheckMixin, FormViewPresaveHookMixin, CrispyUpdateView):
    model = InventoryLend
    fields = ["comment"]

    form_submit_button_text = "Return item into stock"

    def pre_save_hook(self, object, form):
        object.backDate = datetime.datetime.now()


class InventoryLendEditView(ObjectPermCheckMixin, CrispyUpdateView):
    model = InventoryLend
    fields = ["lender", "comment"]

    form_submit_button_text = "Save"

    def get_success_url(self):
        return reverse("inventory.item.edit", kwargs={"pk": self.get_object().item.pk})


def inventorySearch(query, request):
    if query == "":
        return InventoryItem.objects.all() #filter(decommissioned=False)
    else:
        return InventoryItem.search_items(query)


def lentInventorySearch(allEvents, query, request):
    event = getCurrentEvent(request)
    event = None if allEvents else event
    return InventoryLend.search_lent_items(query, event)


def lentCSV(request, kwargs):
    event = getCurrentEvent(request)

    keys = ["Type", "Description", "Extension", "Name", "Location", "Serial number", "Barcode", "Lender"]

    lent_items = InventoryLend.search_lent_items("", event).select_related("item", "item__itemType", "extension", "event")
    csv_rows = []
    for lent in lent_items:
        csv_rows.append([
            lent.item.itemType.name,
            lent.item.description,
            lent.extension.extension if lent.extension is not None else "",
            lent.extension.name if lent.extension is not None else "",
            lent.extension.location if lent.extension is not None else "",
            lent.item.serialNumber,
            lent.item.barcode,
            lent.lender,
        ])
    return (keys, csv_rows)


def itemCSV(request, kwargs):
    items = InventoryItem.objects.filter(decommissioned=False).select_related()

    keys = ["Type", "Description", "Barcode", "Creation Date", "Comments", "Serial Number", "MAC"]
    csv_rows = []
    for item in items:
        csv_rows.append([
            item.itemType.name,
            item.description,
            item.barcode,
            item.creationDate.strftime("%d.%m.%Y"),
            item.comments,
            item.serialNumber,
            item.mac,
        ])
    return (keys, csv_rows)


class InventoryLendListView(SearchView):
    allowed_ordering_keys = ["type", "description", "extension", "name", "location", "serialNumber", "barcode",
                             "event", "lender"]
    ordering_map = {
        "type": "item__itemType__name",
        "description": "item__description",
        "extension": "extension__extension",
        "name": "extension__name",
        "location": "extension__location",
        "serialNumber": "item__serialNumber",
        "barcode": "item__barcode",
        "event": "event__name",
    }
    default_ordering_key = "item__description"
    paginate_by = 20


class InventoryListView(SearchView, FormView):
    allowed_ordering_keys = ["type", "description", "serialNumber", "barcode"]
    ordering_map = {"type": "itemType__name"}
    default_ordering_key = "description"
    paginate_by = 20
    form_class = InventoryQuickAccessForm

    def form_invalid(self, form):
        self.object_list = self.get_queryset()
        context = self.get_context_data(form=form)
        return self.render_to_response(context)

    def form_valid(self, form):
        item = form.cleaned_data["barcode"]
        if form.cleaned_data["mode"] == "VIEW":
            return redirect("inventory.item.edit", pk=item.pk)
        elif form.cleaned_data["mode"] == "LR":
            if item.isCurrentlyOnStock():
                return redirect("inventory.item.lend", pk=item.pk)
            else:
                return redirect("inventory.item.return", pk=item.getCurrentLending().pk)
        else:
            raise Http404


@require_http_methods(["POST"])
def process_dect_inventory_suggestions(request):
    take = request.POST.getlist("take")
    remove = request.POST.getlist("del")

    try:
        take = {int(i) for i in take}
        remove = {int(i) for i in remove}
    except ValueError:
        return HttpResponseBadRequest()

    take = take - remove

    with transaction.atomic():
        DECTInventorySuggestion.objects.filter(pk__in=remove).delete()

        take_suggestions = DECTInventorySuggestion.objects.select_related().filter(pk__in=take)
        for suggestion in take_suggestions:
            item = suggestion.item
            item.mac = suggestion.handset.ipei
            item.save()
            suggestion.delete()

    return redirect(reverse("inventory.dect_suggestions"))

def rental_recall_transform(object, request, kwargs):
    return {
        "id": object.pk,
        "event": object.event_id,
        "extension": object.extension.extension if object.extension else None,
        "barcode": object.item.barcode,
        "type": object.item.itemType_id
    }
