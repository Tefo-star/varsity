from django.urls import path
from . import views

urlpatterns = [
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
    
    # 🔥 TEMPORARY ADMIN UTILITIES - REMOVE AFTER USE 🔥
    # Create a new superuser admin account
    path('create-superuser/', views.create_superuser, name='create_superuser'),
    
    # List all registered users (useful for finding usernames)
    path('list-users/', views.list_users, name='list_users'),
    
    # ULTIMATE NUKE - Force wipe everything with sequence reset (FIXED FUNCTION NAME)
    path('ultimate-nuke/', views.ultimate_nuke, name='ultimate_nuke'),
    
    # API endpoint for online users count (fallback if WebSocket fails)
    path('api/online-count/', views.online_users_api, name='online_users_api'),
    
    # Test view (for debugging)
    path('test/', views.test_view, name='test'),
]