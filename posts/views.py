from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
from .models import Post, Comment, Reaction
from .forms import PostForm, CommentForm

def home(request):
    posts = Post.objects.all()
    
    # Get online users count
    online_count = 0
    for user in User.objects.filter(is_active=True):
        if cache.get(f'online_{user.id}'):
            online_count += 1
    
    # Check for new posts since last visit - FIXED JSON SERIALIZATION
    new_posts_count = 0
    if request.user.is_authenticated:
        last_seen_str = request.session.get('last_seen')
        
        if last_seen_str:
            # Convert string back to datetime for comparison
            last_seen = parse_datetime(last_seen_str)
            if last_seen:
                new_posts_count = Post.objects.filter(created_at__gt=last_seen).count()
        
        # Store as ISO string (JSON serializable) NOT datetime object
        request.session['last_seen'] = timezone.now().isoformat()
    
    context = {
        'posts': posts,
        'online_count': online_count,
        'new_posts_count': new_posts_count,
    }
    return render(request, 'posts/home.html', context)

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Post created successfully! 🎉')
            return redirect('home')
    else:
        form = PostForm()
    
    return render(request, 'posts/create_post.html', {'form': form})

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = post.comments.all()
    
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added!')
            return redirect('post_detail', post_id=post.id)
    else:
        comment_form = CommentForm()
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
    }
    return render(request, 'posts/post_detail.html', context)

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    # Check if user is the author
    if request.user != post.author:
        messages.error(request, "You can only delete your own posts!")
        return redirect('home')
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Your post has been deleted! 🗑️")
        return redirect('home')
    
    return render(request, 'posts/confirm_delete.html', {'post': post})

@login_required
@require_POST
def react_to_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    reaction_type = request.POST.get('reaction_type')
    
    # Check if user already reacted
    existing_reaction = Reaction.objects.filter(
        post=post,
        user=request.user
    ).first()
    
    if existing_reaction:
        if existing_reaction.reaction_type == reaction_type:
            # Remove reaction if clicking same type
            existing_reaction.delete()
            messages.success(request, f'Reaction removed')
        else:
            # Update reaction type
            existing_reaction.reaction_type = reaction_type
            existing_reaction.save()
            messages.success(request, f'Reaction updated to {reaction_type}')
    else:
        # Create new reaction
        Reaction.objects.create(
            post=post,
            user=request.user,
            reaction_type=reaction_type
        )
        messages.success(request, f'Reacted with {reaction_type}')
    
    return redirect('post_detail', post_id=post.id)

@login_required
def profile(request):
    user = request.user
    user_posts = Post.objects.filter(author=user)
    user_activity = getattr(user, 'activity', None)
    
    context = {
        'user': user,
        'user_posts': user_posts,
        'user_activity': user_activity,
    }
    return render(request, 'posts/profile.html', context)

# API endpoint for online users count (fallback if WebSocket fails)
def online_users_api(request):
    online_count = 0
    for user in User.objects.filter(is_active=True):
        if cache.get(f'online_{user.id}'):
            online_count += 1
    return JsonResponse({'count': online_count})

def test_view(request):
    return render(request, 'test.html')