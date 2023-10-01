import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from core.models import InventoryItem, InventoryLend, Extension
from core.utils import mac_format, ipei_normalize

from gcontrib.crispy_forms import defaultLayout


MAC_RE = re.compile("^(?:[0-9A-F]{2}:?){6}$", re.IGNORECASE)
IPEI_RE = re.compile("^\\d{5} ?\\d{7} ?[0-9*]$", re.IGNORECASE)


class InventoryItemForm(ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
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
