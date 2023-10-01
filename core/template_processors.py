from django.utils.functional import SimpleLazyObject
from django.db.models import Q

from core.models import Event, CallGroupInvite
from core.session import getCurrentEvent, sign_current_url

try:
    from epddi.models import EPDDIClient
    epddi_active = True
except ImportError:
    epddi_active = False


def events_processor(request):
    currentEvent = getCurrentEvent(request)
    isEventAdmin = currentEvent.isEventAdmin(request.user) if currentEvent is not None else False
    isEventOrga = currentEvent.isEventOrga(request.user) if currentEvent is not None else False

    permanentEvents = Event.getPermanent(request.user)
    runningEvents = Event.getRunning(request.user)
    upcomingEvents = Event.getUpcoming(request.user)
    pastEvents = Event.getPast(request.user)

    if request.user.is_authenticated:
        callgroupInvites = CallGroupInvite.objects.filter(accepted=False, extension__event=currentEvent) \
                                                  .filter(Q(extension__owner=request.user) |
                                                          Q(extension__group_admins=request.user)).distinct().count()
    else:
        callgroupInvites = 0

    if epddi_active and request.user.is_authenticated:
        show_epddi = EPDDIClient.objects.filter(owner=request.user, event=currentEvent).exists()
    else:
        show_epddi = False

    return {
        "currentEvent": currentEvent,
        "permanentEvents": permanentEvents,
        "runningEvents": runningEvents,
        "upcomingEvents": upcomingEvents,
        "pastEvents": pastEvents,
        "userIsCurrentEventAdmin": isEventAdmin,
        "userIsCurrentEventOrga": isEventOrga,
        "totalEventCount": len(permanentEvents) + len(upcomingEvents) + len(pastEvents) + len(runningEvents),
        "signedCurrentURL": SimpleLazyObject(lambda: sign_current_url(request)),
        "callgroupInvites": callgroupInvites,
        "showEPDDI": show_epddi,
    }
