from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['post_type', 'title', 'content', 'image', 'video_url']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'What\'s on your mind?',
                'maxlength': 5000
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter title',
                'maxlength': 200
            }),
            'video_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'YouTube or video URL'
            }),
            'post_type': forms.Select(attrs={
                'class': 'form-control'
            }),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Write a comment...',
                'maxlength': 1000
            }),
        }