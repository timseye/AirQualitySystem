"""
ETL Pipeline: Transform raw data into normalized ML-ready format

Steps:
1. Create normalized schema (measurements, weather, unified_data)
2. Transform OpenAQ → measurements
3. Transform CAMS → measurements  
4. Transform Open-Meteo → weather
5. Join measurements + weather → unified_data (ML-ready)
6. Add temporal features for ML models

Usage:
    python scripts/normalize_data.py
"""
import os
import glob
import zipfile
import pandas as pd
import xarray as xr
from sqlalchemy import create_engine, text

PG_CONN_STR = os.getenv("PG_CONN_STR", "postgresql://aaqis_user:aaqis_password@localhost:5432/aaqis_db")
CHUNK_SIZE = 5000  # Insert in chunks

def get_engine():
    return create_engine(PG_CONN_STR)

def insert_dataframe(df, table_name, engine):
    """Insert DataFrame in chunks to avoid memory issues"""
    total = 0
    for i in range(0, len(df), CHUNK_SIZE):
        chunk = df.iloc[i:i+CHUNK_SIZE]
        with engine.begin() as conn:
            chunk.to_sql(table_name, conn, if_exists='append', index=False)
        total += len(chunk)
        if total % 10000 == 0:
            print(f"   ... inserted {total:,} records")
    return total

def create_normalized_schema(engine):
    """Create normalized tables from SQL file"""
    print("\n" + "="*60)
    print("STEP 1: Creating Normalized Schema")
    print("="*60)
    
    with open('scripts/create_normalized_schema.sql', 'r') as f:
        sql = f.read()
    
    with engine.begin() as conn:
        conn.execute(text(sql))
    
    print("✅ Schema created: measurements, weather, unified_data")

def transform_openaq(engine):
    """Transform OpenAQ data into normalized measurements table"""
    print("\n" + "="*60)
    print("STEP 2: Transforming OpenAQ → measurements")
    print("="*60)
    
    import glob
    
    # Read directly from CSV files
    files = glob.glob("data/raw/openaq/*.csv")
    all_data = []
    
    for f in files:
        df = pd.read_csv(f)
        
        # Rename columns to match schema
        if 'datetime' in df.columns:
            df = df.rename(columns={'datetime': 'timestamp_utc'})
        
        # Standardize
        df['location'] = 'Astana'
        df['latitude'] = 51.1694
        df['longitude'] = 71.4491
        df['data_source'] = 'openaq'
        df['source_file'] = os.path.basename(f)
        
        # Normalize parameter names
        if 'parameter' in df.columns:
            df['parameter'] = df['parameter'].str.lower()
        
        # Rename 'units' to 'unit'
        if 'units' in df.columns:
            df = df.rename(columns={'units': 'unit'})
        
        all_data.append(df)
    
    df = pd.concat(all_data, ignore_index=True)
    print(f"📊 Read {len(df):,} records from CSV files")
    
    # Convert timestamp to UTC datetime and remove timezone info for PostgreSQL
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True).dt.tz_localize(None)
    
    # Select only needed columns
    cols = ['timestamp_utc', 'location', 'latitude', 'longitude', 
            'parameter', 'value', 'unit', 'data_source', 'source_file']
    
    # Add optional columns if they exist
    if 'data_quality' in df.columns:
        cols.append('data_quality')
    
    df = df[[col for col in cols if col in df.columns]]
    
    # Remove nulls and invalid values
    df = df.dropna(subset=['value'])
    df = df[df['value'] >= 0]  # Remove negative values like -999
    
    # Remove duplicates (keep first occurrence)
    df = df.drop_duplicates(subset=['timestamp_utc', 'location', 'parameter', 'data_source'], keep='first')
    
    # Sort by timestamp to ensure consistent ordering
    df = df.sort_values('timestamp_utc').reset_index(drop=True)
    print(f"📊 After deduplication: {len(df):,} records")
    
    # Insert into measurements using chunked inserts
    count = insert_dataframe(df, 'measurements', engine)
    print(f"✅ Inserted {count:,} measurements from OpenAQ")

