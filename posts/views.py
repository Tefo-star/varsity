from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timesince import timesince
from datetime import timedelta
from django.conf import settings
from django.template.loader import render_to_string
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
from django.core.management import call_command
import json
import io
import sys
from .models import (
    Post, Comment, Reaction, CommentReaction, 
    PostShare, PostSave, PostReport, Notification,
    UserActivity
)
from .forms import PostForm, CommentForm

# ==================== HELPER FUNCTIONS ====================
def get_most_popular_reaction(counts):
    """Return the reaction type with the highest count"""
    if not counts or sum(counts.values()) == 0:
        return 'like'
    return max(counts, key=counts.get)

# ==================== HOME FEED WITH INFINITE SCROLL ====================
def home(request):
    # Get all posts with annotations - ALL RENAMED to avoid property conflicts
    posts_list = Post.objects.filter(is_archived=False).select_related(
        'author', 'author__activity'
    ).prefetch_related(
        'comments', 'reactions', 'shares', 'saves'
    ).annotate(
        total_reactions=Count('reactions'),    # Changed from reaction_count
        comments_count=Count('comments'),       # Changed from comment_count
        total_shares=Count('shares'),           # Changed from share_count
        total_saves=Count('saves')              # Changed from save_count
    )
    
    # Pagination for infinite scroll
    paginator = Paginator(posts_list, 10)  # 10 posts per page
    page = request.GET.get('page', 1)
    posts = paginator.get_page(page)
    
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
                new_posts_count = Post.objects.filter(
                    created_at__gt=last_seen,
                    is_archived=False
                ).count()
        
        request.session['last_seen'] = timezone.now().isoformat()
    
    context = {
        'posts': posts,
        'online_count': online_count,
        'new_posts_count': new_posts_count,
    }
    return render(request, 'posts/home.html', context)

# ==================== INFINITE SCROLL API ====================
def load_more_posts(request):
    page = request.GET.get('page', 1)
    posts_list = Post.objects.filter(is_archived=False).select_related(
        'author', 'author__activity'
    ).prefetch_related(
        'comments', 'reactions', 'shares', 'saves'
    ).annotate(
        total_reactions=Count('reactions'),    # Changed from reaction_count
        comments_count=Count('comments'),       # Changed from comment_count
        total_shares=Count('shares'),           # Changed from share_count
        total_saves=Count('saves')              # Changed from save_count
    )
    
    paginator = Paginator(posts_list, 10)
    posts = paginator.get_page(page)
    
    posts_html = render_to_string('posts/_post_cards.html', {
        'posts': posts,
        'user': request.user
    }, request=request)
    
    return JsonResponse({
        'posts_html': posts_html,
        'has_next': posts.has_next(),
        'next_page': posts.next_page_number() if posts.has_next() else None
    })

# ==================== CREATE POST ====================
@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            
            # Update user activity
            activity, _ = UserActivity.objects.get_or_create(user=request.user)
            activity.last_post_time = timezone.now()
            activity.save()
            
            messages.success(request, 'Post created successfully! 🎉')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                post_html = render_to_string('posts/_post_card.html', {
                    'post': post,
                    'user': request.user
                }, request=request)
                return JsonResponse({'success': True, 'post_html': post_html})
            
            return redirect('home')
    else:
        form = PostForm()
    
    return render(request, 'posts/create_post.html', {'form': form})

# ==================== POST DETAIL ====================
def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id, is_archived=False)
    comments = post.comments.filter(parent=None).select_related(
        'author', 'author__activity'
    ).prefetch_related('reactions', 'replies')
    
    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            
            # Create notification for post author (if not self-comment)
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='comment',
                    post=post,
                    comment=comment
                )
            
            messages.success(request, 'Comment added!')
            return redirect('post_detail', post_id=post.id)
    else:
        comment_form = CommentForm()
    
    # Check if user has interacted
    user_reaction = post.get_user_reaction(request.user) if request.user.is_authenticated else None
    user_saved = PostSave.objects.filter(post=post, user=request.user).exists() if request.user.is_authenticated else False
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'user_reaction': user_reaction,
        'user_saved': user_saved,
    }
    return render(request, 'posts/post_detail.html', context)

