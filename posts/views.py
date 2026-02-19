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
    PostSave, PostReport, Notification,
    UserActivity
)
from .forms import PostForm, CommentForm

# ==================== HELPER FUNCTIONS ====================
def get_most_popular_reaction(counts):
    if not counts or sum(counts.values()) == 0:
        return 'like'
    return max(counts, key=counts.get)

# ==================== HOME FEED ====================
def home(request):
    posts_list = Post.objects.filter(is_archived=False).select_related(
        'author', 'author__activity', 'parent__author', 'parent__author__activity'
    ).prefetch_related(
        'comments', 'reactions', 'saves', 'replies'
    ).annotate(
        total_reactions=Count('reactions'),
        comments_count=Count('comments'),
        total_saves=Count('saves')
    ).order_by('-created_at')

    paginator = Paginator(posts_list, 10)
    page = request.GET.get('page', 1)
    posts = paginator.get_page(page)

    online_count = 0
    for user in User.objects.filter(is_active=True):
        if cache.get(f'online_{user.id}'):
            online_count += 1

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

# ==================== INFINITE SCROLL ====================
def load_more_posts(request):
    page = request.GET.get('page', 1)
    posts_list = Post.objects.filter(is_archived=False).select_related(
        'author', 'author__activity', 'parent__author', 'parent__author__activity'
    ).prefetch_related(
        'comments', 'reactions', 'saves', 'replies'
    ).annotate(
        total_reactions=Count('reactions'),
        comments_count=Count('comments'),
        total_saves=Count('saves')
    ).order_by('-created_at')

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
            post.reply_count = 0

            if not post.title and post.content:
                post.title = post.content[:50] + "..." if len(post.content) > 50 else post.content
            elif not post.title:
                post.title = "Untitled Post"

            post.save()

            activity, _ = UserActivity.objects.get_or_create(user=request.user)
            activity.last_post_time = timezone.now()
            activity.save()

            messages.success(request, 'Post created successfully! 🎉')

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                post_html = render_to_string('posts/_post_card.html', {
                    'post': post,
                    'user': request.user,
                    'user_reaction': None,
                    'user_saved': False
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
    ).prefetch_related('reactions')

    if request.method == 'POST' and request.user.is_authenticated:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()

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
        if post.parent:
            parent = post.parent
            parent.reply_count = max(0, parent.reply_count - 1)
            parent.save(update_fields=['reply_count'])

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

    user_activity, _ = UserActivity.objects.get_or_create(user=profile_user)
    user_posts = Post.objects.filter(author=profile_user, is_archived=False, parent=None)

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
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    notifications_list = Notification.objects.filter(
        recipient=request.user
    ).select_related('sender', 'post', 'comment').order_by('-created_at')[:50]

    context = {'notifications': notifications_list}
    return render(request, 'posts/notifications.html', context)

@login_required
def get_notification_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})

