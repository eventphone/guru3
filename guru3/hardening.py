from django.forms.widgets import PasswordInput

passwordInput_init = getattr(PasswordInput, "__init__")

def _init_with_autocomplete_off(self, attrs=None, render_value=False):
    passwordInput_init(self, attrs, render_value)
    if "autocomplete" not in self.attrs:
        self.attrs["autocomplete"] = "off"

setattr(PasswordInput, "__init__", _init_with_autocomplete_off)
