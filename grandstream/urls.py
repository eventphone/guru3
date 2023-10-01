from django.urls import re_path

from grandstream.views import get_encrypted_config, get_initial_config, get_screen_config

urlpatterns = [
    re_path(r"^initial/cfg(?P<mac>[a-fA-Z0-9]{12})\.xml",
            get_initial_config,
            name="grandstream.initial_phonecfg"),
    re_path(r"^config/cfg(?P<mac>[a-fA-Z0-9]{12})\.xml",
            get_encrypted_config,
            name="grandstream.phonecfg"),
    re_path(r"^screen/(?P<mac>[a-fA-Z0-9]{12})/idle_screen\.xml",
            get_screen_config,
            name="grandstream.phonecfg_screen"),
]
