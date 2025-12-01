"""API URL configuration."""

from django.urls import path
from . import data_views

app_name = 'api'

urlpatterns = [
    # API Overview
    path('', data_views.api_overview, name='overview'),
    
    # Current data
    path('current/', data_views.current_data, name='current'),
    
    # Time series
    path('timeseries/', data_views.timeseries_data, name='timeseries'),
    path('daily/', data_views.daily_averages, name='daily'),
    
    # Statistics
    path('statistics/', data_views.statistics, name='statistics'),
    
    # Patterns
    path('hourly-pattern/', data_views.hourly_pattern, name='hourly_pattern'),
    path('monthly-pattern/', data_views.monthly_pattern, name='monthly_pattern'),
    
    # Correlation
    path('correlation/', data_views.correlation_data, name='correlation'),
]
