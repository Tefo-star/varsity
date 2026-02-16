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

from posts.consumers import OnlineConsumer, NotificationConsumer, LikeConsumer

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter([
                path('ws/online/', OnlineConsumer.as_asgi()),
                path('ws/notifications/', NotificationConsumer.as_asgi()),
                path('ws/like/<int:post_id>/', LikeConsumer.as_asgi()),
            ])
        )
    )
})