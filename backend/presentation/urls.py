"""Presentation layer URL configuration."""

from django.urls import path
from . import views

app_name = 'presentation'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('patterns/', views.patterns, name='patterns'),
    path('about/', views.about, name='about'),
]