# ==================== DELETE POST ====================
@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    
    if request.user != post.author and not request.user.is_superuser:
        messages.error(request, "You can only delete your own posts!")
        return redirect('home')
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Your post has been deleted! 🗑️")
        return redirect('home')
    
    return render(request, 'posts/confirm_delete.html', {'post': post})

# ==================== EDIT POST ====================
@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            messages.success(request, "Post updated successfully! ✏️")
            return redirect('post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)
    
    return render(request, 'posts/edit_post.html', {'form': form, 'post': post})

# ==================== PROFILE ====================
@login_required
def profile(request, username=None):
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user
    
    user_activity, created = UserActivity.objects.get_or_create(user=profile_user)
    user_posts = Post.objects.filter(author=profile_user, is_archived=False)
    
    context = {
        'profile_user': profile_user,
        'user_activity': user_activity,
        'user_posts': user_posts,
        'is_own_profile': request.user == profile_user,
    }
    return render(request, 'posts/profile.html', context)

# ==================== NOTIFICATIONS ====================
@login_required
def notifications(request):
    # First, mark unread notifications as read (without slicing)
    Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).update(is_read=True)
    
    # Then get the sliced queryset for display
    notifications_list = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'post', 'comment').order_by('-created_at')[:50]
    
    context = {
        'notifications': notifications_list
    }
    return render(request, 'posts/notifications.html', context)

@login_required
def get_notification_count(request):
    count = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    return JsonResponse({'count': count})

