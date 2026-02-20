from rest_framework import serializers, viewsets, generics, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib.auth import authenticate
from django.db.models import Q, Count
from .models import (
    Post, Comment, Reaction, User,
    Notification, UserActivity, Follow, Message
)

# ==================== SERIALIZERS ====================

class UserSerializer(serializers.ModelSerializer):
    """User serializer with profile info"""
    university = serializers.CharField(source='activity.university', read_only=True)
    profile_picture = serializers.ImageField(source='activity.profile_picture', read_only=True)
    is_verified = serializers.BooleanField(source='activity.is_verified', read_only=True)
    follower_count = serializers.IntegerField(source='activity.follower_count', read_only=True)
    following_count = serializers.IntegerField(source='activity.following_count', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'university', 'profile_picture', 'is_verified',
            'follower_count', 'following_count', 'last_login'
        ]

class ReactionSerializer(serializers.ModelSerializer):
    """Reaction serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Reaction
        fields = ['id', 'user', 'reaction_type', 'created_at']

class CommentSerializer(serializers.ModelSerializer):
    """Comment serializer with nested replies"""
    author = UserSerializer(read_only=True)
    reply_count = serializers.IntegerField(source='replies.count', read_only=True)
    reaction_count = serializers.IntegerField(source='reactions.count', read_only=True)
    user_reaction = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'post', 'author', 'content', 'parent',
            'created_at', 'updated_at', 'reply_count',
            'reaction_count', 'user_reaction'
        ]
    
    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            reaction = obj.reactions.filter(user=request.user).first()
            return reaction.reaction_type if reaction else None
        return None

class PostSerializer(serializers.ModelSerializer):
    """Post serializer with all related data"""
    author = UserSerializer(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    reaction_counts = serializers.SerializerMethodField()
    user_reaction = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    latest_comments = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = [
            'id', 'author', 'post_type', 'title', 'content',
            'image', 'video', 'created_at', 'updated_at',
            'comment_count', 'reaction_counts', 'user_reaction',
            'is_saved', 'is_pinned', 'is_archived', 'latest_comments'
        ]
    
    def get_reaction_counts(self, obj):
        return obj.get_reaction_counts()
    
    def get_user_reaction(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.get_user_reaction(request.user)
        return None
    
    def get_is_saved(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.saves.filter(user=request.user).exists()
        return False
    
    def get_latest_comments(self, obj):
        comments = obj.comments.filter(parent=None)[:3]
        return CommentSerializer(comments, many=True, context=self.context).data

class NotificationSerializer(serializers.ModelSerializer):
    """Notification serializer"""
    sender = UserSerializer(read_only=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'sender', 'notification_type', 'post', 'comment', 'is_read', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    """Message serializer for private chat"""
    sender = UserSerializer(read_only=True)
    recipient = UserSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'content', 'created_at', 'is_read']

# ==================== VIEWSETS ====================

class PostViewSet(viewsets.ModelViewSet):
    """API endpoint for posts"""
    queryset = Post.objects.filter(is_archived=False).order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """React to a post"""
        post = self.get_object()
        reaction_type = request.data.get('reaction_type')
        
        if not reaction_type:
            return Response({'error': 'reaction_type required'}, status=400)
        
        existing = Reaction.objects.filter(post=post, user=request.user).first()
        
        if existing:
            if existing.reaction_type == reaction_type:
                existing.delete()
                return Response({'status': 'removed'})
            else:
                existing.reaction_type = reaction_type
                existing.save()
                return Response({'status': 'updated', 'reaction_type': reaction_type})
        else:
            Reaction.objects.create(
                post=post,
                user=request.user,
                reaction_type=reaction_type
            )
            return Response({'status': 'added', 'reaction_type': reaction_type})
    
    @action(detail=True, methods=['post'])
    def save(self, request, pk=None):
        """Save/unsave a post"""
        post = self.get_object()
        saved, created = post.saves.get_or_create(user=request.user)
        
        if not created:
            saved.delete()
            return Response({'saved': False})
        return Response({'saved': True})
    
    @action(detail=True, methods=['get'])
    def reactions(self, request, pk=None):
        """Get list of users who reacted"""
        post = self.get_object()
        reactions = post.reactions.select_related('user', 'user__activity')
        
        grouped = {'like': [], 'love': [], 'haha': [], 'wow': [], 'sad': [], 'angry': []}
        
        for r in reactions:
            user_data = {
                'id': r.user.id,
                'username': r.user.username,
                'profile_picture': r.user.activity.profile_picture.url if r.user.activity and r.user.activity.profile_picture else None,
                'university': r.user.activity.university if r.user.activity else None,
            }
            grouped[r.reaction_type].append(user_data)
        
        return Response(grouped)

class CommentViewSet(viewsets.ModelViewSet):
    """API endpoint for comments"""
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        queryset = Comment.objects.all()
        post_id = self.request.query_params.get('post', None)
        parent_id = self.request.query_params.get('parent', None)
        
        if post_id:
            queryset = queryset.filter(post_id=post_id)
        if parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        else:
            queryset = queryset.filter(parent=None)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    @action(detail=True, methods=['post'])
    def react(self, request, pk=None):
        """Like/unlike a comment"""
        comment = self.get_object()
        existing = comment.reactions.filter(user=request.user).first()
        
        if existing:
            existing.delete()
            return Response({'liked': False})
        else:
            comment.reactions.create(user=request.user)
            return Response({'liked': True})

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for users"""
    queryset = User.objects.filter(is_active=True)
    serializer_class = UserSerializer
    
    @action(detail=True, methods=['post'])
    def follow(self, request, pk=None):
        """Follow/unfollow a user"""
        target = self.get_object()
        if target == request.user:
            return Response({'error': 'Cannot follow yourself'}, status=400)
        
        follow, created = target.followers.get_or_create(follower=request.user)
        
        if not created:
            follow.delete()
            return Response({'following': False})
        return Response({'following': True})
    
    @action(detail=True, methods=['get'])
    def posts(self, request, pk=None):
        """Get posts by user"""
        user = self.get_object()
        posts = Post.objects.filter(author=user, is_archived=False).order_by('-created_at')
        page = self.paginate_queryset(posts)
        if page is not None:
            serializer = PostSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = PostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    """API endpoint for private messages"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        other_user_id = self.request.query_params.get('user')
        
        if other_user_id:
            return Message.objects.filter(
                (Q(sender=user) & Q(recipient_id=other_user_id)) |
                (Q(sender_id=other_user_id) & Q(recipient=user))
            ).order_by('-created_at')
        return Message.objects.filter(Q(sender=user) | Q(recipient=user)).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(sender=self.request.user)

# ==================== AUTHENTICATION ====================

class LoginView(ObtainAuthToken):
    """Custom login view that returns user data with token"""
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user, context={'request': request}).data
        })

class RegisterView(generics.CreateAPIView):
    """User registration"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not all([username, email, password]):
            return Response({'error': 'All fields required'}, status=400)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username taken'}, status=400)
        
        user = User.objects.create_user(username, email, password)
        UserActivity.objects.create(user=user)
        token, _ = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user, context={'request': request}).data
        }, status=201)