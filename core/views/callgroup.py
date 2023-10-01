from django.core.exceptions import PermissionDenied
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponse, HttpResponseNotFound
from django.shortcuts import Http404
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.utils.text import format_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.detail import SingleObjectMixin

from core.models import Extension, CallGroupInvite
from core.session import getCurrentEvent
from core import messaging
from core.forms.extension import generateExtensionForm
from core.forms.callgroup import (UsernameInput, InviteForm, MultiringInviteForm, generate_delay_form,
                                  CALLGROUP_MAX_MEMBER_DELAY)
from core.views.extension import ExtensionCreateView, ExtensionUpdateView

from gcontrib.views.api import JsonApiView
from gcontrib.views.edit import (CrispyManyToManyListAddView, ManyToManyDeleteView, CrispyMultiFormMixin, MultiFormView,
                                 PropertySetterView, MultiFormMixin)
from gcontrib.views.mixins import ObjectPermCheckGETMixin, ObjectPermCheckMixin


class CallgroupCreateView(ExtensionCreateView):
    def get_form(self, form_class=None):
        form_class = generateExtensionForm(self.perms, field_filter=Extension.group_display_fields,form_types=["GROUP"])
        form_kwargs = self.get_form_kwargs()
        form = form_class(**form_kwargs)
        form.fields["type"].initial = "GROUP"
        return form


class CallgroupUpdateView(ExtensionUpdateView):
    def get_form(self, form_class=None):
        read_only = False
        if not self.get_object().has_write_permission(self.request.user):
            read_only = True
        form_class = generateExtensionForm(self.perms, field_filter=Extension.group_display_fields,
                                           form_types=["GROUP"],read_only=read_only)
        form_kwargs = self.get_form_kwargs()
        return form_class(**form_kwargs)


class CallgroupOwnerCheckMixin:
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.owner == request.user and not self.object.event.isEventAdmin(request.user):
            self.object = self.get_object()
            raise PermissionDenied
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.owner == request.user and not self.object.event.isEventAdmin(request.user):
            raise PermissionDenied
        return super().post(request, *args, **kwargs)


class CallgroupAdminView(CallgroupOwnerCheckMixin, CrispyManyToManyListAddView):
    model = Extension
    attribute = "group_admins"
    template_name = "callgroup/admin_list.html",
    extra_form_field_params={
        "label": _("Add callgroup administrator"),
        "widget": UsernameInput,
    }


class CallgroupAdminDeleteView(CallgroupOwnerCheckMixin, ManyToManyDeleteView):
    model = Extension
    attribute = "group_admins"


class BaseInviteMemberFormMixin(CrispyMultiFormMixin):

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        group = self.get_object()
        kwargs["event"] = group.event
        kwargs["group"] = group
        kwargs["requester"] = self.request.user
        return kwargs


class InviteMemberFormMixin(BaseInviteMemberFormMixin):
    form_submit_button_text = "Invite"
    form_class = InviteForm
    success_url = "members"

    def form_valid(self, form):
        invite = CallGroupInvite(group=self.get_object(), extension=form.cleaned_data["extension"],
                                 inviter=self.request.user, invite_reason=form.cleaned_data["invite_reason"])
        invite.save()
        return super().form_valid(form)


class MultiringMemberFormMixin(BaseInviteMemberFormMixin):
    form_submit_button_text = "Add"
    form_class = MultiringInviteForm
    success_url = "multiring"

    def form_valid(self, form):
        invite = CallGroupInvite(group=self.get_object(), extension=form.cleaned_data["extension"],
                                 inviter=self.request.user, accepted=True)
        invite.save()
        return super().form_valid(form)


class DelaysUpdateFormMixin(MultiFormMixin):
    def get_success_url(self):
        return self.request.path + "?expert_mode=1"

    def get_form_class(self):
        return generate_delay_form(self.group_invites)

    def get_initial(self):
        return {
            "delay_" + str(invite.pk): invite.delay_s for invite in self.group_invites
        }

    def form_valid(self, form):
        with transaction.atomic():
            updated = False
            for invite in self.group_invites:
                try:
                    new_delay = form.cleaned_data["delay_" + str(invite.pk)]
                    if invite.delay_s != new_delay:  # only generate messages if changed
                        invite.delay_s = new_delay
                        invite.save(no_messaging=True)
                        updated = True
                except KeyError:
                    pass  # Someone might have removed this group member meanwhile, we just ignore this
            if updated:
                update_msg = messaging.makeGroupUpdateMessage(self.get_object())
                update_msg.save()

        return super().form_valid(form)


