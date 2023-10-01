from django.urls import re_path

from gcontrib.decorators import user_is_staff
from snom.views import provisioning

urlpatterns = [
    re_path(r"^prov/(?P<mac>[a-fA-Z0-9]{12})",
            provisioning,
            name="snom.provisioning"),
    re_path(r"^provdebug/(?P<mac>[a-fA-Z0-9]{12})",
            user_is_staff(provisioning),
            kwargs={"admin": True},
            name="snom.provisioning.debug"),
]
