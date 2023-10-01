from django.core.asgi import get_asgi_application
from django.urls import path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from guru3.consumers import StatusConsumer


application = ProtocolTypeRouter({
    "http": get_asgi_application(),

    "websocket": AuthMiddlewareStack(
        URLRouter([
            # URLRouter just takes standard Django path() or url() entries.
            path("status/stream/", StatusConsumer.as_asgi()),
        ]),
    ),
})