def transform_cams(engine):
    """Transform CAMS data into normalized measurements table"""
    print("\n" + "="*60)
    print("STEP 3: Transforming CAMS → measurements")
    print("="*60)
    
    import glob
    import zipfile
    
    files = glob.glob("data/raw/cams/*.nc.zip")
    print(f"📁 Found {len(files)} CAMS files")
    
    all_data = []
    files_processed = 0
    
    # Process all CAMS files
    for f in files:
        print(f"  Processing: {os.path.basename(f)}")
        
        try:
            with zipfile.ZipFile(f) as z:
                for name in z.namelist():
                    if name.endswith('.nc'):
                        with z.open(name) as nc_file:
                            ds = xr.open_dataset(nc_file, engine='h5netcdf')
                            
                            # Convert to DataFrame
                            df = ds.to_dataframe().reset_index()
                            
                            # Rename time column
                            if 'valid_time' in df.columns:
                                df = df.rename(columns={'valid_time': 'timestamp_utc'})
                            elif 'time' in df.columns:
                                df = df.rename(columns={'time': 'timestamp_utc'})
                            
                            # Add metadata
                            df['location'] = 'Astana'
                            df['source_file'] = os.path.basename(f)
                            
                            # Melt pollutant columns to long format
                            id_cols = ['timestamp_utc', 'latitude', 'longitude', 'location', 'source_file']
                            if 'pressure_level' in df.columns:
                                id_cols.append('pressure_level')
                            
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
                                df_long['data_source'] = 'cams'
                                df_long['data_quality'] = 'reanalysis'
                                
                                # Remove nulls
                                df_long = df_long.dropna(subset=['value'])
                                
                                if len(df_long) > 0:
                                    all_data.append(df_long)
                                    files_processed += 1
        
        except Exception as e:
            print(f"    ⚠️  Error: {e}")
            continue
    
    if all_data:
        df = pd.concat(all_data, ignore_index=True)
        print(f"\n📊 Processed {files_processed} files → {len(df):,} raw records")
        
        # Convert timestamp and remove timezone for PostgreSQL
        df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True).dt.tz_localize(None)
        
        # CAMS has grid data - aggregate to single point for Astana
        # Take mean across all grid points for each timestamp/parameter
        df_agg = df.groupby(['timestamp_utc', 'location', 'parameter', 'data_source']).agg({
            'value': 'mean',
            'latitude': 'mean',
            'longitude': 'mean',
            'unit': 'first',
            'data_quality': 'first',
            'source_file': 'first'
        }).reset_index()
        
        # Set fixed Astana coordinates
        df_agg['latitude'] = 51.1694
        df_agg['longitude'] = 71.4491
        
        print(f"📊 After aggregation: {len(df_agg):,} records")
        
        # Remove duplicates (should not be any after aggregation)
        df_agg = df_agg.drop_duplicates(subset=['timestamp_utc', 'location', 'parameter', 'data_source'], keep='first')
        
        # Sort by timestamp
        df_agg = df_agg.sort_values('timestamp_utc').reset_index(drop=True)
        
        # Select final columns
        final_cols = ['timestamp_utc', 'location', 'latitude', 'longitude', 
                     'parameter', 'value', 'unit', 'data_source', 
                     'data_quality', 'source_file']
        df_agg = df_agg[[col for col in final_cols if col in df_agg.columns]]
        
        # Insert into measurements using chunked inserts
        count = insert_dataframe(df_agg, 'measurements', engine)
        print(f"✅ Inserted {count:,} measurements from CAMS")
    else:
        print("⚠️  No CAMS data to insert")

def transform_weather(engine):
    """Transform Open-Meteo data into normalized weather table"""
    print("\n" + "="*60)
    print("STEP 4: Transforming Open-Meteo → weather")
    print("="*60)
    
    import glob
    
    # Read directly from CSV files
    files = glob.glob("data/raw/openmeteo/*.csv")
    all_data = []
    
    for f in files:
        df = pd.read_csv(f)
        
        # Rename columns
        if 'time' in df.columns:
            df = df.rename(columns={'time': 'timestamp_local'})
        
        # Add metadata
        df['location'] = 'Astana'
        df['source_file'] = os.path.basename(f)
        
        all_data.append(df)
    
    df = pd.concat(all_data, ignore_index=True)
    print(f"📊 Read {len(df):,} records from CSV files")
    
    # Convert local time to UTC (Astana is UTC+6) and remove timezone
    df['timestamp_utc'] = pd.to_datetime(df['timestamp_local']) - pd.Timedelta(hours=6)
    
    # Rename columns to match schema
    column_mapping = {
        'temp_c': 'temperature_c',
        'humidity_pct': 'humidity_pct',
        'precip_mm': 'precipitation_mm',
        'wind_dir_deg': 'wind_direction_deg',
        'lat': 'latitude',
        'lon': 'longitude',
        'data_source': 'csv_source'  # Rename to avoid conflict
    }
    df = df.rename(columns=column_mapping)
    
    # Override with our data_source
    df['data_source'] = 'open-meteo'
    
    # Select columns that exist in schema
    schema_cols = ['timestamp_utc', 'location', 'latitude', 'longitude',
                   'temperature_c', 'feels_like_c', 'dew_point_c',
                   'humidity_pct', 'precipitation_mm', 'rain_mm', 'snow_cm', 'snow_depth_m',
                   'pressure_msl_hpa', 'surface_pressure_hpa',
                   'wind_speed_ms', 'wind_direction_deg', 'wind_gust_ms',
                   'cloud_cover_pct', 'weather_code',
                   'data_source', 'source_file']
    
    df = df[[col for col in schema_cols if col in df.columns]]
    
    # Remove duplicates
    df = df.drop_duplicates(subset=['timestamp_utc', 'location', 'data_source'], keep='first')
    df = df.sort_values('timestamp_utc').reset_index(drop=True)
    print(f"📊 After deduplication: {len(df):,} records")
    
    # Insert into weather table using chunked inserts
    count = insert_dataframe(df, 'weather', engine)
    print(f"✅ Inserted {count:,} weather records")

