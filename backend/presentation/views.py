"""Presentation views."""

from django.shortcuts import render


def dashboard(request):
    """Main dashboard view - shows current AQI and charts."""
    return render(request, 'dashboard.html')


def patterns(request):
    """Pattern analysis view - seasonal/diurnal patterns and correlations."""
    return render(request, 'patterns.html')


def about(request):
    """About page with project information."""
    return render(request, 'about.html')
