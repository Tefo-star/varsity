from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/online/$', consumers.OnlineConsumer.as_asgi()),
    re_path(r'ws/notifications/$', consumers.NotificationConsumer.as_asgi()),
    re_path(r'ws/like/(?P<post_id>\d+)/$', consumers.LikeConsumer.as_asgi()),
]