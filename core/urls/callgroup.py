from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.urls import path, re_path, reverse_lazy
from django.utils.translation import gettext_lazy as _


from core.session import getCurrentEvent
from core.models import Extension, CallGroupInvite
from core.views.callgroup import (CallgroupCreateView, CallgroupUpdateView, CallgroupAdminView,
                                  CallgroupAdminDeleteView, GroupMembershipView, check_if_owns_extension,
                                  check_if_group_admin_or_owns_extension)

from gcontrib.views.meta import FlexibleTemplateView
from gcontrib.views.edit import PermCheckDeleteView, PermissionCheckPropertySetterView

urlpatterns = [
    path("my",
         login_required(FlexibleTemplateView.as_view(
             template_name="callgroup/list.html",
             template_params={
                 "object_list":
                     lambda req, _: Extension.objects.filter(type="GROUP").filter(
                         Q(owner=req.user) | Q(group_admins=req.user) | Q(group_members__owner=req.user))
                         .distinct().prefetch_related("event")
                         .order_by("-event__end", "extension"),
                 "invites_list":
                     lambda req, _: CallGroupInvite.objects.filter(extension__event=getCurrentEvent(req),
                                                                   accepted=False)
                                                           .filter(Q(extension__owner=req.user) |
                                                                   Q(extension__group_admins=req.user))
                         .distinct().select_related("group", "extension")
                         .order_by("group__extension"),
             },
         )),
         name="callgroup.my"),
    path("new",
         login_required(CallgroupCreateView.as_view(
             template_name="extension/update.html",
             my_list_path=reverse_lazy("callgroup.my"),
         )),
         name="callgroup.new"),
    path("<int:pk>",
         login_required(CallgroupUpdateView.as_view(
             template_name="extension/update.html",
             my_list_path=reverse_lazy("extension.my"),
         )),
         name="callgroup.edit"),
    path("<int:pk>/admins/",
         login_required(CallgroupAdminView.as_view(
             template_name="callgroup/admin_list.html",
         )),
         name="callgroup.admins"),
    path("<int:pk>/admins/<int:related_pk>/delete",
         login_required(CallgroupAdminDeleteView.as_view(
             template_name="callgroup/admin_delete.html",
             success_url="../",
         )),
         name="callgroup.admins.delete"),
    path("<int:pk>/members",
         login_required(GroupMembershipView.as_view(
             template_name="callgroup/membership_editor.html",
         )),
         name="callgroup.members"),
    path("member/<int:pk>/delete",
         login_required(PermCheckDeleteView.as_view(
             model = CallGroupInvite,
             template_name="callgroup/member_delete.html",
             with_next=True,
             success_url=lambda self: self.get_next_view_path(),
         )),
         name="callgroup.member.delete"),
    path("member/<int:pk>/accept",
         login_required(PermissionCheckPropertySetterView.as_view(
             model=CallGroupInvite,
             post_permission_check_function=check_if_owns_extension,
             property_name="accepted",
             property_value=True,
         )),
         name="callgroup.member.accept"),
    path("member/<int:pk>/pause",
         login_required(PermissionCheckPropertySetterView.as_view(
             model=CallGroupInvite,
             post_permission_check_function=check_if_group_admin_or_owns_extension,
             property_name="active",
             property_value=False,
         )),
         name="callgroup.member.pause"),
    path("member/<int:pk>/resume",
         login_required(PermissionCheckPropertySetterView.as_view(
             model=CallGroupInvite,
             post_permission_check_function=check_if_group_admin_or_owns_extension,
             property_name="active",
             property_value=True,
         )),
         name="callgroup.member.resume"),
]
