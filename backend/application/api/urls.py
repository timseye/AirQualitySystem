"""API URL configuration."""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r'measurements', views.MeasurementViewSet, basename='measurement')
router.register(r'forecasts', views.ForecastViewSet, basename='forecast')

app_name = 'api'

urlpatterns = [
    path('', include(router.urls)),
    path('current/', views.current_aqi, name='current_aqi'),
    path('health/', views.health_check, name='health_check'),
]
