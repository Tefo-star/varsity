from django.urls import path
from . import views

urlpatterns = [
    path('', views.resources_dashboard, name='resources_dashboard'),
    path('university/<str:uni_code>/', views.university_detail, name='university_detail'),
    path('university/<str:uni_code>/<str:course_code>/', views.course_detail, name='course_detail'),
    path('university/<str:uni_code>/<str:course_code>/module/<int:module_id>/', views.module_detail, name='module_detail'),
    path('university/<str:uni_code>/<str:course_code>/year/<int:year>/', views.year_detail, name='year_detail'),
    path('view/<int:resource_id>/', views.view_pdf, name='view_pdf'),
    path('download/<int:resource_id>/', views.download_resource, name='download_resource'),
]