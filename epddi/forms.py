
from django import forms
from django.core.validators import MinValueValidator
from django.forms import ModelForm, ValidationError
from django.utils.translation import gettext_lazy as _

from dal import autocomplete

from OpenSSL import crypto
from OpenSSL.crypto import FILETYPE_PEM

from epddi.models import EPDDIClient


class EPDDIClientForm(ModelForm):
    class Meta:
        model = EPDDIClient
        fields = [
            "owner",
            "description",
            "location",
            "hostname",
            "device_type",
            "device_state",
        ]
        widgets = {
            "owner": autocomplete.ModelSelect2(url="user.autocomplete"),
        }
    antennae_count = forms.IntegerField(label=_("Number of supported antennae"),
                                        validators=[MinValueValidator(1)],
                                        help_text=_("This will be rounded up to the next suitable subnet size."))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance.pk is not None:
            self.fields["device_type"].disabled = True


class EPDDIManualCertForm(forms.Form):
    csr = forms.CharField(label=_("Paste a PEM-formatted CSR here"), widget=forms.Textarea)

    def clean_csr(self):
        csr_pem_data = self.cleaned_data.get("csr", "")
        try:
            return crypto.load_certificate_request(FILETYPE_PEM, csr_pem_data)
        except crypto.Error as e:
            raise ValidationError(f"CSR cannot be loaded: {e}")
