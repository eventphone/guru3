from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import path, re_path, include, reverse_lazy, register_converter
from django.views.generic import RedirectView
from django.views.static import serve
from core.forms.auth import RegistrationFormUniqueEmailWithProfile, GuruAuthenticationForm
from core.converters import LegacyHostingConverter, legacyPath
from core.views.common import SupportView
from core.views.registration import RegistrationViewWithRequest

register_converter(LegacyHostingConverter, 'ext')

@login_required
def protected_serve(request, path, document_root=None, show_indexes=False):
    return serve(request, path, document_root, show_indexes)

urlpatterns = [
     path('', RedirectView.as_view(
        url = reverse_lazy("event.phonebook", kwargs={'ext':'php'}),
     )),
     path('api/', include('core.urls.api')),
     path('admin/', include('core.urls.admin')),
     legacyPath('event.<ext:ext>/', include('core.urls.events')),
     path('event/', include('core.urls.events')),
     legacyPath('extension.<ext:ext>/', include('core.urls.extension')),
     path('extension/', include('core.urls.extension')),
     legacyPath('handset.<ext:ext>/', include('core.urls.handset')),
     path('handset/', include('core.urls.handset')),
     path('callgroup/', include('core.urls.callgroup')),
     legacyPath('callgroup.<ext:ext>/', include('core.urls.callgroup')),
     path('grandstream/', include('grandstream.urls')),
     path('snom/', include('snom.urls')),
     path('epddi/', include('epddi.urls')),
     path('inventory/', include('core.urls.inventory')),
     legacyPath('register.<ext:ext>', RegistrationViewWithRequest.as_view(
        form_class = RegistrationFormUniqueEmailWithProfile,
    ),
         name = "user.register"),
     path('register', RegistrationViewWithRequest.as_view(
        form_class = RegistrationFormUniqueEmailWithProfile,
    ),
         name = "user.register"),
    legacyPath('accounts.<ext:ext>/', include('django.contrib.auth.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    legacyPath('accounts.<ext:ext>/', include('django_registration.backends.activation.urls')),
    path('accounts/', include('django_registration.backends.activation.urls')),
    legacyPath('accounts/login.<ext:ext>', auth_views.LoginView.as_view(),
          {'template_name': 'registration/login.html',
           'authentication_form': GuruAuthenticationForm},
          name = 'login'),
    path('accounts/login', auth_views.LoginView.as_view(),
          {'template_name': 'registration/login.html',
           'authentication_form': GuruAuthenticationForm},
          name = 'login'),
    legacyPath('user.<ext:ext>/', include('core.urls.user')),
    path('user/', include('core.urls.user')),
    path('captcha/', include('captcha.urls')),
    path("support/",
         SupportView.as_view(
             template_name="support.html",
         ),
         name="support"),
    legacyPath('audio.<ext:ext>/', include('core.urls.audio')),
    path('audio/', include('core.urls.audio')),
    re_path(r'^%s(?P<path>.*)$' % settings.MEDIA_URL[1:], protected_serve, {'document_root': settings.MEDIA_ROOT}),
]

if not settings.DEBUG:
    from django.conf.urls import handler404
    from django.shortcuts import render
    handler404 = lambda req, exception: render(req, "404.html", {}, status=404)
