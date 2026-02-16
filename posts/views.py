from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from .models import Post, Comment, Reaction, UserActivity
from .forms import PostForm, CommentForm
from django.contrib.auth.models import User

def get_online_users_count():
    cutoff = timezone.now() - timedelta(minutes=5)
    online_users = []
    for user in User.objects.filter(is_active=True):
        if cache.get(f'online_{user.id}'):
            online_users.append(user)
    return len(online_users)

def home(request):
    posts = Post.objects.all()
    online_count = get_online_users_count()
    new_posts = 0
    
    if request.user.is_authenticated:
        activity, created = UserActivity.objects.get_or_create(user=request.user)
        new_posts = activity.get_new_posts_count()
        activity.last_seen = timezone.now()
        activity.save()
    
    # Debug prints
    print(f"Home view - Posts found: {posts.count()}")
    print(f"Home view - User: {request.user}")
    
    return render(request, 'posts/home.html', {
        'posts': posts,
        'online_count': online_count,
        'new_posts': new_posts
    })

def test_view(request):
    posts = Post.objects.all()
    return render(request, 'test.html', {
        'posts': posts, 
        'user': request.user
    })

@login_required
def profile(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    posts = Post.objects.filter(author=user).order_by('-created_at')
    online_count = get_online_users_count()
    
    return render(request, 'posts/profile.html', {
        'profile_user': user,
        'posts': posts,
        'online_count': online_count,
        'is_own_profile': user == request.user
    })

@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            
            activity, created = UserActivity.objects.get_or_create(user=request.user)
            activity.last_post_time = timezone.now()
            activity.save()
            
            messages.success(request, 'Post created successfully!')
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    post.view_count += 1
    post.save()
    
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
    
    reaction_counts = post.get_reaction_counts()
    
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'reaction_counts': reaction_counts
    })

@login_required
def react_to_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        reaction_type = request.POST.get('reaction_type')
        
        existing_reaction = Reaction.objects.filter(
            post=post, 
            user=request.user
        ).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                existing_reaction.delete()
                messages.info(request, f'Reaction removed')
            else:
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                messages.success(request, f'Reacted with {reaction_type}')
        else:
            Reaction.objects.create(
                post=post,
                user=request.user,
                reaction_type=reaction_type
            )
            messages.success(request, f'Reacted with {reaction_type}')
    
    return redirect('post_detail', post_id=post.id)

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return redirect('profile')
    return render(request, 'posts/confirm_delete.html', {'post': post})