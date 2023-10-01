from collections import OrderedDict

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from core.models import Extension, RecursiveSearchDepthLimitExceededException

from gcontrib.forms.factory import form_factory


class UsernameInput(forms.TextInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_results = {}

    def format_value(self, value):
        if value is None or value == '':
            return None
        if isinstance(value, str):
            return value
        if isinstance(value, User):
            return value.username

    def value_from_datadict(self, data, files, name):
        if name not in self._cached_results:
            try:
                user = User.objects.get(username=data.get(name, ""))
                self._cached_results[name] = user.pk
                return user.pk
            except User.DoesNotExist:
                input_data = data.get(name, "")
                # filter out pure numbers to prevent the underlying ModelChoice from interpreting it as valid pk
                if input_data.isnumeric():
                    return ""
                else:
                    return input_data
        else:
            return self._cached_results[name]


class InviteFormMixin:
    def __init__(self, *args, **kwargs):
        self.event = kwargs.pop("event")
        self.group = kwargs.pop("group")
        self.requester = kwargs.pop("requester")
        super().__init__(*args, **kwargs)

    @staticmethod
    def path_format(path):
        return " -> ".join(path)

    def clean_extension(self):
        extension = self.cleaned_data.get("extension")
        if extension is None:
            self.add_error("extension", ValidationError(_("No extension given"), code="extension-invalid"))

        try:
            ext = Extension.objects.get(event=self.event, extension=extension)
            if ext in self.group.group_members.all():
                self.add_error("extension", ValidationError(_("This extension is already part of the group."),
                                                            code="extension-already-present"))

            # check if it is recursively reachable
            try:
                result = ext.recursive_member_search(self.group.extension, [],
                                                     Extension.ALLOWED_GROUP_RECURSION_DEPTH)
                if result is not None:
                    self.add_error("extension", ValidationError(_("Adding this extension creates a loop: ")
                                                                + self.path_format(result),
                                                                code="extension-creates-loop"))
            except RecursiveSearchDepthLimitExceededException as e:
                self.add_error("extension",
                               ValidationError(_("The following path exceeds the current recursion limit: ") +
                                               self.path_format(e.path), code="extension-recursion-limit"))

            if ext.sip_trunk:
                self.add_error("extension", ValidationError(_("Trunk extensions cannot be part of groups / multiring"),
                                                            code="extension-is-trunk"))

            return ext
        except Extension.DoesNotExist:
            self.add_error("extension", ValidationError(_("This extension does not exist."),
                                                        code="extension-doesnt-exist"))

    def clean(self):
        if self.group.sip_trunk:
            raise ValidationError(_("Misconfiguration: You cannot add members to trunks"))
        return super().clean()


class InviteForm(InviteFormMixin, forms.Form):
    extension = forms.CharField(max_length=32, label=_("Extension"))
    invite_reason = forms.CharField(max_length=64, required=False, label=_("Invitation text"))


class MultiringInviteForm(InviteFormMixin, forms.Form):
    extension = forms.CharField(max_length=32, label=_("Extension"))

    def clean_extension(self):
        ext = super().clean_extension()
        if not isinstance(ext, Extension):
            return ext

        # additional permission check if multiring is allowed, we require that the user has
        # write permission to the target extension (e.i., owner, admin, group admin)
        if not ext.has_write_permission(self.requester):
            self.add_error("extension", ValidationError(_("You must own the extension that you want to add "
                                                          "for multiring"), code="extension-not-allowed"))
        return ext


CALLGROUP_MAX_MEMBER_DELAY = 600


def generate_delay_form(invites):
    fields = [
        ("delay_" + str(invite.pk), forms.IntegerField(min_value=0, max_value=CALLGROUP_MAX_MEMBER_DELAY))
        for invite in invites
    ]
    return form_factory("DelaysForm", OrderedDict(fields))
