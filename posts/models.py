from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField

class Post(models.Model):
    POST_TYPES = [
        ('MEME', 'Meme'),
        ('VIDEO', ' Video'),
        ('PIC', 'Picture'),
        ('TEXT', 'Text Post'),
        ('NEWS', 'News/Notice'),
        ('POLL', 'Poll'),
        ('EVENT', 'Event'),
    ]
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    post_type = models.CharField(max_length=10, choices=POST_TYPES, default='TEXT')
    title = models.CharField(max_length=200)
    content = models.TextField(blank=True)
    image = CloudinaryField('image', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    # WhatsApp-style reply fields
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    reply_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-is_pinned', '-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['author', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} by {self.author.username}"
    
    def get_reaction_counts(self):
        return {
            'like': self.reactions.filter(reaction_type='like').count(),
            'love': self.reactions.filter(reaction_type='love').count(),
            'haha': self.reactions.filter(reaction_type='haha').count(),
            'wow': self.reactions.filter(reaction_type='wow').count(),
            'sad': self.reactions.filter(reaction_type='sad').count(),
            'angry': self.reactions.filter(reaction_type='angry').count(),
        }
    
    def get_user_reaction(self, user):
        if user.is_authenticated:
            reaction = self.reactions.filter(user=user).first()
            return reaction.reaction_type if reaction else None
        return None
    
    @property
    def comment_count(self):
        return self.comments.count()
    
    @property
    def save_count(self):
        return self.saves.count()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()  # No more parent field - no nested replies
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_edited = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'created_at']),
        ]
    
    def __str__(self):
        return f"Comment by {self.author.username}"
    
    def get_reaction_counts(self):
        return {'like': self.reactions.filter(reaction_type='like').count()}
    
    def get_user_reaction(self, user):
        if user.is_authenticated:
            reaction = self.reactions.filter(user=user).first()
            return reaction.reaction_type if reaction else None
        return None

class CommentReaction(models.Model):
    REACTION_TYPES = [('like', '👍 Like')]
    
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES, default='like')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['comment', 'user']
        indexes = [models.Index(fields=['comment', 'user'])]
    
    def __str__(self):
        return f"{self.user.username} liked comment"

class Reaction(models.Model):
    REACTION_TYPES = [
        ('like', '👍 Like'),
        ('love', '❤️ Love'),
        ('haha', '😂 Haha'),
        ('wow', '😮 Wow'),
        ('sad', '😢 Sad'),
        ('angry', '😡 Angry'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['post', 'user']
        indexes = [
            models.Index(fields=['post', 'user']),
            models.Index(fields=['post', 'reaction_type']),
        ]
    
    def __str__(self):
        return f"{self.user.username} reacted {self.reaction_type}"

class PostShare(models.Model):
    # This model can be removed entirely if you want, but keeping for now
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['post', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} shared {self.post.title}"

class PostSave(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='saves')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['post', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} saved {self.post.title}"

class PostReport(models.Model):
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('harassment', 'Harassment'),
        ('hate_speech', 'Hate Speech'),
        ('violence', 'Violence'),
        ('nudity', 'Nudity'),
        ('copyright', 'Copyright Infringement'),
        ('other', 'Other'),
    ]
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='reports')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    is_resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report on {self.post.title}"

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('reaction', 'Reaction'),
        ('comment', 'Comment'),
        ('reply', 'Reply'),
        ('mention', 'Mention'),
        # 'share' removed
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['recipient', 'is_read']),
        ]
    
    def __str__(self):
        return f"{self.sender.username} {self.notification_type}"

class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['follower', 'following']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"

class UserActivity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='activity')
    last_seen = models.DateTimeField(default=timezone.now)
    last_post_time = models.DateTimeField(null=True, blank=True)
    university = models.CharField(max_length=50, blank=True, null=True)
    bio = models.TextField(blank=True, max_length=500)
    profile_picture = CloudinaryField('image', blank=True, null=True)
    cover_photo = CloudinaryField('image', blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    follower_count = models.IntegerField(default=0)
    following_count = models.IntegerField(default=0)
    
    def update_last_seen(self):
        self.last_seen = timezone.now()
        self.save()
    
    def get_new_posts_count(self):
        return Post.objects.filter(created_at__gt=self.last_seen).count()