class BaseMembershipView(ObjectPermCheckMixin, MultiFormView, SingleObjectMixin):
    model = Extension

    @cached_property
    def group_invites(self):
        object = self.get_object()
        invites = CallGroupInvite.objects.filter(group=object)
        return list(invites)

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        delays_form = kwargs.get("form_delays")
        kwargs["group_invites_delays"] = list(zip(self.group_invites, iter(delays_form)))
        return kwargs


class GroupMembershipView(BaseMembershipView):
    forms_mixins_dict = {
        "invite_member": InviteMemberFormMixin,
        "delays": DelaysUpdateFormMixin,
    }


class MultiringMembershipView(BaseMembershipView):
    forms_mixins_dict = {
        "invite_member": MultiringMemberFormMixin,
        "delays": DelaysUpdateFormMixin,
    }

    def get_object(self):
        object = super().get_object()
        # This view is not for groups!
        if object.type == "GROUP":
            raise PermissionDenied
        # And we don't want it on Annoucements either
        if object.type == "ANNOUNCEMENT":
            raise PermissionDenied
        return object


def check_if_group_admin_or_owns_extension(request, view):
    invite = view.get_object()
    if invite.group.has_write_permission(request.user):
        return True
    return check_if_owns_extension(request, view)


def check_if_owns_extension(request, view):
    invite = view.get_object()
    if invite.group.event.isEventAdmin(request.user):
        return True
    if invite.extension.owner == request.user:
        return True
    if invite.extension.type == "GROUP" and invite.extension.group_admins.filter(pk=request.user.pk).exists():
        return True
    return False


class SerializationError(Exception):
    def __init__(self, error_msg):
        self.error_msg = error_msg


class CallgroupMemberSerialierDeserializer:
    def __init__(self, callgroup):
        self._callgroup = callgroup

    @staticmethod
    def serialize_member(member):
        return {
            "accepted": member.accepted,
            "active": member.active,
            "delay_s": member.delay_s,
            "invite_reason": member.invite_reason,
        }

    @staticmethod
    def update_membership_params(membership, values):
        if "active" in values:
            membership.active = values["active"]
        if "delay_s" in values:
            membership.delay_s = values["delay_s"]

    @staticmethod
    def update_self_controlled_membership_params(membership, values):
        if "active" in values:
            membership.active = values["active"]
        if "accepted" in values:
            # this is a one-way street
            membership.accepted = values["accepted"] or membership.accepted

    def member_from_data(self, target, data, inviter):
        membership = CallGroupInvite(group=self._callgroup, extension=target, invite_reason=data["invite_reason"],
                                     inviter=inviter)
        self.update_membership_params(membership, data)
        return membership

    def serialize(self, include_admins=False):
        memberships = CallGroupInvite.objects.select_related("extension").filter(group=self._callgroup)
        result = {
            "members": {
                member.extension.extension: self.serialize_member(member) for member in memberships
            }
        }
        if include_admins:
            result["admins"] = [user.username for user in self._callgroup.group_admins.all()]
        return result

    def update(self, new_values):
        with transaction.atomic():
            memberships = CallGroupInvite.objects.select_related("extension").filter(group=self._callgroup)
            invites_dict = {
                member.extension.extension: member for member in memberships
            }
            for member, values in new_values["members"].items():
                if member not in invites_dict:
                    raise SerializationError(f"Extension {member} is not part of callgroup "
                                             f"{self._callgroup.extension}. This interface cannot be used to add "
                                             f"new members. See API documentation.")
                invite = invites_dict[member]
                self.update_membership_params(invite, values)
                invite.save(no_messaging=True)
            update_msg = messaging.makeGroupUpdateMessage(self._callgroup)
            update_msg.save()


class EventExtensionObjectMixin:
    def get_object(self):
        try:
            return Extension.objects.select_related("event") \
                                    .filter(event=self.kwargs["event"], extension=self.kwargs["extension"]).get()
        except Extension.DoesNotExist:
            raise Http404


class CallgroupMembershipApiView(ObjectPermCheckMixin, EventExtensionObjectMixin, SingleObjectMixin, JsonApiView):
    http_method_names = ["get", "post"]

    json_schema = {
        "$id": format_lazy("{}{}", settings.INSTALLATION_BASE_URL, reverse_lazy("callgroup.api.schema")),
        "$schema": "http://json-schema.org/draft-07/schema#",
        "description": "Input schema for guru3 callgroup API",
        "type": "object",
        "properties": {
            "members": {
                "type": "object",
                "patternProperties": {
                    "^\\d+$": {
                        "type": "object",
                        "properties": {
                            "active": {"type": "boolean"},
                            "delay_s": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": CALLGROUP_MAX_MEMBER_DELAY,
                            },
                        },
                        "additionalProperties": False
                    },
                },
                "additionalProperties": False
            },
        },
        "required": ["members"],
    }

    def process_get(self, request):
        if self.object.type != "GROUP":
            raise Http404

        serializer = CallgroupMemberSerialierDeserializer(self.object)
        include_admins = self.request.user == self.object.owner or self.object.event.isEventAdmin(self.request.user)
        return self.json_response(serializer.serialize(include_admins))

    def process_post(self, request, json_data):
        if self.object.type != "GROUP":
            raise Http404

        serializer = CallgroupMemberSerialierDeserializer(self.object)
        try:
            serializer.update(json_data)
            return self.get(request)
        except SerializationError as e:
            return HttpResponseBadRequest(e.error_msg)


