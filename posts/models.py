from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField

# Then your Post class
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

# Don't forget your other models (Comment, Reaction, UserActivity) below!