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

# LIST ALL USERS - ADD THIS TO SEE EXISTING USERNAMES
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

# SUPERUSER CREATION VIEW - USE THIS TO CREATE ADMIN ACCOUNT
def create_superuser(request):
    # Security: only allow if DEBUG is True
    if not settings.DEBUG:
        return HttpResponse("Not allowed - DEBUG mode is off", status=403)
    
    # Check if superuser already exists
    if User.objects.filter(is_superuser=True).exists():
        return HttpResponse("""
            <html>
                <head>
                    <style>
                        body { font-family: 'Poppins', sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
                        .container { max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; }
                        h1 { font-size: 2.5rem; margin-bottom: 20px; }
                        .warning { background: rgba(255,193,7,0.3); padding: 15px; border-radius: 10px; margin: 20px 0; }
                        a { display: inline-block; background: white; color: #667eea; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; margin: 10px; transition: all 0.3s; }
                        a:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>⚠️ Superuser Already Exists</h1>
                        <p>A superuser account already exists on this site.</p>
                        <div class="warning">
                            <p>Try these common usernames:</p>
                            <p><strong>admin • TefoKeletile • Tefo • tkeletile</strong></p>
                            <p><a href="/list-users/" style="color: white; text-decoration: underline;">Click here to see all users</a></p>
                        </div>
                        <div>
                            <a href="/admin/">Go to Admin Login</a>
                            <a href="/admin/password_reset/">Reset Password</a>
                        </div>
                    </div>
                </body>
            </html>
        """)
    
    # CREATE YOUR NEW SUPERUSER HERE - CHANGE THESE VALUES!
    username = 'TefoAdmin'  # <-- CHANGED to a different username
    email = 'tkeletile@gmail.com'     # <-- Your email
    password = 'Admin123!'      # <-- Your password
    
    # Create the superuser
    user = User.objects.create_superuser(username, email, password)
    
    return HttpResponse(f"""
        <html>
            <head>
                <style>
                    body {{ font-family: 'Poppins', sans-serif; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea, #764ba2); color: white; }}
                    .container {{ max-width: 600px; margin: 0 auto; background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; }}
                    h1 {{ font-size: 2.5rem; margin-bottom: 20px; }}
                    .credentials {{ background: rgba(0,0,0,0.3); padding: 20px; border-radius: 10px; margin: 20px 0; font-size: 1.2rem; }}
                    .warning {{ background: rgba(255,193,7,0.3); padding: 15px; border-radius: 10px; margin: 20px 0; }}
                    a {{ display: inline-block; background: white; color: #667eea; padding: 15px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; margin: 10px; transition: all 0.3s; }}
                    a:hover {{ transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,0,0,0.2); }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>✅ Superuser Created Successfully!</h1>
                    <div class="credentials">
                        <p><strong>Username:</strong> {username}</p>
                        <p><strong>Email:</strong> {email}</p>
                        <p><strong>Password:</strong> {password}</p>
                    </div>
                    <div class="warning">
                        ⚠️ <strong>IMPORTANT:</strong> Write these down and delete this code after logging in!
                    </div>
                    <div>
                        <a href="/admin/">Go to Admin Login</a>
                    </div>
                </div>
            </body>
        </html>
    """)