def create_unified_data(engine):
    """Join measurements + weather to create ML-ready unified_data table"""
    print("\n" + "="*60)
    print("STEP 5: Creating unified_data (ML-ready)")
    print("="*60)
    
    # SQL query to join measurements + weather
    query = """
    WITH hourly_measurements AS (
        SELECT 
            DATE_TRUNC('hour', timestamp_utc) as timestamp_utc,
            location,
            parameter,
            AVG(value) as value,
            MAX(data_source) as data_source
        FROM measurements
        WHERE location = 'Astana'
        GROUP BY DATE_TRUNC('hour', timestamp_utc), location, parameter
    ),
    pivoted_measurements AS (
        SELECT 
            timestamp_utc,
            location,
            MAX(CASE WHEN parameter = 'pm25' THEN value END) as pm25,
            MAX(CASE WHEN parameter = 'pm10' THEN value END) as pm10,
            MAX(CASE WHEN parameter = 'no2' THEN value END) as no2,
            MAX(CASE WHEN parameter = 'o3' THEN value END) as o3,
            MAX(CASE WHEN parameter = 'so2' THEN value END) as so2,
            MAX(CASE WHEN parameter = 'co' THEN value END) as co,
            MAX(CASE WHEN parameter = 'pm25' THEN data_source END) as pm25_source
        FROM hourly_measurements
        GROUP BY timestamp_utc, location
    ),
    hourly_weather AS (
        SELECT 
            DATE_TRUNC('hour', timestamp_utc) as timestamp_utc,
            location,
            AVG(temperature_c) as temperature_c,
            AVG(humidity_pct) as humidity_pct,
            AVG(surface_pressure_hpa) as pressure_hpa,
            AVG(wind_speed_ms) as wind_speed_ms,
            AVG(wind_direction_deg) as wind_direction_deg,
            AVG(precipitation_mm) as precipitation_mm,
            AVG(cloud_cover_pct) as cloud_cover_pct,
            MAX(data_source) as weather_source
        FROM weather
        WHERE location = 'Astana'
        GROUP BY DATE_TRUNC('hour', timestamp_utc), location
    )
    SELECT 
        COALESCE(m.timestamp_utc, w.timestamp_utc) as timestamp_utc,
        COALESCE(m.location, w.location) as location,
        m.pm25,
        m.pm10,
        m.no2,
        m.o3,
        m.so2,
        m.co,
        w.temperature_c,
        w.humidity_pct,
        w.pressure_hpa,
        w.wind_speed_ms,
        w.wind_direction_deg,
        w.precipitation_mm,
        w.cloud_cover_pct,
        
        -- Temporal features (use COALESCE for timestamp)
        EXTRACT(HOUR FROM COALESCE(m.timestamp_utc, w.timestamp_utc))::int as hour,
        EXTRACT(DOW FROM COALESCE(m.timestamp_utc, w.timestamp_utc))::int as day_of_week,
        EXTRACT(DAY FROM COALESCE(m.timestamp_utc, w.timestamp_utc))::int as day_of_month,
        EXTRACT(MONTH FROM COALESCE(m.timestamp_utc, w.timestamp_utc))::int as month,
        CASE 
            WHEN EXTRACT(MONTH FROM COALESCE(m.timestamp_utc, w.timestamp_utc)) IN (12, 1, 2) THEN 'winter'
            WHEN EXTRACT(MONTH FROM COALESCE(m.timestamp_utc, w.timestamp_utc)) IN (3, 4, 5) THEN 'spring'
            WHEN EXTRACT(MONTH FROM COALESCE(m.timestamp_utc, w.timestamp_utc)) IN (6, 7, 8) THEN 'summer'
            ELSE 'autumn'
        END as season,
        CASE WHEN EXTRACT(DOW FROM COALESCE(m.timestamp_utc, w.timestamp_utc)) IN (0, 6) THEN true ELSE false END as is_weekend,
        CASE WHEN EXTRACT(MONTH FROM COALESCE(m.timestamp_utc, w.timestamp_utc)) IN (10, 11, 12, 1, 2, 3, 4) THEN true ELSE false END as is_heating_season,
        
        m.pm25_source,
        w.weather_source,
        
        -- Completeness score (0.0 to 1.0)
        ROUND(
            (CASE WHEN m.pm25 IS NOT NULL THEN 0.3 ELSE 0.0 END +
             CASE WHEN w.temperature_c IS NOT NULL THEN 0.2 ELSE 0.0 END +
             CASE WHEN w.humidity_pct IS NOT NULL THEN 0.15 ELSE 0.0 END +
             CASE WHEN w.wind_speed_ms IS NOT NULL THEN 0.15 ELSE 0.0 END +
             CASE WHEN w.pressure_hpa IS NOT NULL THEN 0.1 ELSE 0.0 END +
             CASE WHEN m.pm10 IS NOT NULL THEN 0.1 ELSE 0.0 END)::numeric,
            2
        ) as completeness_score
    FROM pivoted_measurements m
    FULL OUTER JOIN hourly_weather w 
        ON m.timestamp_utc = w.timestamp_utc AND m.location = w.location
    ORDER BY COALESCE(m.timestamp_utc, w.timestamp_utc)
    """
    
    df = pd.read_sql(query, engine)
    print(f"📊 Created {len(df):,} unified records")
    
    # Insert into unified_data using chunked inserts
    count = insert_dataframe(df, 'unified_data', engine)
    print(f"✅ Inserted {count:,} records into unified_data")
    
    # Show completeness stats
    completeness_stats = df['completeness_score'].describe()
    print(f"\n📈 Completeness Statistics:")
    print(f"   Mean: {completeness_stats['mean']:.2f}")
    print(f"   Median: {completeness_stats['50%']:.2f}")
    print(f"   Min: {completeness_stats['min']:.2f}")
    print(f"   Max: {completeness_stats['max']:.2f}")
    
    # Show date range
    print(f"\n📅 Date Range:")
    print(f"   From: {df['timestamp_utc'].min()}")
    print(f"   To: {df['timestamp_utc'].max()}")

