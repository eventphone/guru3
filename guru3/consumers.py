from django.conf import settings
from django.core.exceptions import PermissionDenied

from channels.generic.websocket import JsonWebsocketConsumer
from channels.exceptions import DenyConnection


clients = {}

def notify_clients(eventid, data):
    try:
        for client in clients.get(eventid, []):
            client.send_json(data)
    except:
        pass


def get_header(headers, header_name):
    for hdr, value in headers:
        if hdr.decode("ascii").lower() == header_name.lower():
            return value.decode("ascii")


class StatusConsumer(JsonWebsocketConsumer):
    def check_user_event(self):
        from core.models import Event

        if self.scope["user"].is_anonymous:
            return None

        eventid = self.scope['session'].get("currentEventId", None)
        if eventid is None:
            return None
        try:
            event = Event.objects.get(pk=eventid)
        except Event.DoesNotExist:
            return None

        if event.isEventAdmin(self.scope["user"]):
            return eventid

        # Unauthorized
        return None

    def check_mgr_api_key(self):
        from core.decorators import event_from_mgr_api_key
        api_key = get_header(self.scope["headers"], settings.AUTH_KEY_HEADER)
        if api_key is None:
            return None
        try:
            return event_from_mgr_api_key(api_key).pk
        except PermissionDenied:
            return None

    def connect(self):
        self.eventid = None
        self.eventid = self.check_user_event()
        if self.eventid is None:
            self.eventid = self.check_mgr_api_key()

        if self.eventid is None:
            raise DenyConnection()

        if self.eventid in clients:
            clients[self.eventid].append(self)
        else:
            clients[self.eventid] = [self]
        self.accept()

    def disconnect(self, code):
        if self.eventid is not None:
            clients[self.eventid].remove(self)
