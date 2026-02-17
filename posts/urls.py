from django.urls import path
from . import views

urlpatterns = [
    # ==================== MAIN SITE ROUTES ====================
    path('', views.home, name='home'),
    path('post/new/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/react/', views.react_to_post, name='react_to_post'),
    path('api/online-count/', views.online_users_api, name='online_users_api'),
    path('test/', views.test_view, name='test'),
    
    # ==================== ADMIN FIX ROUTES ====================
    path('list-users/', views.list_users, name='list_users'),
    path('ultimate-nuke/', views.ultimate_nuke, name='ultimate_nuke'),
    path('force-create-admin/', views.force_create_admin, name='force_create_admin'),
    path('force-login/', views.force_login, name='force_login'),
    path('debug-session/', views.debug_session, name='debug_session'),
    path('emergency-nuke/', views.emergency_nuke, name='emergency_nuke'),  # NEW
]