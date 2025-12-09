import requests
import json
import os
from datetime import datetime, timedelta, timezone
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings

class Command(BaseCommand):
    help = 'Fetch latest air quality data from AQICN API and update unified_data table.'

    def handle(self, *args, **options):
        # AQICN Token
        API_TOKEN = os.getenv("AQICN_TOKEN", "d59d891eb5c761c98d06962f8294037535e8d1d7")
        if not API_TOKEN:
            self.stderr.write("Error: AQICN_TOKEN environment variable not set.")
            return
            
        CITY_URL = f"https://api.waqi.info/feed/astana/?token={API_TOKEN}"

        self.stdout.write("Fetching latest data from AQICN...")
        
        try:
            response = requests.get(CITY_URL, timeout=30)
            data = response.json()
        except Exception as e:
            self.stderr.write(f"Network error: {e}")
            return

        if data.get('status') != 'ok':
            self.stderr.write(f"API Error: {data.get('data')}")
            return

        # Parse data
        result = data.get('data', {})
        iaqi = result.get('iaqi', {})
        
        # Extract values
        # Note: WAQI returns AQI values for pollutants, not raw concentrations.
        # Ideally, we should convert AQI back to concentration or use a raw data source.
        # For now, we store as is but mark source as 'aqicn'.
        pm25 = iaqi.get('pm25', {}).get('v')
        pm10 = iaqi.get('pm10', {}).get('v')
        no2 = iaqi.get('no2', {}).get('v')
        so2 = iaqi.get('so2', {}).get('v')
        o3 = iaqi.get('o3', {}).get('v')
        co = iaqi.get('co', {}).get('v')
        
        # Weather (usually raw values)
        temp = iaqi.get('t', {}).get('v')
        humi = iaqi.get('h', {}).get('v')
        wind = iaqi.get('w', {}).get('v') 
        press = iaqi.get('p', {}).get('v') 
        
        # Timestamp parsing
        # Try to use 'v' (epoch) which is usually UTC or local? 
        # WAQI 'v' in time object is usually local epoch time? No, epoch is universal.
        # Let's verify with 's' (string) and 'tz' (offset).
        time_info = result.get('time', {})
        local_time_str = time_info.get('s') # e.g. "2023-10-25 15:00:00"
        tz_offset = time_info.get('tz')     # e.g. "+06:00"
        
        dt_utc = None
        
        if local_time_str:
            try:
                # Parse local time
                dt_local = datetime.fromisoformat(local_time_str)
                
                # Handle offset
                if tz_offset:
                    # Parse offset like "+06:00"
                    sign = 1 if tz_offset.startswith('+') else -1
                    hours = int(tz_offset[1:3])
                    minutes = int(tz_offset[4:6])
                    offset = timedelta(hours=hours, minutes=minutes) * sign
                    # Apply offset to get UTC
                    # If local is 15:00 and offset is +6, UTC is 09:00.
                    # dt_local is naive, assuming it's the wall clock time.
                    dt_utc = dt_local - offset
                else:
                    # Fallback to hardcoded +6 for Astana
                    dt_utc = dt_local - timedelta(hours=6)
            except ValueError as e:
                self.stdout.write(f"Date parsing error: {e}")
                pass
        
        if not dt_utc:
             self.stdout.write("Could not determine timestamp, skipping.")
             return

        # Prepare temporal features
        hour = dt_utc.hour
        month = dt_utc.month
        day_of_week = dt_utc.weekday() # 0=Monday
        day_of_month = dt_utc.day
        
        is_weekend = day_of_week >= 5
        # Heating season: Oct-Apr (10,11,12,1,2,3,4)
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
                self.stdout.write(f"Data for {dt_utc} already exists. Updating...")
                cursor.execute("""
                    UPDATE unified_data SET
                        pm25 = %s,
                        pm10 = %s,
                        no2 = %s,
                        o3 = %s,
                        so2 = %s,
                        co = %s,
                        temperature_c = %s,
                        humidity_pct = %s,
                        pressure_hpa = %s,
                        wind_speed_ms = %s,
                        pm25_source = 'aqicn',
                        weather_source = 'aqicn'
                    WHERE id = %s
                """, [pm25, pm10, no2, o3, so2, co, temp, humi, press, wind, existing[0]])
            else:
                self.stdout.write(f"Inserting new data for {dt_utc}...")
                cursor.execute("""
                    INSERT INTO unified_data (
                        timestamp_utc, location,
                        pm25, pm10, no2, o3, so2, co,
                        temperature_c, humidity_pct, pressure_hpa, wind_speed_ms,
                        hour, month, day_of_week, day_of_month, season,
                        is_weekend, is_heating_season,
                        pm25_source, weather_source, completeness_score
                    ) VALUES (
                        %s, 'Astana',
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s, %s, %s, %s,
                        %s, %s,
                        'aqicn', 'aqicn', 1.0
                    )
                """, [
                    dt_utc,
                    pm25, pm10, no2, o3, so2, co,
                    temp, humi, press, wind,
                    hour, month, day_of_week, day_of_month, season,
                    is_weekend, is_heating_season
                ])

        self.stdout.write(self.style.SUCCESS(f"Successfully processed data for {dt_utc}"))
