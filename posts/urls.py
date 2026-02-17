from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('post/new/', views.create_post, name='create_post'),
    path('post/<int:post_id>/', views.post_detail, name='post_detail'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/react/', views.react_to_post, name='react_to_post'),
    path('create-superuser/', views.create_superuser, name='create_superuser'),
    # Add other URLs as needed
]