# ==================== AJAX REACTION (NO PAGE RELOAD) ====================
@login_required
@require_POST
def ajax_react_to_post(request, post_id):
    """React to a post without page reload - ONLY ONE REACTION PER USER"""
    try:
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')
        
        # Check if user already has a reaction on this post
        existing_reaction = Reaction.objects.filter(
            post=post,
            user=request.user
        ).first()
        
        if existing_reaction:
            if existing_reaction.reaction_type == reaction_type:
                # Same reaction - remove it (toggle off)
                existing_reaction.delete()
                action = 'removed'
            else:
                # Different reaction - update it (only one allowed)
                existing_reaction.reaction_type = reaction_type
                existing_reaction.save()
                action = 'updated'
        else:
            # No existing reaction - create new
            Reaction.objects.create(
                post=post,
                user=request.user,
                reaction_type=reaction_type
            )
            action = 'added'
            
            # Create notification for post author
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='reaction',
                    post=post
                )
        
        # Get updated counts
        counts = post.get_reaction_counts()
        
        return JsonResponse({
            'success': True,
            'action': action,
            'counts': counts,
            'user_reaction': reaction_type if action != 'removed' else None
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== GET REACTIONS LIST ====================
@login_required
def get_post_reactions(request, post_id):
    """Get list of users who reacted to a post, grouped by reaction type"""
    try:
        post = get_object_or_404(Post, id=post_id)
        
        # Get all reactions for this post with user details
        reactions = Reaction.objects.filter(post=post).select_related(
            'user', 'user__activity'
        ).order_by('-created_at')
        
        # Group reactions by type
        grouped_reactions = {
            'like': [],
            'love': [],
            'haha': [],
            'wow': [],
            'sad': [],
            'angry': []
        }
        
        for reaction in reactions:
            user_data = {
                'id': reaction.user.id,
                'username': reaction.user.username,
                'profile_picture': reaction.user.activity.profile_picture.url if reaction.user.activity and reaction.user.activity.profile_picture else None,
                'university': reaction.user.activity.university if reaction.user.activity and reaction.user.activity.university else None,
                'is_verified': reaction.user.activity.is_verified if reaction.user.activity else False
            }
            grouped_reactions[reaction.reaction_type].append(user_data)
        
        # Get counts for each reaction type
        counts = post.get_reaction_counts()
        
        return JsonResponse({
            'success': True,
            'reactions': grouped_reactions,
            'counts': counts,
            'total': sum(counts.values())
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
        parent_id = data.get('parent_id')
        
        if not content or not content.strip():
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
        
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content.strip(),
            parent_id=parent_id
        )
        
        # Create notification
        if parent_id:
            # Reply to a comment
            parent_comment = Comment.objects.get(id=parent_id)
            if parent_comment.author != request.user:
                Notification.objects.create(
                    recipient=parent_comment.author,
                    sender=request.user,
                    notification_type='reply',
                    post=post,
                    comment=comment
                )
        else:
            # New comment on post
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='comment',
                    post=post,
                    comment=comment
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
            'parent_id': parent_id,
            'comment_count': post.comment_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== AJAX DELETE COMMENT ====================
@login_required
@require_POST
def ajax_delete_comment(request, comment_id):
    """Delete a comment"""
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        
        if comment.author != request.user and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
        
        post_id = comment.post.id
        comment.delete()
        
        return JsonResponse({
            'success': True,
            'post_id': post_id
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
        reaction_type = data.get('reaction_type', 'like')
        
        existing_reaction = CommentReaction.objects.filter(
            comment=comment,
            user=request.user
        ).first()
        
        if existing_reaction:
            existing_reaction.delete()
            action = 'removed'
        else:
            CommentReaction.objects.create(
                comment=comment,
                user=request.user
            )
            action = 'added'
            
            # Create notification for comment author
            if comment.author != request.user:
                Notification.objects.create(
                    recipient=comment.author,
                    sender=request.user,
                    notification_type='reaction',
                    post=comment.post,
                    comment=comment
                )
        
        # Get updated reaction count
        reaction_count = comment.reactions.count()
        
        return JsonResponse({
            'success': True,
            'action': action,
            'reaction_count': reaction_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== AJAX SAVE POST ====================
@login_required
@require_POST
def ajax_save_post(request, post_id):
    """Save/unsave a post"""
    try:
        post = get_object_or_404(Post, id=post_id)
        
        saved, created = PostSave.objects.get_or_create(
            post=post,
            user=request.user
        )
        
        if not created:
            saved.delete()
            is_saved = False
        else:
            is_saved = True
        
        save_count = post.saves.count()
        
        return JsonResponse({
            'success': True,
            'is_saved': is_saved,
            'save_count': save_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== AJAX SHARE POST ====================
@login_required
@require_POST
def ajax_share_post(request, post_id):
    """Share a post"""
    try:
        post = get_object_or_404(Post, id=post_id)
        
        share, created = PostShare.objects.get_or_create(
            post=post,
            user=request.user
        )
        
        if created:
            # Create notification for post author
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='share',
                    post=post
                )
        
        share_count = post.shares.count()
        
        return JsonResponse({
            'success': True,
            'share_count': share_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== AJAX REPORT POST ====================
@login_required
@require_POST
def ajax_report_post(request, post_id):
    """Report a post"""
    try:
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        
        report = PostReport.objects.create(
            post=post,
            user=request.user,
            reason=data.get('reason', 'other'),
            description=data.get('description', '')
        )
        
        return JsonResponse({
            'success': True,
            'report_id': report.id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== SAVED POSTS ====================
@login_required
def saved_posts(request):
    saved_posts = PostSave.objects.filter(
        user=request.user
    ).select_related('post', 'post__author').order_by('-created_at')
    
    context = {
        'saved_posts': saved_posts
    }
    return render(request, 'posts/saved_posts.html', context)

# ==================== SEARCH ====================
def search(request):
    query = request.GET.get('q', '')
    
    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__username__icontains=query)
        ).filter(is_archived=False)[:20]
        
        users = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        )[:10]
    else:
        posts = []
        users = []
    
    context = {
        'query': query,
        'posts': posts,
        'users': users
    }
    return render(request, 'posts/search.html', context)

# ==================== ONLINE USERS API ====================
def online_users_api(request):
    online_count = 0
    for user in User.objects.filter(is_active=True):
        if cache.get(f'online_{user.id}'):
            online_count += 1
    return JsonResponse({'count': online_count})

# ==================== LEGACY: REPLY TO COMMENT (Page reload version) ====================
@login_required
def reply_to_comment(request, comment_id):
    parent_comment = get_object_or_404(Comment, id=comment_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            comment = Comment.objects.create(
                post=parent_comment.post,
                author=request.user,
                parent=parent_comment,
                content=content
            )
            
            # Create notification
            if parent_comment.author != request.user:
                Notification.objects.create(
                    recipient=parent_comment.author,
                    sender=request.user,
                    notification_type='reply',
                    post=parent_comment.post,
                    comment=comment
                )
            
            messages.success(request, 'Reply added!')
    
    return redirect('post_detail', post_id=parent_comment.post.id)

# ==================== LEGACY: REACT TO COMMENT (Page reload version) ====================
@login_required
@require_POST
def react_to_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    
    existing_reaction = CommentReaction.objects.filter(
        comment=comment,
        user=request.user
    ).first()
    
    if existing_reaction:
        existing_reaction.delete()
    else:
        CommentReaction.objects.create(
            comment=comment,
            user=request.user
        )
        
        # Create notification
        if comment.author != request.user:
            Notification.objects.create(
                recipient=comment.author,
                sender=request.user,
                notification_type='reaction',
                post=comment.post,
                comment=comment
            )
    
    return redirect('post_detail', post_id=comment.post.id)

# ==================== TEMPORARY FAKE MIGRATION VIEW ====================
@staff_member_required
def fake_post_migration(request):
    """Temporary view to fake the 0007 migration on Render."""
    from django.core.management import call_command
    from io import StringIO
    
    out = StringIO()
    try:
        # This marks migration 0007 as applied without running the SQL
        call_command('migrate', 'posts', '0007', '--fake', stdout=out)
        
        # Also try to run any other pending migrations normally
        call_command('migrate', 'posts', stdout=out)
        
        return HttpResponse(f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 50px; }}
                    .container {{ max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; }}
                    h1 {{ font-size: 2.5rem; margin-bottom: 20px; }}
                    .success {{ background: rgba(0,255,0,0.2); padding: 20px; border-radius: 10px; }}
                    pre {{ background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; overflow-x: auto; color: #fff; }}
                    a {{ display: inline-block; background: white; color: #667eea; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; margin: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Migration Fake Successful</h1>
                    <div class="success">
                        <h2>Migration 0007 has been faked successfully!</h2>
                    </div>
                    <h3>Output:</h3>
                    <pre>{out.getvalue()}</pre>
                    <a href="/post/1/">Go to Post 1</a>
                    <a href="/admin/">Go to Admin</a>
                </div>
            </body>
        </html>
        """)
    except Exception as e:
        return HttpResponse(f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 50px; }}
                    .container {{ max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; }}
                    h1 {{ font-size: 2.5rem; margin-bottom: 20px; }}
                    .error {{ background: rgba(255,0,0,0.2); padding: 20px; border-radius: 10px; }}
                    pre {{ background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; overflow-x: auto; color: #fff; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>❌ Error</h1>
                    <div class="error">
                        <h2>Error: {str(e)}</h2>
                    </div>
                    <pre>{out.getvalue()}</pre>
                    <a href="/admin/">Go to Admin</a>
                </div>
            </body>
        </html>
        """, status=500)

# ==================== MIGRATION RUNNER ====================
def run_posts_migrations(request):
    """Run migrations for posts app (temporary fix for Render)"""
    if not settings.DEBUG:
        return HttpResponse("Not allowed", status=403)
    
    from django.core.management import call_command
    
    # Capture output
    output = io.StringIO()
    sys.stdout = output
    
    try:
        call_command('migrate', 'posts', verbosity=2, interactive=False)
        result = "✅ Migrations ran successfully!"
    except Exception as e:
        result = f"❌ Error: {str(e)}"
    finally:
        sys.stdout = sys.__stdout__
    
    return HttpResponse(f"""
    <html>
        <head>
            <style>
                body {{ font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 50px; }}
                .container {{ max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; }}
                h1 {{ font-size: 2.5rem; margin-bottom: 20px; }}
                .success {{ background: rgba(0,255,0,0.2); padding: 20px; border-radius: 10px; }}
                .error {{ background: rgba(255,0,0,0.2); padding: 20px; border-radius: 10px; }}
                pre {{ background: rgba(0,0,0,0.3); padding: 15px; border-radius: 10px; overflow-x: auto; }}
                a {{ display: inline-block; background: white; color: #667eea; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; margin: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔄 Posts Migration Runner</h1>
                <div class="{'success' if '✅' in result else 'error'}">
                    <h2>{result}</h2>
                </div>
                <h3>Output:</h3>
                <pre>{output.getvalue()}</pre>
                <a href="/post/1/">Go to Post 1</a>
                <a href="/admin/">Go to Admin</a>
            </div>
        </body>
    </html>
    """)

# ==================== LIST USERS (Admin only) ====================
@login_required
def list_users(request):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=401)
    
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

# ==================== TEST VIEW ====================
def test_view(request):
    return render(request, 'test.html')