from django.urls import re_path, path
from django.shortcuts import get_object_or_404

from gcontrib.decorators import user_is_staff
from gcontrib.views.meta import FlexibleTemplateView
from snom.views import provisioning
from snom.models import SnomFirmware

urlpatterns = [
    re_path(r"^prov/(?P<mac>[a-fA-Z0-9]{12})",
            provisioning,
            name="snom.provisioning"),
    re_path(r"^provdebug/(?P<mac>[a-fA-Z0-9]{12})",
            user_is_staff(provisioning),
            kwargs={"admin": True},
            name="snom.provisioning.debug"),
    path("firmware/<str:model>.xml",
         FlexibleTemplateView.as_view(
             template_params={
                 "firmware": lambda _r, kwargs: get_object_or_404(SnomFirmware, model=kwargs["model"]),
             },
             template_name="snom/firmware.xml",
         ),
        name="snom.provisioning.firmware"
    )

]
