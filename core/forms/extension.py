import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Submit, HTML
from crispy_forms.bootstrap import AppendedText
from dal import autocomplete
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django import forms
from django.forms import ModelForm, CharField, Form, HiddenInput, TextInput, ModelChoiceField
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

from core import utils
from core.models import (Extension, AudioFile, DECTHandset, PERM_ADMIN, PERM_ORGA, InventoryItem,
                         ExtensionNotAllowedException, EXTENSION_TYPES)
from gcontrib.crispy_forms import FormGroup, GroupLabel

QUICK_CREATE_FIELDS = ("extension", "name", "inPhonebook", "type", "requestedRentalDevice")

# These fields must exist and be populated by the form because the model wants non-NULL defaults
# or the code otherwise expects them to be present
MANDATORY_FIELDS = ("announcement_lang", "type", "displayModus", "handset")


class ExtensionField(forms.Field):
    def __init__(self, *args, **kwargs):
        kwargs.pop("limit_choices_to")
        kwargs.pop("queryset")
        kwargs.pop("to_field_name")
        kwargs.pop("blank")
        self._event = None
        super().__init__(*args, **kwargs)
        self.validators.append(self.check_is_extension)

    @staticmethod
    def check_is_extension(value):
        if not isinstance(value, Extension):
            raise ValidationError(_("Cannot find extension"), code="extension-not-found")

    @property
    def event(self):
        return self._event

    @event.setter
    def event(self, val):
        self._event = val

    def to_python(self, value):
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValidationError(_("Extension must be a string"))
        if value == "":
            return None
        if self._event is None:
            raise ImproperlyConfigured("The ExtensionField must have an event set before it can be used")
        extension = Extension.objects.filter(event=self._event, extension=value)
        if len(extension) != 1:
            return value
        return extension[0]

    def prepare_value(self, value):
        if isinstance(value, int):
            try:
                ext = Extension.objects.get(pk=value)
                return ext.extension
            except Extension.DoesNotExist:
                return None
        elif isinstance(value, str):
            return value


