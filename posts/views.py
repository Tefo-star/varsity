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
from django.db import connection
from django.contrib.sessions.models import Session
from django.contrib.auth import login
from .models import Post, Comment, Reaction
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

# ==================== LIST USERS ====================
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

# ==================== FORCE CREATE ADMIN ====================
def force_create_admin(request):
    # Delete ALL existing users
    User.objects.all().delete()
    
    # Create brand new superuser with simple credentials
    username = 'admin'
    email = 'admin@localhost.com'
    password = 'admin123'
    
    user = User.objects.create_superuser(username, email, password)
    
    return HttpResponse(f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Poppins', sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #00b09b, #96c93d); color: white; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; }}
                    h1 {{ font-size: 3rem; margin-bottom: 20px; }}
                    .success {{ background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; margin: 20px 0; font-size: 1.5rem; }}
                    a {{ display: inline-block; background: white; color: #00b09b; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; margin: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ ADMIN CREATED!</h1>
                    <div class="success">
                        <p><strong>Username:</strong> admin</p>
                        <p><strong>Password:</strong> admin123</p>
                    </div>
                    <p style="font-size: 1.2rem;">All old users were deleted. Use these credentials NOW.</p>
                    <div>
                        <a href="/force-login/">FORCE LOGIN</a>
                        <a href="/admin/">GO TO ADMIN LOGIN</a>
                    </div>
                </div>
            </body>
        </html>
    """)

# ==================== FORCE LOGIN ====================
def force_login(request):
    # Get the admin user
    try:
        admin_user = User.objects.get(username='admin')
    except User.DoesNotExist:
        return HttpResponse("""
            <html>
                <head>
                    <style>
                        body { font-family: 'Poppins', sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #ff416c, #ff4b2b); color: white; }
                        .container { max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>❌ Admin user not found</h1>
                        <p>Create one first at <a href="/force-create-admin/" style="color: white;">/force-create-admin/</a></p>
                    </div>
                </body>
            </html>
        """)
    
    # Log them in programmatically
    login(request, admin_user)
    
    return HttpResponse(f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Poppins', sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #00b09b, #96c93d); color: white; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; }}
                    h1 {{ font-size: 3rem; margin-bottom: 20px; }}
                    .success {{ background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; margin: 20px 0; }}
                    a {{ display: inline-block; background: white; color: #00b09b; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; margin: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ FORCE LOGIN SUCCESSFUL!</h1>
                    <div class="success">
                        <p><strong>You are now logged in as:</strong> admin</p>
                    </div>
                    <p>Click below to go to admin panel (you should already be logged in)</p>
                    <div>
                        <a href="/admin/">GO TO ADMIN</a>
                    </div>
                </div>
            </body>
        </html>
    """)

# ==================== ULTIMATE NUKE ====================
def ultimate_nuke(request):
    # Delete everything
    Reaction.objects.all().delete()
    Comment.objects.all().delete()
    Post.objects.all().delete()
    Session.objects.all().delete()
    User.objects.all().delete()
    
    # Reset sequences
    with connection.cursor() as cursor:
        cursor.execute("ALTER SEQUENCE auth_user_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE posts_post_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE posts_comment_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE posts_reaction_id_seq RESTART WITH 1;")
    
    cache.clear()
    
    return HttpResponse("""
        <html>
            <head>
                <style>
                    body { font-family: 'Poppins', sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #ff416c, #ff4b2b); color: white; }
                    .container { max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; }
                    h1 { font-size: 3rem; margin-bottom: 20px; }
                    .fire { font-size: 5rem; margin: 20px 0; animation: flame 1s ease-in-out infinite; }
                    @keyframes flame {
                        0% { transform: scale(1); text-shadow: 0 0 10px orange; }
                        50% { transform: scale(1.2); text-shadow: 0 0 30px red; }
                        100% { transform: scale(1); text-shadow: 0 0 10px orange; }
                    }
                    a { display: inline-block; background: white; color: #ff416c; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; margin: 10px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="fire">🔥🔥🔥</div>
                    <h1>DATABASE WIPED!</h1>
                    <p style="font-size: 1.2rem;">Everything is gone. Create a new admin:</p>
                    <a href="/force-create-admin/">CREATE NEW ADMIN</a>
                </div>
            </body>
        </html>
    """)

# ==================== DEBUG SESSION ====================
def debug_session(request):
    import pprint
    from django.utils import timezone
    
    # Get all sessions
    sessions = Session.objects.all()
    session_info = []
    
    for session in sessions:
        try:
            data = session.get_decoded()
            session_info.append({
                'session_key': session.session_key[:10] + '...',
                'expire_date': session.expire_date.strftime('%Y-%m-%d %H:%M:%S'),
                'user_id': data.get('_auth_user_id'),
            })
        except:
            pass
    
    # Get request session
    request_session = dict(request.session.items())
    
    html = f"""
    <html>
        <head>
            <style>
                body {{ font-family: 'Poppins', sans-serif; background: linear-gradient(135deg, #667eea, #764ba2); color: white; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 30px; border-radius: 20px; }}
                h1, h2 {{ text-align: center; }}
                pre {{ background: #333; color: #0f0; padding: 15px; border-radius: 10px; overflow: auto; text-align: left; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.2); }}
                a {{ display: inline-block; background: white; color: #667eea; padding: 10px 20px; border-radius: 50px; text-decoration: none; margin: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔍 Session Debug</h1>
                
                <h2>📋 Request Session:</h2>
                <pre>{pprint.pformat(request_session)}</pre>
                
                <h2>💾 Database Sessions ({len(session_info)}):</h2>
                <table>
                    <tr>
                        <th>Session Key</th>
                        <th>Expires</th>
                        <th>User ID</th>
                    </tr>
    """
    
    for s in session_info:
        html += f"""
                    <tr>
                        <td>{s['session_key']}</td>
                        <td>{s['expire_date']}</td>
                        <td>{s['user_id']}</td>
                    </tr>
        """
    
    html += """
                </table>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="/admin/">Try Admin Again</a>
                    <a href="/force-login/">Force Login</a>
                </div>
            </div>
        </body>
    </html>
    """
    
    return HttpResponse(html)

# ==================== EMERGENCY NUKE - FORCE DELETE EVERYTHING WITH RAW SQL ====================
def emergency_nuke(request):
    # RAW SQL to TRUNCATE all tables (FORCE DELETE)
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE auth_user CASCADE;")
        cursor.execute("TRUNCATE TABLE posts_post CASCADE;")
        cursor.execute("TRUNCATE TABLE posts_comment CASCADE;")
        cursor.execute("TRUNCATE TABLE posts_reaction CASCADE;")
        cursor.execute("TRUNCATE TABLE posts_useractivity CASCADE;")
        cursor.execute("TRUNCATE TABLE django_session CASCADE;")
        cursor.execute("TRUNCATE TABLE django_admin_log CASCADE;")
        cursor.execute("TRUNCATE TABLE django_content_type CASCADE;")
        cursor.execute("TRUNCATE TABLE auth_permission CASCADE;")
        cursor.execute("TRUNCATE TABLE auth_group CASCADE;")
        cursor.execute("TRUNCATE TABLE auth_group_permissions CASCADE;")
        cursor.execute("TRUNCATE TABLE django_migrations CASCADE;")
        
        # Reset all sequences
        cursor.execute("ALTER SEQUENCE auth_user_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE posts_post_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE posts_comment_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE posts_reaction_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE posts_useractivity_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE django_admin_log_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE django_content_type_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE auth_permission_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE auth_group_id_seq RESTART WITH 1;")
        cursor.execute("ALTER SEQUENCE django_migrations_id_seq RESTART WITH 1;")
    
    cache.clear()
    
    return HttpResponse("""
        <html>
            <head>
                <style>
                    body { font-family: 'Poppins', sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #ff416c, #ff4b2b); color: white; }
                    .container { max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; }
                    h1 { font-size: 3rem; margin-bottom: 20px; }
                    .fire { font-size: 5rem; margin: 20px 0; animation: flame 1s ease-in-out infinite; }
                    @keyframes flame {
                        0% { transform: scale(1); text-shadow: 0 0 10px orange; }
                        50% { transform: scale(1.2); text-shadow: 0 0 30px red; }
                        100% { transform: scale(1); text-shadow: 0 0 10px orange; }
                    }
                    a { display: inline-block; background: white; color: #ff416c; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; margin: 10px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="fire">🔥🔥🔥</div>
                    <h1>🔥 EMERGENCY NUKE COMPLETE! 🔥</h1>
                    <p style="font-size: 1.2rem;">All tables TRUNCATED with CASCADE. Database is COMPLETELY EMPTY.</p>
                    <p style="background: rgba(0,0,0,0.3); padding: 10px; border-radius: 5px;">Next step: Create a new admin</p>
                    <a href="/force-create-admin/">CREATE NEW ADMIN</a>
                </div>
            </body>
        </html>
    """)