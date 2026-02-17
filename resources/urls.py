from django.urls import path
from . import views

urlpatterns = [
    path('', views.resources_dashboard, name='resources_dashboard'),
    path('university/<str:uni_code>/', views.university_detail, name='university_detail'),
    path('university/<str:uni_code>/<str:course_code>/', views.course_detail, name='course_detail'),
]