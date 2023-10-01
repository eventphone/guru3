from django.views.generic.detail import DetailView

from gcontrib.views.mixins import ObjectPermCheckGETMixin, FlexibleTemplateParamsMixin


class PermCheckDetailView(ObjectPermCheckGETMixin, DetailView):
    pass


class FlexibleTemplateDetailView(FlexibleTemplateParamsMixin, DetailView):
    pass


class PermCheckFlexibleTemplateDetailView(ObjectPermCheckGETMixin, FlexibleTemplateDetailView):
    pass
