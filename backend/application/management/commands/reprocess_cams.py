import os
import glob
import zipfile
import pandas as pd
import xarray as xr
from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
from datetime import datetime

class Command(BaseCommand):
    help = 'Reprocess CAMS data from raw files with correct unit conversion (kg/m3 -> ug/m3) and update database.'

    def handle(self, *args, **options):
        self.stdout.write("Starting CAMS reprocessing...")
        
        # Create temp table once
        self.create_temp_table()
        
        # Path to raw data
        base_dir = settings.BASE_DIR
        cams_dir = os.path.join(base_dir, 'data', 'raw', 'cams')
        files = glob.glob(os.path.join(cams_dir, "*.nc.zip"))
        
        if not files:
            # Try recursive search if files are in subfolders
            files = glob.glob(os.path.join(cams_dir, "**", "*.nc.zip"), recursive=True)
            
        self.stdout.write(f"Found {len(files)} CAMS files.")
        
        total_updates = 0
        
        for f in files:
            self.stdout.write(f"Processing {os.path.basename(f)}...")
            try:
                self.process_file(f)
            except Exception as e:
                self.stderr.write(f"Error processing {f}: {e}")

        self.stdout.write(self.style.SUCCESS(f"Finished reprocessing. Database updated."))

    def create_temp_table(self):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS temp_cams_updates")
            cursor.execute("""
                CREATE TEMP TABLE temp_cams_updates (
                    timestamp_utc TIMESTAMP PRIMARY KEY,
                    pm25 DECIMAL,
                    pm10 DECIMAL,
                    no2 DECIMAL,
                    o3 DECIMAL,
                    so2 DECIMAL,
                    co DECIMAL
                )
            """)

    def process_file(self, zip_path):
        with zipfile.ZipFile(zip_path) as z:
            for name in z.namelist():
                if name.endswith('.nc'):
                    with z.open(name) as nc_file:
                        # Open dataset
                        ds = xr.open_dataset(nc_file, engine='h5netcdf')
                        df = ds.to_dataframe().reset_index()
                        
                        # Handle timestamps
                        if 'valid_time' in df.columns:
                            df = df.rename(columns={'valid_time': 'timestamp_utc'})
                        elif 'time' in df.columns:
                            df = df.rename(columns={'time': 'timestamp_utc'})
                            
                        # Convert to UTC and remove timezone
                        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True).dt.tz_localize(None)
                        
                        # Process pollutants
                        # Map: CAMS name -> (DB column, conversion_factor)
                        # CAMS is kg/m3. Target is ug/m3 (1e9) or mg/m3 (1e6 for CO)
                        param_map = {
                            'pm2p5': ('pm25', 1e9),          # kg/m3 -> ug/m3
                            'pm10': ('pm10', 1e9),           # kg/m3 -> ug/m3
                            'nitrogen_dioxide': ('no2', 1e9),# kg/m3 -> ug/m3
                            'no2': ('no2', 1e9),             # Short name
                            'ozone': ('o3', 1e9),            # kg/m3 -> ug/m3
                            'go3': ('o3', 1e9),              # Short name for Ozone
                            'sulphur_dioxide': ('so2', 1e9), # kg/m3 -> ug/m3
                            'so2': ('so2', 1e9),             # Short name
                            'carbon_monoxide': ('co', 1e6),  # kg/m3 -> mg/m3
                            'co': ('co', 1e6)                # Short name
                        }

                        # Aggregate if multiple grid points (Astana average)
                        # Group by timestamp
                        df_agg = df.groupby('timestamp_utc').mean(numeric_only=True).reset_index()
                        
                        # Prepare data for bulk insert into temp table
                        records = []
                        for _, row in df_agg.iterrows():
                            ts = row['timestamp_utc']
                            record = {'timestamp_utc': ts}
                            has_data = False
                            
                            for cams_col, (db_col, factor) in param_map.items():
                                if cams_col in row and pd.notnull(row[cams_col]):
                                    val = row[cams_col] * factor
                                    record[db_col] = val
                                    has_data = True
                                else:
                                    record[db_col] = None
                            
                            if has_data:
                                records.append(record)
                        
                        if records:
                            # Debug: Print first record to verify values
                            self.stdout.write(f"DEBUG: Sample record: {records[0]}")
                            self.bulk_update_db(records)

    def bulk_update_db(self, records):
        """
        Update DB records using a temporary table for performance.
        """
        if not records:
            return

        # Create DataFrame for easier SQL generation/dumping
        df_updates = pd.DataFrame(records)
        
        # We need to ensure columns match what we expect in the temp table
        # Columns: timestamp_utc, pm25, pm10, no2, o3, so2, co
        
        with connection.cursor() as cursor:
            # Truncate temp table first
            cursor.execute("TRUNCATE temp_cams_updates")
            
            # Prepare INSERT statement
            insert_sql = """
                INSERT INTO temp_cams_updates (timestamp_utc, pm25, pm10, no2, o3, so2, co)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            
            # Prepare data tuple list
            data_tuples = []
            for _, row in df_updates.iterrows():
                data_tuples.append((
                    row['timestamp_utc'],
                    row.get('pm25'), row.get('pm10'), row.get('no2'), 
                    row.get('o3'), row.get('so2'), row.get('co')
                ))
            
            cursor.executemany(insert_sql, data_tuples)
            
            # Perform Bulk Update
            update_sql = """
                UPDATE unified_data u
                SET 
                    pm25 = CASE 
                        WHEN t.pm25 IS NOT NULL AND (u.pm25_source = 'cams' OR u.pm25 IS NULL OR u.pm25 = 0) 
                        THEN t.pm25 ELSE u.pm25 END,
                    pm10 = CASE WHEN t.pm10 IS NOT NULL AND (u.pm10 = 0 OR u.pm10 IS NULL OR u.pm25_source = 'cams') THEN t.pm10 ELSE u.pm10 END,
                    no2 = CASE WHEN t.no2 IS NOT NULL AND (u.no2 = 0 OR u.no2 IS NULL OR u.pm25_source = 'cams') THEN t.no2 ELSE u.no2 END,
                    o3 = CASE WHEN t.o3 IS NOT NULL AND (u.o3 = 0 OR u.o3 IS NULL OR u.pm25_source = 'cams') THEN t.o3 ELSE u.o3 END,
                    so2 = CASE WHEN t.so2 IS NOT NULL AND (u.so2 = 0 OR u.so2 IS NULL OR u.pm25_source = 'cams') THEN t.so2 ELSE u.so2 END,
                    co = CASE WHEN t.co IS NOT NULL AND (u.co = 0 OR u.co IS NULL OR u.pm25_source = 'cams') THEN t.co ELSE u.co END,
                    pm25_source = CASE 
                        WHEN t.pm25 IS NOT NULL AND (u.pm25_source = 'cams' OR u.pm25 IS NULL OR u.pm25 = 0) 
                        THEN 'cams' ELSE u.pm25_source END
                FROM temp_cams_updates t
                WHERE u.timestamp_utc = t.timestamp_utc
            """
            
            cursor.execute(update_sql)
            self.stdout.write(f"Updated {cursor.rowcount} records from batch.")

    def update_db(self, timestamp, fields):
        # Deprecated by bulk_update_db
        pass
