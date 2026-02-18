from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField

class Post(models.Model):
    POST_TYPES = [
        ('MEME', 'Meme'),
        ('VIDEO', 'Video'),
        ('PIC', 'Picture'),
        ('TEXT', 'Text Post'),
        ('NEWS', 'News/Notice'),
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
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.author.username}"
    
    def get_reaction_counts(self):
        reactions = {
            'like': self.reactions.filter(reaction_type='like').count(),
            'love': self.reactions.filter(reaction_type='love').count(),
            'haha': self.reactions.filter(reaction_type='haha').count(),
            'wow': self.reactions.filter(reaction_type='wow').count(),
            'sad': self.reactions.filter(reaction_type='sad').count(),
            'angry': self.reactions.filter(reaction_type='angry').count(),
        }
        return reactions

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.author.username}"
    
    @property
    def is_reply(self):
        return self.parent is not None
    
    @property
    def reply_count(self):
        return self.replies.count()

class CommentReaction(models.Model):
    REACTION_TYPES = [
        ('like', '👍 Like'),
        ('love', '❤️ Love'),
        ('haha', '😂 Haha'),
        ('wow', '😮 Wow'),
        ('sad', '😢 Sad'),
        ('angry', '😡 Angry'),
    ]
    
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reaction_type = models.CharField(max_length=10, choices=REACTION_TYPES)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['comment', 'user']

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

class UserActivity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='activity')
    last_seen = models.DateTimeField(default=timezone.now)
    last_post_time = models.DateTimeField(null=True, blank=True)
    university = models.CharField(max_length=50, blank=True, null=True)
    
    def update_last_seen(self):
        self.last_seen = timezone.now()
        self.save()
    
    def get_new_posts_count(self):
        return Post.objects.filter(created_at__gt=self.last_seen).count()