from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, Submit, Div, HTML


def GroupLabel(labelStr):
    return Div(HTML(labelStr), css_class="form-grouper-label")


def FormGroup(*args, **kwargs):
    if "css_class" in kwargs:
        kwargs["css_class"] = kwargs["css_class"] + " form-grouper"
    else:
        kwargs["css_class"] = "form-grouper"

    return Div(*args, **kwargs)


def defaultLayout(form, submitButtonName):
    fields = [Field(f) for f, _ in form.base_fields.items()]
    helper = FormHelper()
    helper.layout = Layout(*fields)
    if isinstance(submitButtonName, tuple):
        helper.add_input(Submit(*submitButtonName))
    else:
        helper.add_input(Submit("save", submitButtonName))
    return helper
