from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect, Http404, HttpResponseBadRequest, HttpResponse
from django.views.generic import CreateView, DeleteView, UpdateView, FormView, View
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.edit import FormMixin
from django.views.generic.detail import SingleObjectMixin, SingleObjectTemplateResponseMixin, BaseDetailView

from gcontrib.views.mixins import *


class CrispyCreateView(FormHelperMixin, CallableSuccessUrlMixin, CreateView):
    pass


class CrispyUpdateView(FormHelperMixin, CallableSuccessUrlMixin, UpdateView):
    pass


class OwnerSettingCrispyCreateView(FormViewPresaveHookMixin, CrispyCreateView):
    owner_attribute = "owner"

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["user"] = self.request.user
        return form_kwargs

    def pre_save_hook(self, object, form):
        if object.owner_id is None:
            setattr(object, self.owner_attribute, self.request.user)


class PermCheckCrispyUpdateView(ObjectPermCheckMixin, CrispyUpdateView):
    pass


class PermCheckDeleteView(CallableSuccessUrlMixin, DeleteView):
    with_next = False

    def get_next_view_path(self):
        return self.request.GET.get("next", "")

    def get_context_data(self, **kwargs):
        if self.with_next:
            kwargs["next_view_path"] = self.get_next_view_path()
        return super(PermCheckDeleteView, self).get_context_data(**kwargs)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.has_delete_permission(self.request.user) and not request.user.is_staff:
            raise PermissionDenied
        return super(PermCheckDeleteView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.has_delete_permission(self.request.user) and not request.user.is_staff:
            raise PermissionDenied
        return super(PermCheckDeleteView, self).delete(request, *args, **kwargs)


class RelationMixin:
    attribute = None

    def get_remote_model(self):
        field = self.model._meta.get_field(self.attribute)
        return field.related_model

    def get_field_verbose_name(self):
        field = self.model._meta.get_field(self.attribute)
        return field.verbose_name


class MultiFormMixin(FormMixin):
    def __init__(self, main_view, prefix):
        self.prefix = prefix
        self._main_view = main_view

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method in ("POST", "PUT") and self.get_active_form_mixin()[1] != self:
            # only the currently active form mixin should feed the form with submitted data
            del kwargs["data"]
            del kwargs["files"]
        return kwargs

    def get_context_data(self, **kwargs):
        if 'form_' + self.prefix not in kwargs:
            kwargs['form_' + self.prefix] = self.get_form()
        return super().get_context_data(**kwargs)

    # Forward unknown attributes to main_view
    def __getattr__(self, item):
        return getattr(self._main_view, item)


class CrispyMultiFormMixin(MultiFormMixin):
    form_helper = None
    form_submit_button_text = None
    form_helper_suffix = "_helper"

    def get_context_data(self, **kwargs):
        if self.form_helper is not None:
            kwargs[self.prefix + self.form_helper_suffix] = self.form_helper
        else:
            form = self.get_form_class()
            kwargs[self.prefix + self.form_helper_suffix] = defaultLayout(form,
                                                                        (self.prefix, self.form_submit_button_text))
        return super().get_context_data(**kwargs)


class MultiFormView(TemplateResponseMixin, View):
    forms_mixins_dict = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._forms_dict = {
            name: Mixin(self, name) for name, Mixin in self.forms_mixins_dict.items()
        }

    def get_context_data(self, **kwargs):
        for form in self._forms_dict.values():
            kwargs = form.get_context_data(**kwargs)
        return super().get_context_data(**kwargs)

    def get_active_form_mixin(self):
        # The implicit agreement is that the submit button should have the name of the active mixin
        for key in self.forms_mixins_dict.keys():
            if key in self.request.POST:
                return key, self._forms_dict.get(key)
        return None, None

    def get(self, request, *args, **kwargs):
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        name, form_mixin = self.get_active_form_mixin()
        if form_mixin is None:
            return HttpResponseBadRequest()

        form = form_mixin.get_form()
        if form.is_valid():
            return form_mixin.form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(**{"form_" + name: form}))


