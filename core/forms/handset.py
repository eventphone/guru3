from django.forms import ModelForm

from core.models import DECTHandset


class HandsetEditForm(ModelForm):
    class Meta:
        model = DECTHandset
        fields = [
            "description",
            "vendor",
            "model_designation",
            "ipei",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ipei"].disabled = True
