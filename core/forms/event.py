from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, HTML
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from core.models import Event
from gcontrib.crispy_forms import FormGroup, GroupLabel


class EventForm(ModelForm):
    class Meta:
        model = Event
        fields = [
            "name",
            "location",
            "announcement_lang",
            "url",
            "descriptionDE",
            "descriptionEN",
            "start",
            "end",
            "registrationStart",
            "extensionLength",
            "extensionStart",
            "extensionEnd",
            "orgaExtensionStart",
            "orgaExtensionEnd",
            "hasGSM",
            "hasPremium",
            "hasDECT",
            "hasApp",
            "isPermanentAndPublic",
            "regularSipServer",
            "timezone",
            "gsm2G",
            "gsm3G",
            "gsm4G",
            "gsm5G",
        ]

    def clean(self):
        cleaned_data = super(EventForm, self).clean()

        # check extension lengths for consistency
        extLen = cleaned_data.get("extensionLength")
        if extLen is not None:
            # check for consistency
            errMsg = _("Must match the specified extension length")
            code = "extension-size-mismatch"
            for extConfigField in ("extensionStart", "extensionEnd", "orgaExtensionStart",
                                   "orgaExtensionEnd"):
                if len(cleaned_data.get(extConfigField, "")) != extLen:
                    self.add_error(extConfigField, ValidationError(errMsg, code=code))

        # check dates for consistency

        start = cleaned_data.get("start")
        end = cleaned_data.get("end")
        registrationStart = cleaned_data.get("registrationStart")
        datesState = [start is not None, end is not None, registrationStart is not None]
        # either all all none are present
        if not (all(datesState) or not (any(datesState))):
            self.add_error(None,
                           ValidationError(_(
                               "Please provide all or none of the dates to indicate if this is a permanent or finite event"),
                               code="date-inconsistent"))
        permanentAndPublic = cleaned_data.get("isPermanentAndPublic", False)
        if any(datesState) and permanentAndPublic:
            self.add_error("start",
                           ValidationError(_("If you want to make this a permanent event, enter no dates."),
                                           code="not-permanent"))

        # if all are present, check their consistency
        if all(datesState):
            if not (start <= end):
                self.add_error("end",
                               ValidationError(_("End date must be after start date"),
                                               code="date-end-wrong"))

            if not (registrationStart <= start):
                self.add_error("registrationStart",
                               ValidationError(_("The registration must start when the event starts"),
                                               code="date-end-wrong"))

        return cleaned_data


def createEventFormhelper():
    helper = FormHelper()
    helper.layout = Layout(
        FormGroup(
            Field("name"),
            Field("location"),
            Field("timezone"),
            Field("announcement_lang"),
            Field("url"),
            Field("descriptionDE"),
            Field("descriptionEN"),
            GroupLabel(_("General Event Information")),
        ),
        FormGroup(
            Field("start"),
            Field("end"),
            Field("registrationStart"),
            Field("isPermanentAndPublic"),
            GroupLabel(_("Dates")),
        ),
        FormGroup(
            Field("extensionLength"),
            Field("extensionStart"),
            Field("extensionEnd"),
            Field("orgaExtensionStart"),
            Field("orgaExtensionEnd"),
            GroupLabel(_("Extension configuration")),
        ),
        FormGroup(
            Field("regularSipServer"),
            GroupLabel(_("SIP configuration")),
        ),
        FormGroup(
            Field("hasDECT"),
            Field("hasPremium"),
            Field("hasApp"),
            Field("hasGSM"),
            GroupLabel(_("Extension types")),
        ),
        FormGroup(
            Field("gsm2G"),
            Field("gsm3G"),
            Field("gsm4G"),
            Field("gsm5G"),
            GroupLabel(_("Mobile Network Technologies"))
        ),
        HTML("""
{% if form.instance.pk %}
<div class="form-grouper">
<div class="form-grouper-label">Event links</div>
<p><a href="{% url "event.orga_upgrade" orga_key=form.instance.orgaKey %}">Organizer activation link</a></p>
</div>
{% endif %}
                 """),
    )
    helper.add_input(Submit("save", _("Save")))
    return helper


class EventInviteForm(forms.Form):
    from_event = forms.ModelChoiceField(Event.objects.all(), label=_("Invite all extensions from event"))
    deadline = forms.DateField(label=_("Valid until"))
