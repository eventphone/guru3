import datetime
import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Row, Column, Div, Layout, HTML, Submit

from core.models import InventoryItem, InventoryLend, Extension, Event
from core.utils import mac_format, ipei_normalize

from gcontrib.crispy_forms import defaultLayout


MAC_RE = re.compile("^(?:[0-9A-F]{2}(:|-)?){6}$", re.IGNORECASE)
IPEI_RE = re.compile("^\\d{5} ?\\d{7} ?[0-9*]$", re.IGNORECASE)


class InventoryItemForm(ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            "containedIn",
            "event",
            "itemType",
            "description",
            "serialNumber",
            "mac",
            "barcode",
            "comments",
            "decommissioned",
        ]

    def clean_mac(self):
        mac = self.cleaned_data.get("mac", "")
        if MAC_RE.match(mac):
            return mac_format(mac)
        elif IPEI_RE.match(mac):
            return ipei_normalize(mac)
        elif mac == "":
            return ""
        else:
            self.add_error("mac",
                           ValidationError(_("The mac needs to be either a valid Ethernet mac or a valid IPEI"),
                           code="mac-invalid"))
            return mac


class InventoryLendForm(ModelForm):
    class Meta:
        model = InventoryLend

        fields = [
            "lender",
            "comment",
        ]
    extension = forms.CharField(label=_("Extension"), required=False)

    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event")
        self.inventory_item = kwargs.pop("inventory_item")
        super().__init__(*args, **kwargs)

    def clean_extension(self):
        extension = self.cleaned_data.get("extension")
        if extension is None or extension == "":
            return None

        try:
            return Extension.objects.get(event=self.event, extension=extension)
        except Extension.DoesNotExist:
            self.add_error("extension",
                           ValidationError(_("Extension unknown in current event."),
                                           code="extension-unknown"))

    def clean(self):
        _ = super().clean()
        if not self.inventory_item.isCurrentlyOnStock():
            self.add_error(None, "This item is already lent out. It needs to be returned first.")


class InventoryReturnForm(ModelForm):
    class Meta:
        model = InventoryLend

        fields = [
            "comment"
        ]

    box_barcode = forms.CharField(label=_("Box Barcode"), required=False,
                                  help_text=_("Scan a box this item is being put into. Leave empty to not pack into a box."))

    @property
    def form_helper(self):
        helper = FormHelper()
        helper.layout = Layout(
            Row(Column(Field("box_barcode"), css_class="col-md-6"),
                Column(
                    Div(
                        HTML("<div style=\"margin-bottom: 0.5rem\"><br /></div>"),
                        Div(HTML("(Scan box)"), css_id="box_description"),
                        css_class="col-md-6")
                ),
                ),
            Field("comment"),
        )
        helper.add_input(Submit("submit", "Return item into stock"))
        return helper


QUICK_ACCESS_MODE_CHOICES = (
    ("VIEW", "View item"),
    ("LR", "Lend/Return item"),
)


class InventoryQuickAccessForm(forms.Form):
    mode = forms.ChoiceField(label=_("Quick access mode"), choices=QUICK_ACCESS_MODE_CHOICES)
    barcode = forms.CharField(label=_("Barcode"), widget=forms.TextInput(attrs={"autofocus": "autofocus"}))

    def get_form_helper(self):
        helper = defaultLayout(self, "Go")
        helper.form_class = "form-inline"
        helper.label_class = 'col'
        helper.field_class = 'col'
        return helper

    def clean_barcode(self):
        barcode = self.cleaned_data.get("barcode", "")
        try:
            item = InventoryItem.find_item(barcode)
            return item
        except InventoryItem.DoesNotExist:
            self.add_error("barcode",
                           ValidationError("Unknown item", code="unkown-item"))


class InventoryPackBoxFom(forms.Form):
    box_barcode = forms.CharField(label=_("Box barcode"), widget=forms.TextInput(attrs={"autofocus": "autofocus"}))
    content_barcodes = forms.CharField(label=_("Content barcodes"), widget=forms.Textarea(attrs={"rows": "10"}))
    return_on_pack = forms.BooleanField(label=_("Return all items if currently lent out"), required=False, initial=True)
    repack_box = forms.BooleanField(label=_("Completely repack this box"), required=False, initial=False,
                                    help_text=_("Check this box to repack the box by completely defining its content instead of adding items."))

    @property
    def form_helper(self):
        helper = FormHelper()
        helper.layout = Layout(
            Row(Column(Field("box_barcode"), css_class="col-md-6"),
                Column(
                    Div(
                        HTML("<div style=\"margin-bottom: 0.5rem\"><br /></div>"),
                        Div(HTML("(Scan box)"), css_id="box_description"),
                        css_class="col-md-6")
                ),
            ),
            Row(Column(Field("content_barcodes"), css_class="col-md-6"),
                Column(
                    Div(
                        HTML("<div style=\"margin-bottom: 0.5rem\"><span id=\"content_count\">0</span> items<br /></div>"),
                        Div(HTML("(Scan content)"),  css_id="box_content_description"),
                    css_class="col-md-6")
                ),
            ),
            Field("return_on_pack"),
            Field("repack_box"),
        )
        helper.add_input(Submit("pack", "Pack box"))
        return helper

    def clean_content_barcodes(self):
        barcodes = self.cleaned_data["content_barcodes"]
        unique_barcodes = set([barcode.strip() for barcode in barcodes.split("\n")])
        items = InventoryItem.objects.filter(barcode__in=unique_barcodes)
        if len(unique_barcodes) != len(items):
            raise ValidationError("The item list contains invalid barcodes? See information on the right.")
        return items

    def clean_box_barcode(self):
        try:
            box = InventoryItem.objects.get(barcode=self.cleaned_data["box_barcode"])
        except InventoryItem.DoesNotExist:
            raise ValidationError("Invalid barcode.")
        if not box.itemType.isContainer:
            raise ValidationError("This item is no container? Wrong scan?")
        return box


class InventoryBoxEventAssignmentForm(forms.Form):
    event = forms.ModelChoiceField(Event.objects.all(), label=_("To which event should this box be assigned?"),
                                   empty_label="(Storage)", required=False,
                                   help_text="Select (Storage) to indicate that the items are now in storage and not assigned to the event anymore")
    barcodes = forms.CharField(label=_("Content barcodes"), widget=forms.Textarea(attrs={"rows": "10"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["event"].queryset = Event.objects.filter(end__gte=datetime.date.today())


    @property
    def form_helper(self):
        helper = FormHelper()
        helper.layout = Layout(
            Field("event"),
            Row(Column(Field("barcodes"), css_class="col-md-6"),
                Column(
                    Div(
                        HTML("<div style=\"margin-bottom: 0.5rem\"><br /></div>"),
                        Div(HTML("(Scan content)"), css_id="barcodes_description"),
                        css_class="col-md-6")
                ),
                ),
        )
        helper.add_input(Submit("assign", "Assign boxes to event"))
        return helper

    def clean_barcodes(self):
        barcodes = self.cleaned_data["barcodes"]
        unique_barcodes = set([barcode.strip() for barcode in barcodes.split("\n")])
        items = InventoryItem.objects.filter(barcode__in=unique_barcodes)
        if len(unique_barcodes) != len(items):
            raise ValidationError("The item list contains invalid barcodes? See information on the right.")
        return items
