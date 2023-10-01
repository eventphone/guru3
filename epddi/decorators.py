import functools
from typing import Optional, List
import json

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt

from core.utils import get_apikey_header


def json_request(mandatory_params: Optional[List] = None):
    def decorator_func(function):
        @functools.wraps(function)
        def wrapped_function(request, *args, **kwargs):
            if request.body is None or request.body == b"":
                return HttpResponseBadRequest(b"No content")
            try:
                body_data = request.body.decode(request.encoding or settings.DEFAULT_CHARSET)
            except UnicodeDecodeError:
                return HttpResponseBadRequest(b"Charset parsing error")
            try:
                data = json.loads(body_data)
            except json.JSONDecodeError:
                return HttpResponseBadRequest(b"Invalid JSON")

            if mandatory_params:
                for param in mandatory_params:
                    if param not in data:
                        return HttpResponseBadRequest(f"Missing data element in json request: '{param}'".encode("utf8"))
            kwargs["json_data"] = data
            return function(request, *args, **kwargs)
        return wrapped_function
    return decorator_func


def user_is_staff_or_epddi_apikey(function):
    @functools.wraps(function)
    def wrapped_function(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return function(request, *args, **kwargs)

        api_key = get_apikey_header(request)
        if api_key != "" and api_key == settings.EPDDI_API_KEY:
            return function(request, *args, **kwargs)
        raise PermissionDenied
    return csrf_exempt(wrapped_function)
