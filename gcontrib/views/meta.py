from django.views.generic import TemplateView

from gcontrib.views.mixins import FlexibleTemplateParamsMixin


class FlexibleTemplateView(FlexibleTemplateParamsMixin, TemplateView):
    pass