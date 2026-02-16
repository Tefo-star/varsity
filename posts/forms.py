from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['post_type', 'title', 'content', 'image', 'video_url']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control', 'placeholder': 'What\'s on your mind?'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter title'}),
            'video_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'YouTube or video URL'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Write a comment...'}),
        }