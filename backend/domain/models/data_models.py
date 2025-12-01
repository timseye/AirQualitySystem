"""
Models for normalized data tables (unified_data, measurements, weather).
These models map to existing PostgreSQL tables created by ETL scripts.
"""

from django.db import models


class Measurement(models.Model):
    """Air quality measurements from OpenAQ and CAMS."""
    
    timestamp = models.DateTimeField(db_index=True)
    source = models.CharField(max_length=50)  # 'openaq' or 'cams'
    parameter = models.CharField(max_length=50)  # 'pm25', 'pm10', 'no2', etc.
    value = models.FloatField()
    unit = models.CharField(max_length=20, default='µg/m³')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    
    class Meta:
        app_label = 'domain'
        db_table = 'measurements'
        managed = False  # Don't manage this table via Django migrations
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['parameter']),
        ]
    
    def __str__(self):
        return f"{self.parameter}: {self.value} @ {self.timestamp}"


class Weather(models.Model):
    """Weather data from Open-Meteo."""
    
    timestamp = models.DateTimeField(db_index=True, primary_key=True)
    temperature_2m = models.FloatField(null=True, blank=True)
    relative_humidity_2m = models.FloatField(null=True, blank=True)
    surface_pressure = models.FloatField(null=True, blank=True)
    wind_speed_10m = models.FloatField(null=True, blank=True)
    wind_direction_10m = models.FloatField(null=True, blank=True)
    precipitation = models.FloatField(null=True, blank=True)
    cloud_cover = models.FloatField(null=True, blank=True)
    
    class Meta:
        app_label = 'domain'
        db_table = 'weather'
        managed = False
    
    def __str__(self):
        return f"Weather @ {self.timestamp}"


class UnifiedData(models.Model):
    """Unified dataset for ML - joins measurements with weather."""
    
    timestamp = models.DateTimeField(db_index=True, primary_key=True)
    
    # Air quality
    pm25 = models.FloatField(null=True, blank=True)
    pm25_source = models.CharField(max_length=50, null=True, blank=True)
    pm10 = models.FloatField(null=True, blank=True)
    no2 = models.FloatField(null=True, blank=True)
    so2 = models.FloatField(null=True, blank=True)
    o3 = models.FloatField(null=True, blank=True)
    co = models.FloatField(null=True, blank=True)
    
    # Weather
    temperature_2m = models.FloatField(null=True, blank=True)
    relative_humidity_2m = models.FloatField(null=True, blank=True)
    surface_pressure = models.FloatField(null=True, blank=True)
    wind_speed_10m = models.FloatField(null=True, blank=True)
    wind_direction_10m = models.FloatField(null=True, blank=True)
    precipitation = models.FloatField(null=True, blank=True)
    cloud_cover = models.FloatField(null=True, blank=True)
    
    class Meta:
        app_label = 'domain'
        db_table = 'unified_data'
        managed = False
    
    def __str__(self):
        return f"Data @ {self.timestamp} - PM2.5: {self.pm25}"
    
    @property
    def aqi_category(self):
        """Calculate AQI category based on PM2.5."""
        if self.pm25 is None:
            return 'unknown'
        if self.pm25 <= 12:
            return 'good'
        elif self.pm25 <= 35.4:
            return 'moderate'
        elif self.pm25 <= 55.4:
            return 'unhealthy_sensitive'
        elif self.pm25 <= 150.4:
            return 'unhealthy'
        elif self.pm25 <= 250.4:
            return 'very_unhealthy'
        else:
            return 'hazardous'
    
    @property
    def aqi_value(self):
        """Calculate US EPA AQI from PM2.5."""
        if self.pm25 is None:
            return None
        
        # EPA AQI breakpoints for PM2.5
        breakpoints = [
            (0, 12.0, 0, 50),
            (12.1, 35.4, 51, 100),
            (35.5, 55.4, 101, 150),
            (55.5, 150.4, 151, 200),
            (150.5, 250.4, 201, 300),
            (250.5, 500.4, 301, 500),
        ]
        
        pm = self.pm25
        for bp_lo, bp_hi, i_lo, i_hi in breakpoints:
            if bp_lo <= pm <= bp_hi:
                return round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (pm - bp_lo) + i_lo)
        
        return 500 if pm > 500.4 else 0