class CallgroupMemberApiView(ObjectPermCheckGETMixin, EventExtensionObjectMixin, SingleObjectMixin, JsonApiView):
    http_method_names = ["get", "post", "put", "delete"]

    json_schema = {
        "$id": format_lazy("{}{}", settings.INSTALLATION_BASE_URL, reverse_lazy("callgroup.member.api.schema")),
        "$schema": "http://json-schema.org/draft-07/schema#",
        "description": "Input schema for guru3 callgroup API",
        "type": "object",
        "properties": {
            "invite_reason": {"type": "string"},
            "accepted": {"type": "boolean"},
            "active": {"type": "boolean"},
            "delay_s": {
                "type": "integer",
                "minimum": 0,
                "maximum": CALLGROUP_MAX_MEMBER_DELAY,
            },
        },
        "additionalProperties": False,
    }

    def get_membership(self, raise_404=True):
        try:
            return CallGroupInvite.objects.select_related("extension") \
                                          .get(group=self.object,
                                               extension__extension=self.kwargs["member_extension"])
        except CallGroupInvite.DoesNotExist:
            if raise_404:
                raise Http404

    def json_response_membership(self, membership, status=200):
        return self.json_response(CallgroupMemberSerialierDeserializer.serialize_member(membership), status=status)

    def process_get(self, request):
        if self.object.type != "GROUP":
            raise Http404
        membership = self.get_membership()
        return self.json_response_membership(membership)

    def process_delete(self, request):
        self.object = self.get_object()
        if self.object.type != "GROUP":
            raise Http404
        membership = self.get_membership()
        if (not self.object.has_write_permission(request.user)
                and not membership.extension.has_write_permission(request.user)):
            raise PermissionDenied
        with transaction.atomic():
            membership.delete()
        return HttpResponse("Deleted")

    def process_post(self, request, json_data):
        return self.process_put(request, json_data)

    def process_put(self, request, json_data):
        self.object = self.get_object()
        if self.object.type != "GROUP":
            raise Http404
        # we allow users to pause/unpause themselves and to accept their invitations, so we check only
        #  read permission here.
        if not self.object.has_read_permission(request.user):
            raise PermissionDenied

        try:
            membership = self.get_membership(raise_404=False)
            if membership is None:
                if not self.object.has_write_permission(request.user):
                    raise PermissionDenied
                return self.create_new_membership(request, json_data)
            # this is a membership update
            member_write_perms = membership.extension.has_write_permission(request.user)
            group_write_perms = self.object.has_write_permission(request.user)
            if not member_write_perms and not group_write_perms:
                raise PermissionDenied
            if member_write_perms:
                CallgroupMemberSerialierDeserializer.update_self_controlled_membership_params(membership, json_data)
            if group_write_perms:
                CallgroupMemberSerialierDeserializer.update_membership_params(membership, json_data)
            with transaction.atomic():
                membership.save()
            return self.json_response_membership(membership)
        except SerializationError as e:
            return HttpResponseBadRequest(e.error_msg)

    def create_new_membership(self, request, json_data):
        try:
            target = Extension.objects.get(event=self.kwargs["event"], extension=self.kwargs["member_extension"])
        except Extension.DoesNotExist:
            return HttpResponseNotFound(f"Target extension {self.kwargs['member_extension']} is not known"
                                        f"in this event.")
        # Validate the request
        validation_form = InviteForm({
            "extension": target.extension,
            "invite_reason": json_data.get("invite_reason"),
            },
            event=self.object.event,
            group=self.object,
            requester=request.user,
        )
        if not validation_form.is_valid():
            return self.json_response({
                "validation_errors": validation_form.errors.get_json_data()
            }, status=422)
        if "accepted" in json_data and json_data["accepted"]:
            return self.json_response({
                "validation_errors": {
                    "accepted": "New memberships must be created in non-accepted mode."
                }
            }, status=422)

        serializer = CallgroupMemberSerialierDeserializer(self.object)
        membership = serializer.member_from_data(target, json_data, request.user)
        with transaction.atomic():
            membership.save()
        return self.json_response_membership(membership, status=201)





