from django.urls import path
from . import views

urlpatterns = [
    # Main feed
    path('', views.home, name='home'),
    path('load-more/', views.load_more_posts, name='load_more_posts'),
    
    # Post operations
    path('post/new/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/edit/', views.edit_post, name='edit_post'),
    
    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/<str:username>/', views.profile, name='user_profile'),
    # Follow URL REMOVED
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/count/', views.get_notification_count, name='notification_count'),
    
    # Saved posts
    path('saved/', views.saved_posts, name='saved_posts'),
    
    # Search
    path('search/', views.search, name='search'),
    
    # API endpoints
    path('api/online-count/', views.online_users_api, name='online_users_api'),
    
    # AJAX endpoints
    path('ajax/react/<int:post_id>/', views.ajax_react_to_post, name='ajax_react_to_post'),
    path('ajax/comment/<int:post_id>/', views.ajax_add_comment, name='ajax_add_comment'),
    path('ajax/comment/<int:comment_id>/delete/', views.ajax_delete_comment, name='ajax_delete_comment'),
    path('ajax/comment/<int:comment_id>/react/', views.ajax_react_to_comment, name='ajax_react_to_comment'),
    path('ajax/post/<int:post_id>/save/', views.ajax_save_post, name='ajax_save_post'),
    path('ajax/post/<int:post_id>/share/', views.ajax_share_post, name='ajax_share_post'),
    path('ajax/post/<int:post_id>/report/', views.ajax_report_post, name='ajax_report_post'),
    path('ajax/post/<int:post_id>/reactions/', views.get_post_reactions, name='get_post_reactions'),
    path('ajax/post/<int:post_id>/reply/', views.ajax_reply_to_post, name='ajax_reply_to_post'),  # NEW URL
    
    # Legacy endpoints
    path('comment/<int:comment_id>/reply/', views.reply_to_comment, name='reply_to_comment'),
    path('comment/<int:comment_id>/react/', views.react_to_comment, name='react_to_comment'),
    
    # ==================== MIGRATION HELPERS ====================
    path('run-migrations/', views.run_posts_migrations, name='run_posts_migrations'),
    path('fake-migration/', views.fake_post_migration, name='fake_post_migration'),
    
    # Admin utilities
    path('list-users/', views.list_users, name='list_users'),
    path('test/', views.test_view, name='test'),
]