from django.urls import reverse
from django.http import HttpResponseRedirect
from django.utils.http import urlencode


def redirect_with_params(url_name, params, *args, **kwargs):
    url = reverse(url_name, args=args, kwargs=kwargs)
    urlencoded_params = urlencode(params)
    return HttpResponseRedirect(url + f"?{urlencoded_params}")