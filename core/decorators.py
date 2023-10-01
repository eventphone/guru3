import functools

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from core.models import Event, PERM_ADMIN, PERM_ORGA
from core.session import getCurrentEvent
from core.views.common import vacationView
from core.utils import get_apikey_header


def can_access_phonebook(req_func):
    def request_handler(request, *args, **kwargs):
        event = getCurrentEvent(request)

        if event is None:
            return vacationView(request)

        if (event is not None and not event.isPhonebookPublic()
                and not request.user.is_authenticated):
            return redirect_to_login(request.path)
        else:
            return req_func(request, *args, **kwargs)

    return request_handler


def event_from_mgr_api_key(apiKey):
    if apiKey is not None:
        keyparts = apiKey.split("$", 1)
        if len(keyparts) != 2:
            raise PermissionDenied
        if not keyparts[0].isnumeric():
            raise PermissionDenied
        try:
            event = Event.objects.get(pk=keyparts[0])
        except Event.DoesNotExist:
            raise PermissionDenied
        if event.check_mgr_key(keyparts[1]):
            return event
        return None


def user_is_staff_or_mgr_apikey(reqfn):
    @functools.wraps(reqfn)
    def requestHandler(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.is_staff:
            return reqfn(request, *args, **kwargs)

        apiKey = get_apikey_header(request)
        if apiKey is not None:
            event = event_from_mgr_api_key(apiKey)
            if event is not None:
                kwargs["event"] = event
                try:
                    return reqfn(request, *args, **kwargs)
                except TypeError:
                    # it might be that reqfn doesn't want to receive the event param, so try again
                    # I don't think that this is a supernice solution but feel encouraged by
                    # https://docs.python.org/3/glossary.html#term-eafp
                    del kwargs["event"]
                    return reqfn(request, *args, **kwargs)
            else:
                raise PermissionDenied

        if request.user.is_authenticated and request.user.is_staff:
            return reqfn(request, *args, **kwargs)
        else:
            raise PermissionDenied
    return requestHandler


def user_is_current_event_admin(req_function):
    return user_is_event_test(req_function, lambda user, event: event.isEventAdmin(user))


def user_is_current_event_admin_or_orga(req_function):
    return user_is_event_test(req_function,
                              lambda user, event: event.getUserPermissions(user) & (PERM_ADMIN | PERM_ORGA))


def user_is_event_test(req_function, test_function):
    @functools.wraps(req_function)
    def request_handler(request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied

        # speed up the decision for staff members
        if request.user.is_staff:
            return req_function(request, *args, **kwargs)

        event = getCurrentEvent(request)
        if event is None:
            raise PermissionDenied
        if test_function(request.user, event):
            return req_function(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return request_handler
