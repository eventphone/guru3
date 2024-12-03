from captcha.fields import CaptchaField
from django import forms
from django.forms import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationFormUniqueEmail

from core.session import get_register_token
from core.models import RegistrationEmailToken


class GuruAuthenticationForm(AuthenticationForm):
    def clean(self):
        username = self.cleaned_data.get('username')

        if '@' in username:
            raise forms.ValidationError(
                "Sorry, you cannot use your email to login. Please use your Username."
            )

        return super().clean()


class RegistrationFormUniqueEmailWithProfile(RegistrationFormUniqueEmail):
    token = forms.CharField(max_length=32, disabled=True)

    class Meta(RegistrationFormUniqueEmail.Meta):
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "token",
        ]

    def __init__(self, *args, **kwargs):
        request = kwargs.pop("request")
        super().__init__(*args, **kwargs)
        # The django way via help_texts in the Meta class is not working here, since username, password1 and email
        # are defined in super classes.
        self.fields["username"].help_text = _("Required. 150 characters or fewer. Letters, digits and ./+/-/_ only.")
        self.fields["password1"].help_text = _("Required.")
        self.fields["email"].help_text = _("Required. Please enter a valid address, because an activation link will be sent by email.")
        self.fields["token"].help_text = _("Please send this token in the subject of an email to register@guru3.eventphone.de BEFORE submitting the form.")

        token = get_register_token(request)
        self.fields["token"].initial = token.token


    def clean_username(self):
        """
        Validate that the supplied username does not contain the @ character
        """
        if "@" in self.cleaned_data['username']:
            raise forms.ValidationError(_("@ is not allowed."))
        return self.cleaned_data['username']

    def clean_token(self):
        token = self.fields["token"].initial
        try:
            token_obj = RegistrationEmailToken.objects.get(token=token)
            if not token_obj.confirmed:
                raise ValidationError("This token is not confirmed yet. You either need to send the mail or wait a bit until the email was processed on our end. Try again in one minute.")
        except RegistrationEmailToken.DoesNotExist:
            raise ValidationError("Unknown token. Please refresh the page.")
        return token
