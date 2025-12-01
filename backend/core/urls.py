"""
URL configuration for AAQIS project.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('backend.application.api.urls')),
    path('', include('backend.presentation.urls')),
]
