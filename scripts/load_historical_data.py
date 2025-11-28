#!/usr/bin/env python
"""
ETL Script: Load historical OpenAQ data into PostgreSQL.

This script reads the CSV file with historical PM2.5 measurements
and loads them into the database.

Usage:
    python scripts/load_historical_data.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.core.settings')

import django
django.setup()

import pandas as pd
from datetime import datetime
from django.db import transaction
from django.utils import timezone

from src.domain.models import City, MonitoringStation, AirQualityMeasurement


def load_openaq_historical_data():
    """Load historical OpenAQ data from CSV into database."""
    
    csv_path = PROJECT_ROOT / 'data' / 'raw' / 'openaq' / 'openaq_astana_historical.csv'
    
    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_path}")
        return False
    
    print(f"Loading data from: {csv_path}")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    print(f"Found {len(df)} records")
    print(f"Columns: {list(df.columns)}")
    
    # Show sample
    print("\nSample data:")
    print(df.head())
    
    # Determine datetime column
    datetime_col = 'timestamp_utc' if 'timestamp_utc' in df.columns else 'datetime'
    print(f"\nDate range: {df[datetime_col].min()} to {df[datetime_col].max()}")
    
    # Create or get Astana city
    astana, created = City.objects.get_or_create(
        name='Astana',
        country='Kazakhstan',
        defaults={
            'latitude': 51.1801,
            'longitude': 71.446,
            'timezone': 'Asia/Almaty',
        }
    )
    print(f"\nCity: {astana} ({'created' if created else 'exists'})")
    
    # Create or get US Embassy station
    station, created = MonitoringStation.objects.get_or_create(
        station_id='openaq-us-embassy-astana',
        defaults={
            'name': 'U.S. Embassy Astana',
            'city': astana,
            'source': 'openaq',
            'latitude': 51.1283,
            'longitude': 71.4305,
            'is_reference': True,
            'is_active': True,
        }
    )
    print(f"Station: {station} ({'created' if created else 'exists'})")
    
    # Load measurements
    print(f"\nLoading {len(df)} measurements into database...")
    
    # Determine datetime column
    datetime_col = 'timestamp_utc' if 'timestamp_utc' in df.columns else 'datetime'
    
    measurements_to_create = []
    skipped = 0
    
    for _, row in df.iterrows():
        try:
            # Parse datetime
            dt = pd.to_datetime(row[datetime_col])
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt, timezone.utc)
            
            measurements_to_create.append(
                AirQualityMeasurement(
                    station=station,
                    timestamp=dt,
                    pollutant='pm25',
                    value=row['value'],
                    unit='µg/m³',
                    is_validated=True,
                    quality_flag='historical_import',
                )
            )
        except Exception as e:
            skipped += 1
            if skipped <= 5:
                print(f"  WARNING: Skipping row: {e}")
    
    # Bulk create with ignore conflicts
    with transaction.atomic():
        created_count = AirQualityMeasurement.objects.bulk_create(
            measurements_to_create,
            ignore_conflicts=True,
            batch_size=1000,
        )
    
    print(f"\nSuccessfully loaded {len(created_count)} measurements")
    print(f"Skipped {skipped} rows with errors")
    
    # Summary
    total_in_db = AirQualityMeasurement.objects.filter(station=station).count()
    print(f"\nTotal measurements in database: {total_in_db}")
    
    return True


if __name__ == '__main__':
    print("=" * 60)
    print("AAQIS ETL: Historical Data Loader")
    print("=" * 60)
    
    success = load_openaq_historical_data()
    
    if success:
        print("\nETL completed successfully!")
    else:
        print("\nETL failed!")
        sys.exit(1)
