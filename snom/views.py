import re

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import Http404, reverse

from snom.models import SnomPhone

CN_MAC_RE = re.compile("CN=([0-9A-Fa-f]{12})(?:,|/|$)")
PHONE_TYPE_RE = re.compile("(snomD?\\d+)-SIP")


SNOM_CAS = [
    ("CN=Snom Phone 1,O=Snom Technology AG,L=Berlin,ST=Berlin,C=DE",
     "/C=DE/ST=Berlin/L=Berlin/O=Snom Technology AG/CN=Snom Phone 1"),
    ("CN=Snom Phone 1 SHA-256,O=snom technology AG,L=Berlin,ST=Berlin,C=DE",
     "/C=DE/ST=Berlin/L=Berlin/O=snom technology AG/CN=Snom Phone 1 SHA-256"),
]


def verify_snom_ca(ca_name):
    return any([ca_name.endswith(ca[0]) or ca_name.startswith(ca[1]) for ca in SNOM_CAS])

def provisioning(request, mac, admin=False):
    user_agent = request.META.get("HTTP_USER_AGENT", None)
    mac = mac.upper()

    if not admin:
        # check that phone is authenticated and request is valid
        CA_DN = request.META.get("HTTP_X_FORWARDED_CLIENT_CERT_I_DN", None)
        CERT_SUBJECT = request.META.get("HTTP_X_FORWARDED_CLIENT_CERT_S_DN", None)
        if CA_DN is None or CERT_SUBJECT is None:
            raise PermissionDenied
        if not verify_snom_ca(CA_DN):
            raise PermissionDenied
        mac_match = CN_MAC_RE.search(CERT_SUBJECT)
        if not mac_match:
            raise PermissionDenied
        if mac_match.group(1).upper() != mac:
            raise PermissionDenied

    try:
        snom_phone = SnomPhone.objects.get(mac=mac)
    except SnomPhone.DoesNotExist:
        # check if we have it in the inventory database
        snom_phone = SnomPhone.create_for_mac(mac)
        if snom_phone.get_inventory_item() is None:
            raise Http404
        m = PHONE_TYPE_RE.search(user_agent)
        if m:
            snom_phone.model = m.group(1)

    snom_phone.userAgent = user_agent
    snom_phone.save()

    this_url = request.build_absolute_uri("/snom/prov/") + "{mac}"  # do not url encode {mac}

    provisioning_xml = snom_phone.get_xml_config(this_url)
    if provisioning_xml is None:
        raise Http404
    return HttpResponse(provisioning_xml, content_type="application/xml")




