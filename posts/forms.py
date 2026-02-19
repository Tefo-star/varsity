from django import forms
from .models import Post, Comment

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['post_type', 'title', 'content', 'image', 'video']  # Changed from video_url to video
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'What\'s on your mind?',
                'maxlength': 5000
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Title (optional)',
                'maxlength': 200
            }),
            'video': forms.FileInput(attrs={  # Changed from URLInput to FileInput
                'class': 'form-control',
                'accept': 'video/*'
            }),
            'post_type': forms.Select(attrs={
                'class': 'form-control'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = False
        self.fields['video'].required = False
        self.fields['image'].required = False