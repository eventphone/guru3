from collections import OrderedDict

from django.forms import Form


def form_factory(name: str, fields: OrderedDict, form_class=Form):
    return type(form_class)(name, (form_class, ), fields)
