from datetime import date
from typing import Optional

from django.core import signing

from core.models import Event, RegistrationEmailToken

def get_register_token(request):
    token = request.session.get("register_token", None)
    if token is None:
        token = RegistrationEmailToken.new_token()
        request.session["register_token"] = token.pk
    else:
        token = RegistrationEmailToken.objects.get(pk=token)
    return token

def sign_current_url(request):
    data = {
        "session": request.session.session_key,
        "url": request.get_full_path(),
    }
    return signing.dumps(data)


def extract_signed_url(request, signed_data):
    try:
        data = signing.loads(signed_data)
        if data.get("session", "") == request.session.session_key:
            return data.get("url")
    except signing.BadSignature:
        return None


def getCurrentEvent(request) -> Optional[Event]:
    currEventId = request.session.get("currentEventId", None)
    if currEventId:
        try:
            event = Event.objects.get(pk=currEventId)
            if request.user.is_staff:
                return event
            # if it became past, we need to reselect a new one if this is a normal user
            if not event.isPermanent and date.today() <= event.end:
                if event.registrationStart <= date.today():
                    return event
                elif event.isEventOrga(request.user):
                    return event
            elif event.isPermanent and event.isPermanentAndPublic and request.user.is_authenticated:
                return event
        except Event.DoesNotExist:
            pass

    # If none is set or the one that is set is gone (e.g., deleted)
    # First, select the upper most running event
    running = Event.getRunning(request.user)
    if len(running) > 0:
        event = running[0]
        request.session["currentEventId"] = event.pk
        return event

    # Second, try upcomming events
    upcomming = Event.getUpcoming(request.user)
    if len(upcomming) > 0:
        event = upcomming[0]
        request.session["currentEventId"] = event.pk
        return event

    # Third, try permant events
    permant = Event.getPermanent(request.user)
    if len(permant) > 0:
        event = permant[0]
        request.session["currentEventId"] = event.pk
        return event

    # Well that's unfortunate.. No event found
    return None


def setCurrentEvent(request, event):
    if not request.user.is_staff:
        if event.isPermanent:
            if not event.isPermanentAndPublic:
                return
        else:
            if event.end < date.today():
                return
    request.session["currentEventId"] = event.pk
