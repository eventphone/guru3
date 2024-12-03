import datetime
from functools import cached_property

from django.db import transaction
from django.db.models import Subquery, OuterRef, Sum, F, Value, Count
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.views.generic import FormView

from core.forms.inventory import InventoryLendForm, InventoryQuickAccessForm, InventoryPackBoxFom, \
    InventoryBoxEventAssignmentForm, InventoryReturnForm
from core.models import InventoryLend, InventoryItem, DECTInventorySuggestion, InventoryType
from core.session import getCurrentEvent
from core.views.event import CurrentEventMixin
from core.tasks import recall_rental_devices
from core.utils import task_url
from gcontrib.crispy_forms import defaultLayout
from gcontrib.views.edit import CrispyCreateView, CrispyUpdateView
from gcontrib.views.list import SearchView
from gcontrib.views.mixins import FormViewPresaveHookMixin, ObjectPermCheckMixin
from gcontrib.views.redirect import redirect_with_params

# Import hooks for DECT phones
import core.inventory_dect

@method_decorator(transaction.atomic, name="dispatch")
class InventoryLendingView(FormViewPresaveHookMixin, CurrentEventMixin, CrispyCreateView):
    model = InventoryLend
    form_class = InventoryLendForm
    form_helper = defaultLayout(InventoryLendForm, "Hand out item")

    @cached_property
    def inventory_item(self):
        # lock inventory item to prevent concurrent lending creation
        res = InventoryItem.objects.select_for_update().prefetch_related("inventorylend_set").filter(pk=self.kwargs["pk"])
        if len(res) != 1:
            raise Http404
        return res[0]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["event"] = self.get_event()
        kwargs["inventory_item"] = self.inventory_item
        return kwargs

    def pre_save_hook(self, object, form):
        # Set event and item
        object.item = self.inventory_item
        object.event = self.get_event()
        object.extension = form.cleaned_data["extension"]
        self.inventory_item.containedIn = None
        self.inventory_item.save()
        return super(InventoryLendingView, self).pre_save_hook(object, form)


class InventoryEditView(CrispyUpdateView):
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.is_staff:
            for f in form.fields.values():
                f.disabled = True
        return form


@method_decorator(transaction.atomic, name="post")
class InventoryReturnView(ObjectPermCheckMixin, FormViewPresaveHookMixin, CrispyUpdateView):
    model = InventoryLend
    form_class = InventoryReturnForm

    def pre_save_hook(self, object, form):
        box_barcode = form.cleaned_data["box_barcode"]
        try:
            box = InventoryItem.objects.get(barcode=box_barcode)
            object.item.containedIn = box
            object.item.save()
        except InventoryItem.DoesNotExist:
            pass
        object.backDate = datetime.datetime.now()


class InventoryLendEditView(ObjectPermCheckMixin, CrispyUpdateView):
    model = InventoryLend
    fields = ["lender", "comment"]

    form_submit_button_text = "Save"

    def get_success_url(self):
        return reverse("inventory.item.edit", kwargs={"pk": self.get_object().item.pk})


def inventorySearch(query, request, event=None):
    if query == "":
        qs = InventoryItem.objects.all()
    else:
        qs = InventoryItem.search_items(query)
    if event is not None:
        qs = qs.filter(event=event)
    if "decommissioned" in request.GET:
        return qs
    else:
        return qs.filter(decommissioned=False)

def currentEventInventorySearch(query, request):
    event = getCurrentEvent(request)
    return inventorySearch(query, request, event)

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if "decommissioned" in self.request.GET:
            context["search_params"]["decommissioned"] = "1"
        return context

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


@require_POST
def trigger_rental_recall(request):
    event = getCurrentEvent(request)
    task = recall_rental_devices.delay(event.pk)
    return JsonResponse({
        "task_url": task_url(task),
        "next_view": reverse("inventory.recall_status"),
    })


class InventoryPackBox(FormView):
    form_class = InventoryPackBoxFom
    template_name = "inventory/box/pack.html"

    def form_valid(self, form):
        with transaction.atomic():
            box = form.cleaned_data["box_barcode"]
            new_items = form.cleaned_data["content_barcodes"]
            if form.cleaned_data["repack_box"]:
                InventoryItem.objects.filter(containedIn=box).update(containedIn=None)
            for item in new_items:
                item.containedIn = box
                if form.cleaned_data["return_on_pack"]:
                    lending = item.getCurrentLending()
                    if lending:
                        lending.backDate = datetime.datetime.now()
                        lending.save()
                item.save()
        return redirect_with_params("inventory.box.pack", params={"success": "1"})


@require_GET
def inventory_item_info(request):
    barcodes = request.GET.get("q", "").strip().split("\n")
    barcodes = [barcode for barcode in barcodes if barcode.strip() != ""]
    items = InventoryItem.objects.filter(barcode__in=barcodes)
    items_by_barcodes = {item.barcode: item.json_info() for item in items}
    return JsonResponse({"results": [items_by_barcodes.get(barcode, None) for barcode in barcodes]})


@require_GET
def box_content_info(request):
    box = get_object_or_404(InventoryItem, barcode=request.GET.get("q"))
    content_items = InventoryItem.objects.filter(containedIn=box)
    return JsonResponse({"results" : [item.json_info() for item in content_items]})


class InventoryBoxEventAssignment(FormView):
    form_class = InventoryBoxEventAssignmentForm
    template_name = "inventory/box/event_assignment.html"

    def form_valid(self, form):
        with transaction.atomic():
            boxes = form.cleaned_data["barcodes"]
            event = form.cleaned_data["event"]
            for box in boxes:
                box.recursively_set_event(event)
        return redirect("inventory.item.list")


def event_available_item_types(request, _kwargs):
    event = getCurrentEvent(request)
    return InventoryItem.objects.filter(event=event).annotate(
        active_lending=Coalesce(Subquery(InventoryLend.objects.filter(item=OuterRef("pk"), backDate__isnull=True)
                               .annotate(count=Count("id")).values("count")), 0),
        item=Value(1),
    ).values("itemType__name").annotate(
        event_total=Sum("item"),
        event_lent=Sum("active_lending")
    ).annotate(
        event_available=F("event_total") - F("event_lent")
    )