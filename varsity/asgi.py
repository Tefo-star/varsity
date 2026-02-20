"""
ASGI config for varsity project.
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'varsity.settings')

# Import WebSocket consumers
from posts.consumers import ChatConsumer, NotificationConsumer

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path("ws/chat/<str:room_name>/", ChatConsumer.as_asgi()),
                path("ws/notifications/", NotificationConsumer.as_asgi()),
            ])
        )
    ),
})