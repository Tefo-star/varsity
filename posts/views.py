from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from datetime import timedelta
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
import json
from .models import Post, Comment, Reaction, CommentReaction
from .forms import PostForm, CommentForm

def home(request):
    posts = Post.objects.all()
    
    # Get online users count
    online_count = 0
    for user in User.objects.filter(is_active=True):
        if cache.get(f'online_{user.id}'):
            online_count += 1
    
    # Check for new posts since last visit
    new_posts_count = 0
    if request.user.is_authenticated:
        last_seen_str = request.session.get('last_seen')
        
        if last_seen_str:
            last_seen = parse_datetime(last_seen_str)
            if last_seen:
                new_posts_count = Post.objects.filter(created_at__gt=last_seen).count()
        
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
    comments = post.comments.filter(parent=None)  # Only top-level comments
    
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
    
    existing_reaction = Reaction.objects.filter(
        post=post,
        user=request.user
    ).first()
    
    if existing_reaction:
        if existing_reaction.reaction_type == reaction_type:
            existing_reaction.delete()
            messages.success(request, f'Reaction removed')
        else:
            existing_reaction.reaction_type = reaction_type
            existing_reaction.save()
            messages.success(request, f'Reaction updated to {reaction_type}')
    else:
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

def online_users_api(request):
    online_count = 0
    for user in User.objects.filter(is_active=True):
        if cache.get(f'online_{user.id}'):
            online_count += 1
    return JsonResponse({'count': online_count})

def test_view(request):
    return render(request, 'test.html')

# ==================== COMMENT REPLY (Regular) ====================
@login_required
def reply_to_comment(request, comment_id):
    parent_comment = get_object_or_404(Comment, id=comment_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Comment.objects.create(
                post=parent_comment.post,
                author=request.user,
                parent=parent_comment,
                content=content
            )
            messages.success(request, 'Reply added!')
    
    return redirect('post_detail', post_id=parent_comment.post.id)

# ==================== REACT TO COMMENT (Regular) ====================
@login_required
@require_POST
def react_to_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    reaction_type = request.POST.get('reaction_type')
    
    existing_reaction = CommentReaction.objects.filter(
        comment=comment,
        user=request.user
    ).first()
    
    if existing_reaction:
        if existing_reaction.reaction_type == reaction_type:
            existing_reaction.delete()
        else:
            existing_reaction.reaction_type = reaction_type
            existing_reaction.save()
    else:
        CommentReaction.objects.create(
            comment=comment,
            user=request.user,
            reaction_type=reaction_type
        )
    
    return redirect('post_detail', post_id=comment.post.id)

# ==================== AJAX REACTION (NO PAGE RELOAD) ====================
@login_required
@require_POST
def ajax_react_to_post(request, post_id):
    """React to a post without page reload"""
    try:
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')
        
        existing_reaction = Reaction.objects.filter(
            post=post,
            user=request.user
        ).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                existing_reaction.delete()
                action = 'removed'
            else:
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                action = 'updated'
        else:
            Reaction.objects.create(
                post=post,
                user=request.user,
                reaction_type=reaction_type
            )
            action = 'added'
        
        # Get updated counts
        counts = post.get_reaction_counts()
        
        return JsonResponse({
            'success': True,
            'action': action,
            'counts': counts
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== AJAX ADD COMMENT ====================
@login_required
@require_POST
def ajax_add_comment(request, post_id):
    """Add comment without page reload"""
    try:
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        content = data.get('content')
        parent_id = data.get('parent_id')  # For replies
        
        if not content:
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
        
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content,
            parent_id=parent_id
        )
        
        # Return the new comment HTML
        comment_html = render_to_string('posts/_comment.html', {
            'comment': comment,
            'user': request.user
        }, request=request)
        
        return JsonResponse({
            'success': True,
            'comment_html': comment_html,
            'comment_id': comment.id,
            'parent_id': parent_id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== AJAX REACT TO COMMENT ====================
@login_required
@require_POST
def ajax_react_to_comment(request, comment_id):
    """React to a comment without page reload"""
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')
        
        existing_reaction = CommentReaction.objects.filter(
            comment=comment,
            user=request.user
        ).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                existing_reaction.delete()
            else:
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
        else:
            CommentReaction.objects.create(
                comment=comment,
                user=request.user,
                reaction_type=reaction_type
            )
        
        # Get updated reaction count
        reaction_count = comment.commentreaction_set.count()
        
        return JsonResponse({
            'success': True,
            'reaction_count': reaction_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== LIST USERS (Optional - Keep for debugging) ====================
def list_users(request):
    users = User.objects.all().values('id', 'username', 'email', 'is_superuser', 'is_staff')
    user_list = list(users)
    
    html = """
    <html>
        <head>
            <style>
                body { font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 50px; }
                .container { max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 20px; }
                h1 { text-align: center; margin-bottom: 30px; }
                table { width: 100%; border-collapse: collapse; background: rgba(255,255,255,0.2); border-radius: 10px; overflow: hidden; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.1); }
                th { background: rgba(0,0,0,0.3); font-weight: 600; }
                tr:hover { background: rgba(255,255,255,0.1); }
                .badge { background: #ffd700; color: #333; padding: 3px 8px; border-radius: 20px; font-size: 0.8rem; }
                .admin-badge { background: #ff416c; color: white; padding: 3px 8px; border-radius: 20px; font-size: 0.8rem; }
                a { display: inline-block; margin-top: 20px; color: white; text-decoration: none; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>👥 Registered Users</h1>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Type</th>
                    </tr>
    """
    
    for user in user_list:
        user_type = ""
        if user['is_superuser']:
            user_type = '<span class="admin-badge">SUPERUSER</span>'
        elif user['is_staff']:
            user_type = '<span class="admin-badge">STAFF</span>'
        else:
            user_type = '<span class="badge">USER</span>'
            
        html += f"""
                    <tr>
                        <td>{user['id']}</td>
                        <td><strong>{user['username']}</strong></td>
                        <td>{user['email']}</td>
                        <td>{user_type}</td>
                    </tr>
        """
    
    html += """
                </table>
                <div style="text-align: center; margin-top: 30px;">
                    <a href="/admin/">Go to Admin Login →</a>
                </div>
            </div>
        </body>
    </html>
    """
    
    return HttpResponse(html)