def verify_normalized_data(engine):
    """Verify the normalized data"""
    print("\n" + "="*60)
    print("VERIFICATION REPORT")
    print("="*60)
    
    with engine.connect() as conn:
        # Measurements
        result = conn.execute(text("SELECT COUNT(*) FROM measurements")).fetchone()
        print(f"\n📊 measurements: {result[0]:,} records")
        
        param_counts = pd.read_sql(text("""
            SELECT parameter, COUNT(*) as count, data_source
            FROM measurements
            GROUP BY parameter, data_source
            ORDER BY parameter, data_source
        """), conn)
        print("\nBy parameter and source:")
        print(param_counts.to_string(index=False))
        
        # Weather
        result = conn.execute(text("SELECT COUNT(*) FROM weather")).fetchone()
        print(f"\n📊 weather: {result[0]:,} records")
        
        # Unified data
        result = conn.execute(text("SELECT COUNT(*) FROM unified_data")).fetchone()
        print(f"\n📊 unified_data: {result[0]:,} records")
        
        # Completeness distribution
        completeness = pd.read_sql(text("""
            SELECT 
                CASE 
                    WHEN completeness_score >= 0.8 THEN 'Excellent (>=0.8)'
                    WHEN completeness_score >= 0.6 THEN 'Good (0.6-0.8)'
                    WHEN completeness_score >= 0.4 THEN 'Fair (0.4-0.6)'
                    ELSE 'Poor (<0.4)'
                END as quality,
                COUNT(*) as count,
                ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM unified_data
            GROUP BY quality
            ORDER BY quality DESC
        """), conn)
        print("\n📈 Data Quality Distribution:")
        print(completeness.to_string(index=False))

def main():
    engine = get_engine()
    
    print("\n" + "="*60)
    print("AAQIS ETL PIPELINE: Data Normalization")
    print("="*60)
    
    # Step 1: Create schema
    create_normalized_schema(engine)
    
    # Step 2-4: Transform raw data
    transform_openaq(engine)
    transform_cams(engine)
    transform_weather(engine)
    
    # Step 5: Create unified dataset
    create_unified_data(engine)
    
    # Step 6: Verify
    verify_normalized_data(engine)
    
    print("\n" + "="*60)
    print("✅ ETL PIPELINE COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("  1. Check 'unified_data' table for ML-ready dataset")
    print("  2. Run EDA notebook: notebooks/01_exploratory_data_analysis.ipynb")
    print("  3. Train ML models using unified_data")

if __name__ == "__main__":
    main()