def generateExtensionForm(permissions, quick_create=False, field_filter=None, read_only=False, form_types=None):
    """Generate a form object to handle extensions

    If the given type is none, a form that will contain all possible fields for all

    """
    (commonFields, typeFields, readOnly) = Extension.calculateFormFields(permissions)

    commonFields.append("next_url")
    flatFields = list(commonFields)
    for k, v in typeFields.items():
        flatFields.extend(v)

    # uniquify the list
    flatFields = list(set(flatFields))

    if quick_create:
        form_widgets = {
            val: HiddenInput() for val in flatFields if val not in QUICK_CREATE_FIELDS
        }
    else:
        form_widgets = {
            "owner": autocomplete.ModelSelect2(url="user.autocomplete"),
        }

    # make filtered out fields invisible
    if field_filter is not None:
        field_filter.append("next_url")

        flatFields = list(filter(lambda f: f in field_filter or f in MANDATORY_FIELDS, flatFields))
        form_widgets = {
            val: HiddenInput() for val in flatFields if val not in field_filter
        }
        if "owner" in flatFields:
            form_widgets["owner"] = autocomplete.ModelSelect2(url="user.autocomplete")
        readOnly.extend(set(flatFields).difference(field_filter))
        # we need to filter common and flat fields to get the layouter and validation work correctly
        commonFields = list(filter(lambda f: f in field_filter or f in MANDATORY_FIELDS, commonFields))
        typeFields = {k: list(filter(lambda f: f in field_filter or f in MANDATORY_FIELDS, typeFields[k])) for
                      k in typeFields.keys()}

    if read_only:
        readOnly = flatFields

    class ExtForm(ModelForm):
        next_url = CharField(widget=HiddenInput(), required=False)

        class Meta:
            model = Extension
            fields = flatFields
            widgets = form_widgets
            field_classes = {
                "forward_extension": ExtensionField,
            }

        def __init__(self, *args, **kwargs):
            self.event = kwargs.pop("event")
            self.user = kwargs.pop("user")
            next_url = kwargs.pop("next_url", "")

            self.perms = permissions
            super(ExtForm, self).__init__(*args, **kwargs)

            if form_types is None:
                validTypes = self.event.calculateFormExtensionTypes(permissions)
            else:
                validTypes = [(short, long) for (short, long) in EXTENSION_TYPES if short in form_types]
            self.fields["type"].choices = validTypes
            self.fields["announcement_lang"].initial = self.event.announcement_lang
            self.fields["next_url"].initial = next_url

            self._initialize_field_with_owned_audiofiles("ringback_tone")
            if "announcement_audio" in self.fields:
                self._initialize_field_with_owned_audiofiles("announcement_audio")

            if not self.instance.pk or self.instance.handset is None:
                # This is a creation form not an edit form
                self.fields["handset"].queryset = DECTHandset.get_unused(self.user, self.event)
            else:
                self.fields["handset"].queryset = DECTHandset.objects.filter(pk=self.instance.handset_id)
                self.fields["handset"].disabled = True

            if permissions & PERM_ADMIN and (field_filter is None or "lending" in field_filter):
                self.fields["lending"] = CharField(label=_("Inventory barcode of rental device"), required=False)
                if self.instance.pk is not None:
                    lending = self.instance.currentLending
                    if lending is not None:
                        self.fields["lending"].initial = lending.item.barcode

            if not(permissions & PERM_ORGA) and "rentalDeviceRequest" in self.fields:
                del self.fields["rentalDeviceRequest"]
            if not(permissions & PERM_ORGA) and "assignedRentalDevice" in self.fields:
                del self.fields["assignedRentalDevice"]

            for name, field in self.fields.items():
                field.disabled = field.disabled or (name in readOnly)
                if isinstance(field, ExtensionField):
                    field.event = self.event

        def _initialize_field_with_owned_audiofiles(self, field_name):
            if self.instance.owner is not None:
                self.fields[field_name].queryset = AudioFile.objects.filter(owner=self.instance.owner)
            else:
                self.fields[field_name].queryset = AudioFile.objects.filter(owner=self.user)

        def get_form_helper(self):
            helper = FormHelper()

            if quick_create:
                layout_fields = [Field(f) for f in QUICK_CREATE_FIELDS]
                layout_fields.extend([Field(f) for f in flatFields if f not in QUICK_CREATE_FIELDS])
                helper.layout = Layout(*layout_fields)
                helper.form_class = 'form-horizontal'
                helper.label_class = 'col-lg-2'
                helper.field_class = 'col-lg-8'
                helper.form_action = reverse("extension.new")
                helper.add_input(Submit("save", _("Create")))
            else:
                commonFieldsLayout = FormGroup(
                    *[Field(f) for f in commonFields if f not in Extension.special_layout_attributes],
                    GroupLabel(_("General Extension Configuration"))
                )
                lendingFields = [Field(f) for f in ["lending", "requestedRentalDevice", "assignedRentalDevice"]
                                 if f in self.fields]
                lendingFieldsLayout = FormGroup(
                    *lendingFields,
                    GroupLabel(_("Rental device")),
                )

                forwardFields = [Field(f) for f in ["forward_mode", "forward_extension"] if f in self.fields]
                if "forward_delay" in self.fields:
                    forwardFields.append(AppendedText("forward_delay", "s", css_class="col-sm-1"))
                forwardFieldsLayout = FormGroup(
                    *forwardFields,
                    HTML("<p class=\"text-info\">Warning: In contrast to callgroups, call forwarding has no"
                         " loop detection in this stage as this can be a feature in certain situations (e.g, mutual "
                         " forward on busy for two people that stand in for each other). If you end up"
                         " configuring a loop, the last forward will be automatically deactivated upon calling.</p>"),
                    GroupLabel(_("Call forwarding")),
                    id="forward_grouper",
                )

                typeFieldsLayout = [
                    FormGroup(
                        *[Field(f) for f in tf],
                        GroupLabel(Extension.getExtensionDesciption(t)),
                        css_class="form-ext-specific",
                        data_extension_type=t)
                    for t, tf in typeFields.items() if len(tf) != 0
                ]

                if len(lendingFields) > 0:
                    typeFieldsLayout.insert(0, lendingFieldsLayout)
                if len(forwardFields) > 0 or "forward_delay" in self.fields:
                    typeFieldsLayout.append(forwardFieldsLayout)

                helper.layout = Layout(commonFieldsLayout, *typeFieldsLayout)

                helper.add_input(Submit("save", _("Save")))
            return helper

        def full_clean(self):
            """Hook form cleaning

            We hook before form cleaning to update the list of required fields
            depending on the selected extension type
            """
            t = self.data.get("type")
            # Add fields for the required type to the list, if the type is invalid this
            # is caught in the type validation and does not hurt us here.
            required = commonFields + typeFields.get(t, [])

            # Remove all form fields from required list if they don't match current ext type
            # This approach preserves non-required inputs from the model
            for name, field in self.fields.items():
                if field.required:
                    field.required = (name in required)

            return super(ExtForm, self).full_clean()

        def clean_lending(self):
            barcode = self.cleaned_data.get("lending")
            if barcode is not None and len(barcode) > 0:
                try:
                    item = InventoryItem.find_item(barcode)
                    if barcode == self.fields["lending"].initial:
                        return item
                    if not item.isCurrentlyOnStock():
                        self.add_error("lending",
                                       ValidationError(_("This item is currently not on stock. Return it first."),
                                                       code="item-currently-lended"))
                        return None
                    return item
                except InventoryItem.DoesNotExist:
                    self.add_error("lending",
                                   ValidationError(_("No item found in inventory"),
                                                   code="no-item-found"))
                    return None
            return None

        def clean_extension(self):
            # Validation of the chosen extension (if changed)
            ext = self.cleaned_data.get("extension")
            # Check extension if changed or this object is not existing at all (extension claim case)
            if ext != self["extension"].initial or self.instance.pk is None:
                # Clean up input
                ext = ext.upper()

                if not re.match("^[A-Z0-9]+$", ext):
                    self.add_error("extension",
                                   ValidationError(_("Invalid characters in extension"),
                                                   code="extension-invalid"))

                ext = utils.extension_normalize(ext)

                # Check if the user is allowed to create this..
                try:
                    self.event.userIsAllowedToCreateExtension(self.user, ext, throw=True, perms=self.perms, current_ext=self["extension"].initial)
                except ExtensionNotAllowedException as e:
                    self.add_error("extension",
                                   ValidationError(_(
                                       "You are not allowed to take this extension:  ") + str(e.args[0]),
                                                   code="extension-not-permitted"))
                # now check if it is available
                if not self.event.checkIfExtensionIsFree(ext, current_ext=self["extension"].initial):
                    self.add_error("extension",
                                   ValidationError(_("Extension already taken. Try our random button."),
                                                   code="extension-taken"))
            return ext

        def clean_type_GSM(self):
            if not self.event.hasGSM:
                self.add_error("type",
                               ValidationError(_("This event does not have a GSM network."),
                                               code="gsm-invalid"))

            if not(self.cleaned_data.get("twoGOptIn", False) or self.cleaned_data.get("threeGOptIn", False)
                   or self.cleaned_data.get("fourGOptIn", False)):
                self.add_error("twoGOptIn",
                               ValidationError(_("You should not disable all access technologies. We recommend"
                                                 "using 2G"), code="gsm-no-access-tech"))

        def clean_type_ANNOUNCEMENT(self):
            if self.cleaned_data.get("announcement_audio") is None:
                self.add_error("announcement_audio",
                               ValidationError(_("Announcements must have an audio source."),
                                                 code="announcement-no-audio"))
            if self.cleaned_data.get("ringback_tone") is not None:
                self.add_error("ringback_tone",
                               ValidationError(_("Setting a ringback tone on an announcement can have no effect"),
                                               code="announcement-invalid-ringback"))

        def clean_forward_extension(self):
            ext = self.cleaned_data["forward_extension"]
            if isinstance(ext, Extension) and self.instance.pk is not None:
                if ext.pk == self.instance.pk:
                    self.add_error("forward_extension", ValidationError(_("You cannot forward to yourself."),
                                                                        code="forward-self"))
                if ext.type == "TRUNK":
                    self.add_error("forward_extension", ValidationError(_("You cannot forward to a trunk."),
                                                                        code="forward-to-trunk"))
            return ext

        def clean_sip_trunk(self):
            trunk = self.cleaned_data["sip_trunk"]
            if trunk:
                if self.instance.pk is not None and len(self.instance.group_members.all()) > 0:
                    self.add_error("sip_trunk",
                                   ValidationError(_("Extensions with multiring participants cannot be configured"
                                                     " as trunk."),
                                                   code="trunk-has-members"))
                if self.instance.pk is not None and len(self.instance.callgroups.all()) > 0:
                    self.add_error("sip_trunk",
                                   ValidationError(_("Extensions that are part of a group/multiring cannot be"
                                                     " configured as trunk."),
                                                   code="trunk-is-member"))
            return trunk

        def clean_isPremium(self):
            premium = self.cleaned_data["isPremium"]
            if premium and not self.event.hasPremium:
                self.add_error("isPremium", ValidationError(_("Premium SIP is not configured for this event."),
                                                            code="premium-unavailable"))
            return premium

        def clean(self):
            cleaned_data = super(ExtForm, self).clean()

            # ensure that forward is correctly configured
            if "forward_mode" in self.fields:
                mode = self.cleaned_data.get("forward_mode", "")
                if mode != "DISABLED" and cleaned_data.get("forward_extension") is None:
                    if "forward_extension" in self.fields:
                        self.add_error("forward_extension", ValidationError(_("You need to configure an extension in"
                                                                              " order to enable call forwarding."),
                                                                            code="forward-without-extension"))
                if ((self.instance.pk is not None and self.instance.sip_trunk or
                     self.cleaned_data.get("sip_trunk", False)) and mode != "DISABLED"):
                    self.add_error("forward_mode", ValidationError(_("You cannot forward from a trunk."),
                                                                   code="forward-from-trunk"))

            # Do type specific cleans if type is valid and they are present
            type = cleaned_data.get("type")
            if type:
                if hasattr(self, "clean_type_{}".format(type)):
                    getattr(self, "clean_type_{}".format(type))()

            trunk = self.cleaned_data.get("sip_trunk", False)
            if self.instance.pk is not None:
                trunk = trunk or self.instance.sip_trunk
            if trunk and type not in Extension.ALLOWED_TRUNK_TYPES:
                self.add_error("sip_trunk",
                               ValidationError(_("This extension type is not allowed to be configured as trunk."),
                                               code="trunk-invalid-type"))

            return cleaned_data

    return ExtForm

