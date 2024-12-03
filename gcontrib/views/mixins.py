from django.core.exceptions import PermissionDenied
from django.db.models import Model

from gcontrib.crispy_forms import defaultLayout


class FormHelperMixin(object):
    form_helper = None
    form_submit_button_text = None
    form_helper_name = "form_helper"

    def get_context_data(self, **kwargs):
        if self.form_helper is not None:
            kwargs[self.form_helper_name] = self.form_helper
        else:
            form = self.get_form_class()
            if hasattr(form, "form_helper"):
                kwargs[self.form_helper_name] = self.get_form().form_helper
            else:
                kwargs[self.form_helper_name] = defaultLayout(form, self.form_submit_button_text)
        return super(FormHelperMixin, self).get_context_data(**kwargs)


class ObjectPermCheckGETMixin(object):
    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.has_read_permission(self.request.user) and not request.user.is_staff:
            raise PermissionDenied
        return super().get(request, *args, **kwargs)


class ObjectPermCheckPOSTMixin(object):
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if not self.object.has_write_permission(self.request.user) and not request.user.is_staff:
            raise PermissionDenied
        return super().post(request, *args, **kwargs)


class ObjectPermCheckMixin(ObjectPermCheckGETMixin, ObjectPermCheckPOSTMixin):
    pass


class FunctorPermCheckGETMixin:
    get_permission_check_function = None

    def get(self, request, *args, **kwargs):
        if not self.get_permission_check_function(request, self):
            raise PermissionDenied
        return super().get(request, *args, **kwargs)


class FunctorPermCheckPOSTMixin:
    post_permission_check_function = None

    def post(self, request, *args, **kwargs):
        if not self.post_permission_check_function(request, self):
            raise PermissionDenied
        return super().post(request, *args, **kwargs)


class FunctorPermCheckMixin(FunctorPermCheckGETMixin, FunctorPermCheckPOSTMixin):
    pass


class FormViewPresaveHookMixin(object):
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.pre_save_hook(self.object, form)
        return super(FormViewPresaveHookMixin, self).form_valid(form)

    def pre_save_hook(self, object, form):
        pass


class CallableSuccessUrlMixin(object):
    def get_success_url(self):
        if callable(self.success_url):
            return self.success_url(self)
        else:
            return super(CallableSuccessUrlMixin, self).get_success_url()


class FlexibleTemplateParamsMixin(object):
    template_params = {}

    def get_context_data(self, **kwargs):
        context = super(FlexibleTemplateParamsMixin, self).get_context_data(**kwargs)
        for key, value in self.template_params.items():
            if callable(value):
                context[key] = value(self.request, self.kwargs)
            elif isinstance(value, type) and issubclass(value, Model):
                context[key] = value._default_manager.all()
            else:
                context[key] = value._clone()

        return context
