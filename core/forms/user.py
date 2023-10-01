from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _


class AdminUserEditForm(ModelForm):
    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "is_active",
            "is_staff",
        ]


class UserProfileForm(ModelForm):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if self.instance is not None and self.instance.email == email:
            return email
        if User.objects.filter(email__iexact=email).count() > 0:
            self.add_error("email",
                           ValidationError(_("This email is already used by another account."),
                                           code="email-invalid"))


        return email
