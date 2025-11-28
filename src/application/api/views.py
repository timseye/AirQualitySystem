"""API views."""

from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from src.domain.models import AirQualityMeasurement, Forecast


class MeasurementViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for air quality measurements."""
    queryset = AirQualityMeasurement.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by pollutant
        pollutant = self.request.query_params.get('pollutant')
        if pollutant:
            queryset = queryset.filter(pollutant=pollutant)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')


class ForecastViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for forecasts."""
    queryset = Forecast.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        model_type = self.request.query_params.get('model')
        if model_type:
            queryset = queryset.filter(model_type=model_type)
        
        return queryset.order_by('-created_at')


@api_view(['GET'])
def current_aqi(request):
    """Get current AQI for Astana."""
    # TODO: Implement after data is loaded
    return Response({
        'city': 'Astana',
        'aqi': None,
        'category': None,
        'message': 'Data not yet loaded. Run ETL pipeline first.',
    })


@api_view(['GET'])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'healthy',
        'service': 'AAQIS API',
        'version': '0.1.0',
    })
