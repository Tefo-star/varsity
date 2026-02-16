"""
ASGI config for varsity project.
"""
import os
# Set the settings module FIRST, before any other imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'varsity.settings')

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
import posts.routing

# Initialize Django ASGI application early to ensure the AppRegistry is populated
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                posts.routing.websocket_urlpatterns
            )
        )
    ),
})