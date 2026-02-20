import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Notification, Message

class ChatConsumer(AsyncWebsocketConsumer):
    """Handles private chat between users"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.room_name = f"chat_{self.user.id}"
        self.room_group_name = f"chat_{self.user.id}"
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            await self.handle_message(data)
        elif message_type == 'typing':
            await self.handle_typing(data)
        elif message_type == 'read':
            await self.handle_read(data)
    
    async def handle_message(self, data):
        recipient_id = data.get('recipient_id')
        content = data.get('content')
        
        # Save message to database
        message = await self.save_message(recipient_id, content)
        
        # Send to recipient's room
        await self.channel_layer.group_send(
            f"chat_{recipient_id}",
            {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'sender': self.user.username,
                    'sender_id': self.user.id,
                    'content': content,
                    'timestamp': str(timezone.now()),
                }
            }
        )
        
        # Also send back to sender for confirmation
        await self.send(text_data=json.dumps({
            'type': 'sent',
            'message': {
                'id': message.id,
                'content': content,
                'timestamp': str(timezone.now()),
            }
        }))
    
    async def handle_typing(self, data):
        recipient_id = data.get('recipient_id')
        is_typing = data.get('is_typing', True)
        
        await self.channel_layer.group_send(
            f"chat_{recipient_id}",
            {
                'type': 'typing_indicator',
                'user_id': self.user.id,
                'username': self.user.username,
                'is_typing': is_typing
            }
        )
    
    async def handle_read(self, data):
        message_ids = data.get('message_ids', [])
        await self.mark_messages_read(message_ids)
        
        await self.channel_layer.group_send(
            f"chat_{data.get('recipient_id')}",
            {
                'type': 'read_receipt',
                'message_ids': message_ids,
                'read_by': self.user.id
            }
        )
    
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))
    
    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read',
            'message_ids': event['message_ids'],
            'read_by': event['read_by']
        }))
    
    @database_sync_to_async
    def save_message(self, recipient_id, content):
        recipient = User.objects.get(id=recipient_id)
        return Message.objects.create(
            sender=self.user,
            recipient=recipient,
            content=content
        )
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        Message.objects.filter(id__in=message_ids, recipient=self.user).update(is_read=True)

class NotificationConsumer(AsyncWebsocketConsumer):
    """Handles real-time notifications"""
    
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        self.group_name = f"notifications_{self.user.id}"
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        
        # Send unread count on connect
        unread_count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': unread_count
        }))
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'mark_read':
            await self.mark_all_read()
            await self.send(text_data=json.dumps({
                'type': 'unread_count',
                'count': 0
            }))
    
    async def send_notification(self, event):
        """Send notification to client"""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
        
        # Also send updated count
        count = await self.get_unread_count()
        await self.send(text_data=json.dumps({
            'type': 'unread_count',
            'count': count
        }))
    
    @database_sync_to_async
    def get_unread_count(self):
        return Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).count()
    
    @database_sync_to_async
    def mark_all_read(self):
        Notification.objects.filter(
            recipient=self.user,
            is_read=False
        ).update(is_read=True)