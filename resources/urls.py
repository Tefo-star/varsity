from django.urls import path
from . import views

urlpatterns = [
    path('', views.resources_dashboard, name='resources_dashboard'),
]