class ManyToManyListAddView(RelationMixin, SingleObjectMixin, FormView):
    model = None
    attribute = None
    context_related_list_name = "related_list"
    extra_form_field_params = {}

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)

    def get_form_class(self):
        if self.form_class is not None:
            return self.form_class
        else:
            RemoteModel = self.get_remote_model()
            field_params = {
                "queryset": RemoteModel._default_manager.all(),
                "label": self.get_field_verbose_name(),
            }
            field_params.update(self.extra_form_field_params)

            class DefaultForm(forms.Form):
                other = forms.ModelChoiceField(**field_params)
            return DefaultForm

    def get_context_data(self, **kwargs):
        related_name = self.context_related_list_name
        object = self.get_object()
        kwargs[related_name] = getattr(object, self.attribute).all()
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        object = self.get_object()
        getattr(object, self.attribute).add(form.cleaned_data["other"])
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
        if self.success_url:
            return self.success_url
        else:
            return self.request.path


class CrispyManyToManyListAddView(FormHelperMixin, ManyToManyListAddView):
    form_submit_button_text = "Add"


class RelatedObjectMixin(RelationMixin):
    attribute = None
    context_related_object_name = "related_object"
    related_pk_url_kwarg = 'related_pk'

    def get_related_object(self):
        if self.attribute is None:
            raise ImproperlyConfigured("Views with related object need \"attribute\" parameter to specify the"
                                       "releation attribute of the primary object")
        pk = self.kwargs.get(self.related_pk_url_kwarg)
        if pk is None:
            raise ImproperlyConfigured("Views with related objects need a related objected pk. Used {} but"
                                       " nothing found in view kwargs.".format(self.related_pk_url_kwarg))

        RemoteModel = self.get_remote_model()
        try:
            object = RemoteModel._default_manager.get(pk=pk)
        except RemoteModel.DoesNotExist:
            raise Http404
        return object

    def get_context_data(self, **kwargs):
        kwargs[self.context_related_object_name] = self.get_related_object()
        return super().get_context_data(**kwargs)


class ManyToManyDeleteView(RelatedObjectMixin, SingleObjectTemplateResponseMixin, BaseDetailView):
    """Provide the ability to delete items from manytomany lists."""
    success_url = None

    def delete(self, request, *args, **kwargs):
        """
        Call the delete() method on the fetched object and then redirect to the
        success URL.
        """
        self.object = self.get_object()
        self.related_object = self.get_related_object()
        getattr(self.object, self.attribute).remove(self.related_object)
        success_url = self.get_success_url()
        return HttpResponseRedirect(success_url)

    # Add support for browsers which only accept GET and POST for now.
    def post(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

    def get_success_url(self):
        if self.success_url:
            return self.success_url.format(**self.object.__dict__)
        else:
            raise ImproperlyConfigured(
                "No URL to redirect to. Provide a success_url.")


class PropertySetterView(SingleObjectMixin, View):
    property_name = None
    property_value = None
    success_url = None

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.redirect_url = self.request.POST.get("next", self.success_url)
        if callable(self.property_value):
            setattr(self.object, self.property_name, self.property_value(request, kwargs))
        else:
            setattr(self.object, self.property_name, self.property_value)
        self.object.save()
        if self.redirect_url:
            return HttpResponseRedirect(self.redirect_url)
        else:
            return HttpResponse()


class MultiPropertySetterView(SingleObjectMixin, View):
    properties = {}
    success_url = None

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.redirect_url = self.request.POST.get("next", self.success_url)
        for property_name, property_value in self.properties.items():
            if callable(property_value):
                setattr(self.object, property_name, property_value(request, kwargs))
            else:
                setattr(self.object, property_name, property_value)
        self.object.save()
        if self.redirect_url:
            return HttpResponseRedirect(self.redirect_url)
        else:
            return HttpResponse()


class PermissionCheckPropertySetterView(FunctorPermCheckPOSTMixin, PropertySetterView):
    pass


class PermissionCheckMultiPropertySetterView(FunctorPermCheckPOSTMixin, MultiPropertySetterView):
    pass
