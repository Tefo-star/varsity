from django.urls import path
from . import views

urlpatterns = [
    # Main dashboard
    path('', views.resources_dashboard, name='resources_dashboard'),
    
    # University detail
    path('university/<str:uni_code>/', views.university_detail, name='university_detail'),
    
    # Course detail
    path('university/<str:uni_code>/<str:course_code>/', views.course_detail, name='course_detail'),
    
    # Year level detail (First Year, Second Year, etc.)
    path('university/<str:uni_code>/<str:course_code>/year-level/<int:year_level>/', 
         views.year_level_detail, name='year_level_detail'),
    
    # Year level + academic year detail
    path('university/<str:uni_code>/<str:course_code>/year-level/<int:year_level>/<int:academic_year>/', 
         views.year_level_academic_detail, name='year_level_academic_detail'),
    
    # Module detail
    path('university/<str:uni_code>/<str:course_code>/module/<int:module_id>/', 
         views.module_detail, name='module_detail'),
    
    # PDF viewing and download
    path('view/<int:resource_id>/', views.view_pdf, name='view_pdf'),
    path('download/<int:resource_id>/', views.download_resource, name='download_resource'),
    
    # Utility URLs
    path('run-migrations/', views.run_migrations, name='run_migrations'),
    path('force-tables/', views.force_create_tables_view, name='force_tables'),
]