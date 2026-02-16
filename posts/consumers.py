import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from channels.db import database_sync_to_async

class OnlineConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print(f"🔌 WebSocket connection attempt - User: {self.scope['user']}")
        self.user = self.scope['user']
        
        if self.user.is_authenticated:
            print(f"✅ User authenticated: {self.user.username}")
            self.online_group_name = 'online_users'
            await self.channel_layer.group_add(self.online_group_name, self.channel_name)
            cache.set(f'online_{self.user.id}', timezone.now().timestamp(), timeout=300)
            await self.accept()
            print(f"✅ WebSocket accepted for {self.user.username}")
            await self.update_online_count()
        else:
            print(f"❌ User not authenticated, closing connection")
            await self.close()

    async def disconnect(self, close_code):
        print(f"🔌 WebSocket disconnected with code: {close_code}")
        if hasattr(self, 'user') and self.user.is_authenticated:
            cache.delete(f'online_{self.user.id}')
            await self.channel_layer.group_discard(self.online_group_name, self.channel_name)
            await self.update_online_count()

    async def receive(self, text_data):
        print(f"📨 Received: {text_data}")
        data = json.loads(text_data)
        if data.get('type') == 'ping':
            cache.set(f'online_{self.user.id}', timezone.now().timestamp(), timeout=300)
            await self.send(text_data=json.dumps({'type': 'pong'}))

    async def update_online_count(self):
        online_users = await self.get_online_users()
        count = len(online_users)
        print(f"📊 Online count: {count}")
        
        await self.channel_layer.group_send(self.online_group_name, {
            'type': 'online_count_update',
            'count': count
        })

    async def online_count_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'online_count',
            'count': event['count']
        }))

    @database_sync_to_async
    def get_online_users(self):
        cutoff = timezone.now() - timedelta(minutes=5)
        online_users = []
        for user in User.objects.filter(is_active=True):
            last_seen = cache.get(f'online_{user.id}')
            if last_seen:
                online_users.append(user)
        return online_users

# ... rest of your consumers (LikeConsumer, NotificationConsumer)