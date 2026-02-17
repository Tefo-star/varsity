from django.urls import path
from . import views

urlpatterns = [
    # ==================== MAIN SITE ROUTES ====================
    # Home page - displays all posts
    path('', views.home, name='home'),
    
    # Post creation
    path('post/new/', views.create_post, name='create_post'),
    
    # Post detail view (individual post page)
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    
    # Delete a post
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    
    # React to a post (like, love, haha, etc.)
    path('post/<int:post_id>/react/', views.react_to_post, name='react_to_post'),
    
    # API endpoint for online users count (fallback if WebSocket fails)
    path('api/online-count/', views.online_users_api, name='online_users_api'),
    
    # Test view (for debugging)
    path('test/', views.test_view, name='test'),
    
    # ==================== ADMIN FIX ROUTES ====================
    # 🔥🔥🔥 USE THESE IN ORDER TO FIX ADMIN 🔥🔥🔥
    
    # STEP 1: List all users (to see what's in database)
    path('list-users/', views.list_users, name='list_users'),
    
    # STEP 2: Completely wipe EVERYTHING (users, posts, comments, reactions)
    path('ultimate-nuke/', views.ultimate_nuke, name='ultimate_nuke'),
    
    # STEP 3: FORCE CREATE ADMIN - DELETES ALL EXISTING USERS AND CREATES NEW ONE
    # This ignores all checks and just makes a working admin
    path('force-create-admin/', views.force_create_admin, name='force_create_admin'),
    
    # ==================== OLD STUFF (KEPT FOR REFERENCE) ====================
    # Create a new superuser admin account (old version)
    # path('create-superuser/', views.create_superuser, name='create_superuser'),
]