# ==================== AJAX REACTION ====================
@login_required
@require_POST
def ajax_react_to_post(request, post_id):
    try:
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        reaction_type = data.get('reaction_type')

        existing = Reaction.objects.filter(post=post, user=request.user).first()

        if existing:
            if existing.reaction_type == reaction_type:
                existing.delete()
            else:
                existing.reaction_type = reaction_type
                existing.save()
        else:
            Reaction.objects.create(post=post, user=request.user, reaction_type=reaction_type)
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='reaction',
                    post=post
                )

        return JsonResponse({
            'success': True,
            'counts': post.get_reaction_counts(),
            'user_reaction': reaction_type if not existing or existing.reaction_type != reaction_type else None
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== GET REACTIONS LIST ====================
@login_required
def get_post_reactions(request, post_id):
    try:
        post = get_object_or_404(Post, id=post_id)
        reactions = Reaction.objects.filter(post=post).select_related('user', 'user__activity')

        grouped = {'like': [], 'love': [], 'haha': [], 'wow': [], 'sad': [], 'angry': []}
        for r in reactions:
            user_data = {
                'id': r.user.id,
                'username': r.user.username,
                'profile_picture': r.user.activity.profile_picture.url if r.user.activity and r.user.activity.profile_picture else None,
                'university': r.user.activity.university if r.user.activity and r.user.activity.university else None,
                'is_verified': r.user.activity.is_verified if r.user.activity else False
            }
            grouped[r.reaction_type].append(user_data)

        return JsonResponse({
            'success': True,
            'reactions': grouped,
            'counts': post.get_reaction_counts(),
            'total': sum(post.get_reaction_counts().values())
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== AJAX ADD COMMENT (2 LEVELS ONLY) ====================
@login_required
@require_POST
def ajax_add_comment(request, post_id):
    try:
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        content = data.get('content')
        parent_id = data.get('parent_id')
        
        if not content or not content.strip():
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)
        
        # 2 LEVELS ONLY: Comment → Reply (NO deeper nesting)
        if parent_id:
            parent_comment = Comment.objects.get(id=parent_id)
            # If parent already has a parent, that would be level 3 - NOT ALLOWED
            if parent_comment.parent:
                return JsonResponse({
                    'success': False, 
                    'error': 'Cannot reply to a reply - 2 levels only (Comment → Reply)'
                }, status=400)
        
        comment = Comment.objects.create(
            post=post,
            author=request.user,
            content=content.strip(),
            parent_id=parent_id
        )
        
        # Create notification
        if parent_id:
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
            if post.author != request.user:
                Notification.objects.create(
                    recipient=post.author,
                    sender=request.user,
                    notification_type='comment',
                    post=post,
                    comment=comment
                )
        
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

# ==================== REPLY TO POST ====================
@login_required
@require_POST
def ajax_reply_to_post(request, post_id):
    try:
        original = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)
        content = data.get('content')

        if not content or not content.strip():
            return JsonResponse({'success': False, 'error': 'Content is required'}, status=400)

        reply = Post.objects.create(
            author=request.user,
            post_type='TEXT',
            title="",
            content=content.strip(),
            is_archived=False,
            parent=original,
            reply_count=0
        )

        original.reply_count += 1
        original.save(update_fields=['reply_count'])

        if original.author != request.user:
            Notification.objects.create(
                recipient=original.author,
                sender=request.user,
                notification_type='reply',
                post=original
            )

        reply_html = render_to_string('posts/_post_card.html', {
            'post': reply,
            'user': request.user,
            'user_reaction': None,
            'user_saved': False
        }, request=request)

        return JsonResponse({
            'success': True,
            'reply_html': reply_html,
            'reply_id': reply.id,
            'post_id': original.id,
            'new_reply_count': original.reply_count
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== AJAX DELETE COMMENT ====================
@login_required
@require_POST
def ajax_delete_comment(request, comment_id):
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        if comment.author != request.user and not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

        post_id = comment.post.id
        comment.delete()
        return JsonResponse({'success': True, 'post_id': post_id})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== AJAX REACT TO COMMENT ====================
@login_required
@require_POST
def ajax_react_to_comment(request, comment_id):
    try:
        comment = get_object_or_404(Comment, id=comment_id)
        data = json.loads(request.body)

        existing = CommentReaction.objects.filter(comment=comment, user=request.user).first()

        if existing:
            existing.delete()
        else:
            CommentReaction.objects.create(comment=comment, user=request.user)
            if comment.author != request.user:
                Notification.objects.create(
                    recipient=comment.author,
                    sender=request.user,
                    notification_type='reaction',
                    post=comment.post,
                    comment=comment
                )

        return JsonResponse({
            'success': True,
            'reaction_count': comment.reactions.count()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== AJAX SAVE POST ====================
@login_required
@require_POST
def ajax_save_post(request, post_id):
    try:
        post = get_object_or_404(Post, id=post_id)
        saved, created = PostSave.objects.get_or_create(post=post, user=request.user)

        if not created:
            saved.delete()
            is_saved = False
        else:
            is_saved = True

        return JsonResponse({
            'success': True,
            'is_saved': is_saved,
            'save_count': post.saves.count()
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== AJAX REPORT POST ====================
@login_required
@require_POST
def ajax_report_post(request, post_id):
    try:
        post = get_object_or_404(Post, id=post_id)
        data = json.loads(request.body)

        PostReport.objects.create(
            post=post,
            user=request.user,
            reason=data.get('reason', 'other'),
            description=data.get('description', '')
        )

        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)

# ==================== SAVED POSTS ====================
@login_required
def saved_posts(request):
    saved = PostSave.objects.filter(user=request.user).select_related('post', 'post__author')
    context = {'saved_posts': saved}
    return render(request, 'posts/saved_posts.html', context)

# ==================== SEARCH ====================
def search(request):
    query = request.GET.get('q', '')

    if query:
        posts = Post.objects.filter(
            Q(title__icontains=query) | Q(content__icontains=query) | Q(author__username__icontains=query),
            is_archived=False, parent=None
        )[:20]
        users = User.objects.filter(Q(username__icontains=query) | Q(email__icontains=query))[:10]
    else:
        posts, users = [], []

    context = {'query': query, 'posts': posts, 'users': users}
    return render(request, 'posts/search.html', context)

# ==================== ONLINE USERS API ====================
def online_users_api(request):
    count = 0
    for user in User.objects.filter(is_active=True):
        if cache.get(f'online_{user.id}'):
            count += 1
    return JsonResponse({'count': count})

# ==================== MIGRATION HELPERS ====================
@staff_member_required
def fake_post_migration(request):
    if not settings.DEBUG:
        return HttpResponse("Not allowed", status=403)

    out = io.StringIO()
    sys.stdout = out
    try:
        call_command('migrate', 'posts', '0007', '--fake', stdout=out)
        result = "✅ Migration fake successful!"
    except Exception as e:
        result = f"❌ Error: {e}"
    finally:
        sys.stdout = sys.__stdout__

    return HttpResponse(f"<pre>{result}\n\n{out.getvalue()}</pre>")

def run_posts_migrations(request):
    if not settings.DEBUG:
        return HttpResponse("Not allowed", status=403)

    out = io.StringIO()
    sys.stdout = out
    try:
        call_command('migrate', 'posts', verbosity=2, interactive=False)
        result = "✅ Migrations ran successfully!"
    except Exception as e:
        result = f"❌ Error: {e}"
    finally:
        sys.stdout = sys.__stdout__

    return HttpResponse(f"<pre>{result}\n\n{out.getvalue()}</pre>")

# ==================== ADMIN UTILITIES ====================
@login_required
def list_users(request):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=401)

    users = User.objects.all().values('id', 'username', 'email', 'is_superuser', 'is_staff')
    html = "<h1>Users</h1><table border=1><tr><th>ID</th><th>Username</th><th>Email</th><th>Type</th></tr>"
    for u in users:
        user_type = "SUPERUSER" if u['is_superuser'] else "STAFF" if u['is_staff'] else "USER"
        html += f"<tr><td>{u['id']}</td><td>{u['username']}</td><td>{u['email']}</td><td>{user_type}</td></tr>"
    html += "</table><a href='/admin/'>Admin</a>"
    return HttpResponse(html)

def test_view(request):
    return render(request, 'test.html')