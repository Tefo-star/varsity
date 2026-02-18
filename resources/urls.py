from django.urls import path
from . import views

urlpatterns = [
    # Main dashboard - shows all universities
    path('', views.resources_dashboard, name='resources_dashboard'),
    
    # University detail - shows courses for a specific university
    path('university/<str:uni_code>/', views.university_detail, name='university_detail'),
    
    # Course detail - shows modules and years for a specific course
    path('university/<str:uni_code>/<str:course_code>/', views.course_detail, name='course_detail'),
    
    # Module detail - shows submodules and resources within a module
    path('university/<str:uni_code>/<str:course_code>/module/<int:module_id>/', 
         views.module_detail, name='module_detail'),
    
    # Year detail - shows all resources for a specific academic year
    path('university/<str:uni_code>/<str:course_code>/year/<int:year>/', 
         views.year_detail, name='year_detail'),
    
    # PDF viewing - opens PDF in browser
    path('view/<int:resource_id>/', views.view_pdf, name='view_pdf'),
    
    # PDF download - forces download with counter increment
    path('download/<int:resource_id>/', views.download_resource, name='download_resource'),
    
    # TEMPORARY: Run migrations manually (REMOVE AFTER USE)
    path('run-migrations/', views.run_migrations, name='run_migrations'),
]