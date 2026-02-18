from django.urls import path
from . import views

urlpatterns = [
    # ==================== MAIN DASHBOARD ====================
    path('', views.resources_dashboard, name='resources_dashboard'),
    
    # ==================== UNIVERSITY LEVEL ====================
    path('university/<str:uni_code>/', views.university_detail, name='university_detail'),
    
    # ==================== COURSE LEVEL ====================
    path('university/<str:uni_code>/<str:course_code>/', views.course_detail, name='course_detail'),
    
    # ==================== YEAR LEVEL (First Year, Second Year, etc.) ====================
    path('university/<str:uni_code>/<str:course_code>/year-level/<int:year_level>/', 
         views.year_level_detail, name='year_level_detail'),
    
    # ==================== YEAR LEVEL + ACADEMIC YEAR (e.g., First Year 2024) ====================
    path('university/<str:uni_code>/<str:course_code>/year-level/<int:year_level>/<int:academic_year>/', 
         views.year_level_academic_detail, name='year_level_academic_detail'),
    
    # ==================== MODULE LEVEL ====================
    path('university/<str:uni_code>/<str:course_code>/module/<int:module_id>/', 
         views.module_detail, name='module_detail'),
    
    # ==================== PDF VIEWING AND DOWNLOAD ====================
    path('view/<int:resource_id>/', views.view_pdf, name='view_pdf'),
    path('download/<int:resource_id>/', views.download_resource, name='download_resource'),
    
    # ==================== UTILITY URLS (FOR DATABASE FIXES) ====================
    # Run Django migrations
    path('run-migrations/', views.run_migrations, name='run_migrations'),
    
    # Force create tables using management command
    path('force-tables/', views.force_create_tables_view, name='force_tables'),
    
    # Fix missing columns (year_level, academic_year) directly in PostgreSQL
    path('fix-missing-columns/', views.fix_missing_columns, name='fix_missing_columns'),
    
    # NEW: Drop old year column that's causing IntegrityError
    path('drop-old-year/', views.drop_old_year_column, name='drop_old_year'),
]