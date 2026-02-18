from django.urls import path
from . import views

urlpatterns = [
    # Regular views
    path('', views.home, name='home'),
    path('post/new/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/react/', views.react_to_post, name='react_to_post'),
    path('comment/<int:comment_id>/reply/', views.reply_to_comment, name='reply_to_comment'),
    path('comment/<int:comment_id>/react/', views.react_to_comment, name='react_to_comment'),
    path('api/online-count/', views.online_users_api, name='online_users_api'),
    path('list-users/', views.list_users, name='list_users'),
    
    # AJAX endpoints (no page reload)
    path('ajax/react/<int:post_id>/', views.ajax_react_to_post, name='ajax_react_to_post'),
    path('ajax/comment/<int:post_id>/', views.ajax_add_comment, name='ajax_add_comment'),
    path('ajax/comment/<int:comment_id>/react/', views.ajax_react_to_comment, name='ajax_react_to_comment'),
]