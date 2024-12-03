from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.urls import path, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import DeleteView

from gcontrib.crispy_forms import defaultLayout
from gcontrib.decorators import user_is_staff, user_is_superuser
from gcontrib.views.edit import CrispyUpdateView
from gcontrib.views.list import SearchView
from core.decorators import user_is_current_event_admin
from core.forms.user import AdminUserEditForm
from core.views.user import (UserProfileView, userSearch, UserAutocompleteView, send_reset_password_link, InvoiceView,
                             UserApiKeyCreationView, delete_api_key, confirm_new_mail)

urlpatterns = [
    path("list",
         user_is_current_event_admin(SearchView.as_view(
             search_function=userSearch,
             allowed_ordering_keys=["username", "first_name", "last_name", "email"],
             default_ordering_key="username",
             paginate_by=20,
             model=User,
             template_name="user/list.html",
         )),
         name="user.list"),
    path("<int:pk>",
         user_is_staff(CrispyUpdateView.as_view(
             model=User,
             context_object_name="edit_user",
             form_class=AdminUserEditForm,
             form_helper=defaultLayout(AdminUserEditForm, _("Save")),
             template_name="user/update.html",
             success_url=reverse_lazy("user.list"),
         )),
         name="user.edit"),
    path("<int:pk>/delete",
         user_is_staff(DeleteView.as_view(
             model=User,
             context_object_name="delete_user",
             template_name="user/delete.html",
             success_url=reverse_lazy("user.list"),
         )),
         name="user.delete"),
    path("profile",
         login_required(UserProfileView.as_view(
             template_name="user/profile.html",
             success_url="/"
         )),
         name="user.profile"),
    path("newapikey",
         login_required(UserApiKeyCreationView.as_view(
             template_name="user/apikey.html",
         )),
         name="user.newapikey"),
    path("invoice",
         login_required(InvoiceView.as_view(
         )),
         name="user.invoice"),
    path("<int:pk>/invoice",
         user_is_staff(InvoiceView.as_view(
         )),
         name="user.invoice"),
    path("autocomplete",
        user_is_current_event_admin(UserAutocompleteView.as_view()),
        name="user.autocomplete"),
    path("<int:pk>/resetpassword",
         user_is_current_event_admin(send_reset_password_link),
         name="user.resetpassword"),
    path("<int:pk>/deleteapikey",
         user_is_superuser(delete_api_key),
         name="user.deleteapikey"),
    path("confirm_new_mail/<str:signed_data>",
         confirm_new_mail,
         name="user.confirm_new_mail"),
]
