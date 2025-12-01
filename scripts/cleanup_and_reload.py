"""
Clean up incorrectly loaded data and reload with proper structure.

This script:
1. Drops the malformed tables (openaq_data, weather_data, cams_data)
2. Reloads data with correct structure
3. Creates normalized schema
"""
import os
import glob
import zipfile
import pandas as pd
import xarray as xr
from sqlalchemy import create_engine, text

PG_CONN_STR = os.getenv("PG_CONN_STR", "postgresql://aaqis_user:aaqis_password@localhost:5432/aaqis_db")

def get_engine():
    return create_engine(PG_CONN_STR)

def cleanup_tables(engine):
    """Drop malformed tables"""
    print("\n" + "="*60)
    print("STEP 1: Cleaning up malformed tables")
    print("="*60)
    
    tables_to_drop = ['openaq_data', 'weather_data', 'cams_data']
    
    with engine.begin() as conn:
        for table in tables_to_drop:
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"✅ Dropped table: {table}")
            except Exception as e:
                print(f"⚠️  Could not drop {table}: {e}")

def load_openaq_clean(engine):
    """Load OpenAQ data with clean structure"""
    print("\n" + "="*60)
    print("STEP 2: Loading OpenAQ (clean)")
    print("="*60)
    
    files = glob.glob("data/raw/openaq/*.csv")
    
    for f in files:
        print(f"\n📄 Processing: {os.path.basename(f)}")
        df = pd.read_csv(f)
        
        # Standardize column names
        df = df.rename(columns={
            'datetime': 'timestamp_utc',
            'location': 'location_name'
        })
        
        # Add metadata
        df['location'] = 'Astana'
        df['latitude'] = 51.1694
        df['longitude'] = 71.4491
        df['source_file'] = os.path.basename(f)
        
        # Ensure timestamp is UTC
        if 'timestamp_utc' in df.columns:
            df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True)
        
        # Select and order columns properly
        cols_to_keep = ['timestamp_utc', 'location', 'latitude', 'longitude', 
                       'parameter', 'value', 'units', 'source_file']
        
        # Add optional columns if they exist
        if 'data_quality' in df.columns:
            cols_to_keep.append('data_quality')
        if 'location_id' in df.columns:
            cols_to_keep.append('location_id')
        if 'sensor_id' in df.columns:
            cols_to_keep.append('sensor_id')
        
        df_clean = df[[col for col in cols_to_keep if col in df.columns]].copy()
        
        print(f"   Records: {len(df_clean):,}")
        print(f"   Columns: {list(df_clean.columns)}")
        
        # Load to database
        with engine.begin() as conn:
            df_clean.to_sql('openaq_data', conn, if_exists='append', index=False)
        
        print(f"   ✅ Loaded to openaq_data")

def load_weather_clean(engine):
    """Load Open-Meteo data with clean structure"""
    print("\n" + "="*60)
    print("STEP 3: Loading Weather (clean)")
    print("="*60)
    
    files = glob.glob("data/raw/openmeteo/*.csv")
    
    for f in files:
        print(f"\n📄 Processing: {os.path.basename(f)}")
        df = pd.read_csv(f)
        
        # Rename timestamp column if needed
        if 'time' in df.columns:
            df = df.rename(columns={'time': 'timestamp_local'})
        
        # Add location metadata
        df['location'] = 'Astana'
        df['latitude'] = 51.1694
        df['longitude'] = 71.4491
        df['source_file'] = os.path.basename(f)
        
        # Parse timestamp
        if 'timestamp_local' in df.columns:
            df['timestamp_local'] = pd.to_datetime(df['timestamp_local'])
        
        print(f"   Records: {len(df):,}")
        print(f"   Columns: {len(df.columns)}")
        
        # Load to database
        with engine.begin() as conn:
            df.to_sql('weather_data', conn, if_exists='append', index=False)
        
        print(f"   ✅ Loaded to weather_data")

def load_cams_clean(engine):
    """Load CAMS data with clean structure (long format)"""
    print("\n" + "="*60)
    print("STEP 4: Loading CAMS (clean, long format)")
    print("="*60)
    
    files = glob.glob("data/raw/cams/*.nc.zip")
    total_records = 0
    
    for f in files[:10]:  # Limit to first 10 files for testing
        print(f"\n📄 Processing: {os.path.basename(f)}")
        
        with zipfile.ZipFile(f) as z:
            for name in z.namelist():
                if name.endswith('.nc'):
                    with z.open(name) as nc_file:
                        ds = xr.open_dataset(nc_file, engine='h5netcdf')
                        
                        # Convert to DataFrame (this creates proper structure)
                        df = ds.to_dataframe().reset_index()
                        
                        # Add metadata
                        df['source_file'] = os.path.basename(f)
                        df['location'] = 'Astana'
                        
                        # Rename time column
                        if 'valid_time' in df.columns:
                            df = df.rename(columns={'valid_time': 'timestamp_utc'})
                        elif 'time' in df.columns:
                            df = df.rename(columns={'time': 'timestamp_utc'})
                        
                        # Convert to long format (melt pollutant columns)
                        id_cols = ['timestamp_utc', 'latitude', 'longitude', 'location', 'source_file']
                        if 'pressure_level' in df.columns:
                            id_cols.append('pressure_level')
                        
                        # Identify pollutant columns
                        pollutant_cols = [col for col in df.columns 
                                        if col in ['pm2p5', 'pm10', 'nitrogen_dioxide', 
                                                  'ozone', 'sulphur_dioxide', 'carbon_monoxide']]
                        
                        if pollutant_cols:
                            df_long = df.melt(
                                id_vars=[col for col in id_cols if col in df.columns],
                                value_vars=pollutant_cols,
                                var_name='parameter',
                                value_name='value'
                            )
                            
                            # Map parameter names
                            param_map = {
                                'pm2p5': 'pm25',
                                'nitrogen_dioxide': 'no2',
                                'ozone': 'o3',
                                'sulphur_dioxide': 'so2',
                                'carbon_monoxide': 'co'
                            }
                            df_long['parameter'] = df_long['parameter'].replace(param_map)
                            df_long['unit'] = 'kg/m³'
                            
                            # Remove nulls
                            df_long = df_long.dropna(subset=['value'])
                            
                            print(f"   Records: {len(df_long):,}")
                            
                            # Load to database
                            if len(df_long) > 0:
                                with engine.begin() as conn:
                                    df_long.to_sql('cams_data', conn, if_exists='append', index=False)
                                total_records += len(df_long)
    
    print(f"\n✅ Total CAMS records loaded: {total_records:,}")

def main():
    engine = get_engine()
    
    print("\n" + "="*60)
    print("DATA CLEANUP AND RELOAD")
    print("="*60)
    
    # Step 1: Cleanup
    cleanup_tables(engine)
    
    # Step 2-4: Reload with clean structure
    load_openaq_clean(engine)
    load_weather_clean(engine)
    load_cams_clean(engine)
    
    print("\n" + "="*60)
    print("✅ CLEANUP AND RELOAD COMPLETE")
    print("="*60)
    print("\nNext: Run normalization script")
    print("  python scripts/normalize_data.py")

if __name__ == "__main__":
    main()
