from captcha.fields import CaptchaField
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationFormUniqueEmail


class GuruAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')

        if '@' in username:
            raise forms.ValidationError(
                "Sorry, you cannot use your email to login. Please use your Username."
            )

        return super().clean()


class RegistrationFormUniqueEmailWithProfile(RegistrationFormUniqueEmail):
    captcha = CaptchaField(label="Captcha", help_text=_("Yes, you have to solve the equation!"))

    class Meta(RegistrationFormUniqueEmail.Meta):
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # The django way via help_texts in the Meta class is not working here, since username, password1 and email
        # are defined in super classes.
        self.fields["username"].help_text = _("Required. 150 characters or fewer. Letters, digits and ./+/-/_ only.")
        self.fields["password1"].help_text = _("Required.")
        self.fields["email"].help_text = _("Required. Please enter a valid address, because an activation link will be sent by email.")

    def clean_username(self):
        """
        Validate that the supplied username does not contain the @ character
        """
        if "@" in self.cleaned_data['username']:
            raise forms.ValidationError(_("@ is not allowed."))
        return self.cleaned_data['username']
