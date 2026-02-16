"""
ASGI config for varsity project.
"""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import posts.routing  # Import routing instead of consumers directly

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'varsity.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                posts.routing.websocket_urlpatterns  # Use routing file
            )
        )
    ),
})