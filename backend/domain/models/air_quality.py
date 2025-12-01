"""
Domain models for AAQIS.
These are the core business entities representing air quality data.
"""

from django.db import models


class City(models.Model):
    """City/Location for air quality monitoring."""
    
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='Kazakhstan')
    latitude = models.FloatField()
    longitude = models.FloatField()
    timezone = models.CharField(max_length=50, default='Asia/Almaty')
    
    class Meta:
        app_label = 'domain'
        verbose_name_plural = 'cities'
        unique_together = ['name', 'country']
    
    def __str__(self):
        return f"{self.name}, {self.country}"


class MonitoringStation(models.Model):
    """Air quality monitoring station."""
    
    SOURCE_CHOICES = [
        ('openaq', 'OpenAQ'),
        ('aqicn', 'AQICN'),
        ('kazhydromet', 'Kazhydromet'),
        ('us_embassy', 'U.S. Embassy'),
    ]
    
    station_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='stations')
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES)
    latitude = models.FloatField()
    longitude = models.FloatField()
    is_reference = models.BooleanField(default=False, help_text="Is this a reference-grade station?")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        app_label = 'domain'
    
    def __str__(self):
        return f"{self.name} ({self.source})"


class AirQualityMeasurement(models.Model):
    """Individual air quality measurement."""
    
    POLLUTANT_CHOICES = [
        ('pm25', 'PM2.5'),
        ('pm10', 'PM10'),
        ('o3', 'Ozone'),
        ('no2', 'Nitrogen Dioxide'),
        ('so2', 'Sulfur Dioxide'),
        ('co', 'Carbon Monoxide'),
    ]
    
    UNIT_CHOICES = [
        ('µg/m³', 'Micrograms per cubic meter'),
        ('ppm', 'Parts per million'),
        ('ppb', 'Parts per billion'),
    ]
    
    station = models.ForeignKey(MonitoringStation, on_delete=models.CASCADE, related_name='measurements')
    timestamp = models.DateTimeField(db_index=True)
    pollutant = models.CharField(max_length=10, choices=POLLUTANT_CHOICES)
    value = models.FloatField()
    unit = models.CharField(max_length=10, choices=UNIT_CHOICES, default='µg/m³')
    
    # Quality flags
    is_validated = models.BooleanField(default=False)
    quality_flag = models.CharField(max_length=20, blank=True, null=True)
    
    class Meta:
        app_label = 'domain'
        unique_together = ['station', 'timestamp', 'pollutant']
        indexes = [
            models.Index(fields=['timestamp', 'pollutant']),
            models.Index(fields=['station', 'pollutant', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.pollutant}: {self.value} {self.unit} @ {self.timestamp}"


class WeatherData(models.Model):
    """Meteorological data for correlation analysis."""
    
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='weather_data')
    timestamp = models.DateTimeField(db_index=True)
    
    temperature = models.FloatField(null=True, blank=True, help_text="Temperature in Celsius")
    humidity = models.FloatField(null=True, blank=True, help_text="Relative humidity in %")
    pressure = models.FloatField(null=True, blank=True, help_text="Atmospheric pressure in hPa")
    wind_speed = models.FloatField(null=True, blank=True, help_text="Wind speed in m/s")
    wind_direction = models.FloatField(null=True, blank=True, help_text="Wind direction in degrees")
    precipitation = models.FloatField(null=True, blank=True, help_text="Precipitation in mm")
    
    class Meta:
        app_label = 'domain'
        unique_together = ['city', 'timestamp']
    
    def __str__(self):
        return f"Weather @ {self.city.name} {self.timestamp}"


class AQICalculation(models.Model):
    """Calculated Air Quality Index values."""
    
    CATEGORY_CHOICES = [
        ('good', 'Good (0-50)'),
        ('moderate', 'Moderate (51-100)'),
        ('unhealthy_sensitive', 'Unhealthy for Sensitive Groups (101-150)'),
        ('unhealthy', 'Unhealthy (151-200)'),
        ('very_unhealthy', 'Very Unhealthy (201-300)'),
        ('hazardous', 'Hazardous (301+)'),
    ]
    
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='aqi_calculations')
    timestamp = models.DateTimeField(db_index=True)
    aqi_value = models.IntegerField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    dominant_pollutant = models.CharField(max_length=10)
    
    # Individual pollutant sub-indices
    pm25_aqi = models.IntegerField(null=True, blank=True)
    pm10_aqi = models.IntegerField(null=True, blank=True)
    o3_aqi = models.IntegerField(null=True, blank=True)
    no2_aqi = models.IntegerField(null=True, blank=True)
    so2_aqi = models.IntegerField(null=True, blank=True)
    co_aqi = models.IntegerField(null=True, blank=True)
    
    class Meta:
        app_label = 'domain'
        unique_together = ['city', 'timestamp']
    
    def __str__(self):
        return f"AQI {self.aqi_value} ({self.category}) @ {self.city.name}"


class Forecast(models.Model):
    """ML model forecasts."""
    
    MODEL_CHOICES = [
        ('lstm', 'LSTM Neural Network'),
        ('svr', 'Support Vector Regression'),
        ('ensemble', 'Ensemble'),
    ]
    
    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name='forecasts')
    created_at = models.DateTimeField(auto_now_add=True)
    forecast_timestamp = models.DateTimeField(db_index=True, help_text="Time for which forecast is made")
    horizon_hours = models.IntegerField(help_text="Hours ahead from creation time")
    
    model_type = models.CharField(max_length=20, choices=MODEL_CHOICES)
    model_version = models.CharField(max_length=50)
    
    pollutant = models.CharField(max_length=10, default='pm25')
    predicted_value = models.FloatField()
    confidence_lower = models.FloatField(null=True, blank=True)
    confidence_upper = models.FloatField(null=True, blank=True)
    
    # For validation
    actual_value = models.FloatField(null=True, blank=True)
    error = models.FloatField(null=True, blank=True)
    
    class Meta:
        app_label = 'domain'
        indexes = [
            models.Index(fields=['city', 'forecast_timestamp']),
            models.Index(fields=['model_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.model_type} forecast: {self.predicted_value} for {self.forecast_timestamp}"
