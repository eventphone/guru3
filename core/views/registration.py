from django_registration.backends.activation.views import RegistrationView


class RegistrationViewWithRequest(RegistrationView):
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs