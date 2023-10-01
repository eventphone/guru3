from django.core.exceptions import ImproperlyConfigured
from django.db.models.functions import Lower
from django.db.models import CharField, Q
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.views.generic import ListView
from django.views.generic.list import BaseListView

from gcontrib.views.mixins import FlexibleTemplateParamsMixin

def _parseOrderString(orderStr):
    if orderStr[0] == "-":
        return "-", orderStr[1:]
    else:
        return "", orderStr


class JsonListView(BaseListView):
    @staticmethod
    def object_transform(object, request, kwargs):
        return model_to_dict(object)

    def render_to_response(self, context):
        object_list = context.get("object_list", [])
        response_data = {
            "data": [self.object_transform(obj, self.request, self.kwargs) for obj in object_list]
        }
        return JsonResponse(response_data)

    def get_queryset(self):
        if callable(self.queryset):
            return self.queryset(self.request, self.kwargs)
        return super().get_queryset()


class SearchView(ListView):
    allowed_ordering_keys = None
    default_ordering_key = None
    search_function = None
    ordering_map = {}
    filters = []

    def get_ordering(self):
        displayOrder = None
        if self.ordering is None:
            requestedOrder = self.request.GET.get("order")
            if requestedOrder is None:
                (orderDir, order) = _parseOrderString(self.default_ordering_key)
            else:
                (orderDir, orderKey) = _parseOrderString(requestedOrder)

                if orderKey in self.allowed_ordering_keys:
                    if orderKey in self.ordering_map:
                        order = self.ordering_map[orderKey]
                        displayOrder = orderKey
                    else:
                        order = orderKey
                else:
                    (orderDir, order) = _parseOrderString(self.default_ordering_key)
        else:
            # the order is fixed to ordering
            (orderDir, order) = _parseOrderString(self.ordering)

        if displayOrder is not None:
            self.order = orderDir + displayOrder
        else:
            self.order = orderDir + order

        try:
            if self.model is not None and isinstance(order, str):
                field = self.model._meta.get_field(order)
                if isinstance(field, CharField):
                    order = Lower(order)
        finally:
            if isinstance(order, str):
                return orderDir + order
            else:
                return order if orderDir == "" else order.desc()

    def get_filter(self):
        filter_dict = {key: transform(self.request.GET[req_key]) for (req_key, key, transform) in self.filters
                       if req_key in self.request.GET}
        if filter_dict:
            return Q(**filter_dict)

    def get_queryset(self):
        if self.search_function is None or not callable(self.search_function):
            raise ImproperlyConfigured("SearchView needs a search_function")
        query = self.request.GET.get("q", "").strip()
        search_query = self.search_function(query, self.request)
        filter_q = self.get_filter()
        if filter_q:
            search_query = search_query.filter(filter_q)
        ordering = self.get_ordering()
        if ordering:
            if not (isinstance(ordering, tuple) or isinstance(ordering, list)):
                ordering = (ordering,)
            ordering = ordering + ("pk",)  # enforce stable ordering also in presense of LIMIT
            return search_query.order_by(*ordering)
        else:
            return search_query

    def get_context_data(self, **kwargs):
        searchParams = {"order": self.order}
        for key in next(zip(*self.filters), []):
            if key in self.request.GET:
                searchParams[key] = self.request.GET[key]
        if "q" in self.request.GET:
            searchParams["q"] = self.request.GET["q"]

        kwargs["search_params"] = searchParams
        return super(SearchView, self).get_context_data(**kwargs)


class SearchViewWithExtraParams(FlexibleTemplateParamsMixin, SearchView):
    pass
