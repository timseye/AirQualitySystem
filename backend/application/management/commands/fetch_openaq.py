import requests
import json
import os
from datetime import datetime, timedelta, timezone
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Fetch latest PM2.5 data from OpenAQ (US Embassy) and update unified_data table.'

    def handle(self, *args, **options):
        # OpenAQ Configuration
        API_KEY = os.getenv("OPENAQ_API_KEY", "c5fb53161f8c1a4a07723fbb9a025c04b61471501b7c7f6b4839def76e1b08bd")
        SENSOR_ID = 20512 # Astana US Embassy PM2.5
        
        # Fetch data for the last 24 hours to ensure we get the latest
        start_time = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        
        URL = f"https://api.openaq.org/v3/sensors/{SENSOR_ID}/measurements?limit=100&datetime_from={start_time}"
        
        HEADERS = {"X-API-Key": API_KEY}

        self.stdout.write("Fetching latest data from OpenAQ...")
        
        try:
            response = requests.get(URL, headers=HEADERS, timeout=30)
            data = response.json()
        except Exception as e:
            self.stderr.write(f"Network error: {e}")
            return

        if 'results' not in data or not data['results']:
            self.stderr.write(f"No results found since {start_time}")
            return

        # Sort by timestamp descending in Python to be sure
        results = data['results']
        results.sort(key=lambda x: x.get('period', {}).get('datetimeFrom', {}).get('utc', ''), reverse=True)
        
        # Parse latest measurement
        measurement = results[0]
        
        # Timestamp
        period = measurement.get('period', {})
        utc_str = period.get('datetimeFrom', {}).get('utc')
        
        if not utc_str:
            self.stderr.write("No timestamp found.")
            return
            
        # Parse UTC string (e.g., "2025-12-09T10:00:00Z")
        # Ensure it handles the 'Z' correctly
        utc_str = utc_str.replace('Z', '+00:00')
        dt_utc = datetime.fromisoformat(utc_str)
        
        # Value
        value = measurement.get('value')
        parameter = measurement.get('parameter', {}).get('name')
        units = measurement.get('parameter', {}).get('units')
        
        self.stdout.write(f"Latest: {dt_utc} | {parameter}: {value} {units}")
        
        if parameter != 'pm25':
            self.stderr.write(f"Unexpected parameter: {parameter}")
            return

        # Prepare temporal features
        hour = dt_utc.hour
        month = dt_utc.month
        day_of_week = dt_utc.weekday() # 0=Monday
        day_of_month = dt_utc.day
        
        is_weekend = day_of_week >= 5
        is_heating_season = month in [10, 11, 12, 1, 2, 3, 4]
        
        season = 'winter'
        if month in [3, 4, 5]: season = 'spring'
        elif month in [6, 7, 8]: season = 'summer'
        elif month in [9, 10, 11]: season = 'autumn'

        # Insert into DB
        with connection.cursor() as cursor:
            # Check if exists
            cursor.execute("SELECT id FROM unified_data WHERE timestamp_utc = %s", [dt_utc])
            existing = cursor.fetchone()
            
            if existing:
                self.stdout.write(f"Data for {dt_utc} already exists. Updating PM2.5...")
                cursor.execute("""
                    UPDATE unified_data SET
                        pm25 = %s,
                        pm25_source = 'openaq'
                    WHERE id = %s
                """, [value, existing[0]])
            else:
                self.stdout.write(f"Inserting new data for {dt_utc}...")
                cursor.execute("""
                    INSERT INTO unified_data (
                        timestamp_utc, location,
                        pm25, 
                        hour, month, day_of_week, day_of_month, season,
                        is_weekend, is_heating_season,
                        pm25_source, completeness_score
                    ) VALUES (
                        %s, 'Astana',
                        %s,
                        %s, %s, %s, %s, %s,
                        %s, %s,
                        'openaq', 0.3
                    )
                """, [
                    dt_utc,
                    value,
                    hour, month, day_of_week, day_of_month, season,
                    is_weekend, is_heating_season
                ])

        self.stdout.write(self.style.SUCCESS(f"Successfully processed OpenAQ data for {dt_utc}"))
