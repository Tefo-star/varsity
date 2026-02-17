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
    
    # API endpoint for online users count
    path('api/online-count/', views.online_users_api, name='online_users_api'),
    
    # Optional: Keep list-users for debugging (can remove later)
    path('list-users/', views.list_users, name='list_users'),
]