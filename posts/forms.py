from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['post_type', 'title', 'content', 'image', 'video_url']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'What\'s on your mind?', 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'placeholder': 'Post title', 'class': 'form-control'}),
            'post_type': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'video_url': forms.URLInput(attrs={'placeholder': 'YouTube/Vimeo URL', 'class': 'form-control'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Add a comment...', 'class': 'form-control'}),
        }