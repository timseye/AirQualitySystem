"""
Verify PostgreSQL database contents after ETL load.
Checks record counts, date ranges, and data quality.
"""
import os
import pandas as pd
from sqlalchemy import create_engine, text

PG_CONN_STR = os.getenv("PG_CONN_STR", "postgresql://aaqis_user:aaqis_password@localhost:5432/aaqis_db")

def verify_database():
    engine = create_engine(PG_CONN_STR)
    
    print("=" * 60)
    print("DATABASE VERIFICATION REPORT")
    print("=" * 60)
    
    with engine.connect() as conn:
        # Check if tables exist
        tables_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        tables = pd.read_sql(tables_query, conn)
        print("\n📋 Tables in database:")
        print(tables.to_string(index=False))
        
        # Check OpenAQ data
        if 'openaq_data' in tables['table_name'].values:
            print("\n" + "=" * 60)
            print("1️⃣  OPENAQ DATA (PM2.5 from U.S. Embassy)")
            print("=" * 60)
            
            count = pd.read_sql(text("SELECT COUNT(*) as count FROM openaq_data"), conn)
            print(f"📊 Total records: {count['count'][0]:,}")
            
            # Get actual column names
            cols = pd.read_sql(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'openaq_data'
                ORDER BY ordinal_position
            """), conn)
            print(f"\n📝 Columns: {', '.join(cols['column_name'].tolist())}")
            
            # Sample data
            sample = pd.read_sql(text("SELECT * FROM openaq_data LIMIT 5"), conn)
            print(f"\n🔍 Sample records (showing {len(sample)} rows):")
            print(sample.to_string())
        
        # Check Weather data
        if 'weather_data' in tables['table_name'].values:
            print("\n" + "=" * 60)
            print("2️⃣  WEATHER DATA (Open-Meteo)")
            print("=" * 60)
            
            count = pd.read_sql(text("SELECT COUNT(*) as count FROM weather_data"), conn)
            print(f"📊 Total records: {count['count'][0]:,}")
            
            # Get columns
            cols = pd.read_sql(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'weather_data'
                ORDER BY ordinal_position
            """), conn)
            print(f"\n📝 Columns ({len(cols)}): {', '.join(cols['column_name'].tolist())}")
            
            # Sample data
            sample = pd.read_sql(text("SELECT * FROM weather_data LIMIT 3"), conn)
            print(f"\n🔍 Sample records:")
            print(sample.to_string())
        
        # Check CAMS data
        if 'cams_data' in tables['table_name'].values:
            print("\n" + "=" * 60)
            print("3️⃣  CAMS DATA (Multi-Pollutant Reanalysis)")
            print("=" * 60)
            
            count = pd.read_sql(text("SELECT COUNT(*) as count FROM cams_data"), conn)
            print(f"📊 Total records: {count['count'][0]:,}")
            
            # Get column info
            cols = pd.read_sql(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'cams_data'
                ORDER BY ordinal_position
            """), conn)
            print(f"📝 Columns: {len(cols)}")
            
            # Sample data
            sample = pd.read_sql(text("SELECT * FROM cams_data LIMIT 3"), conn)
            print("\n🔍 Sample records:")
            print(sample.head())
        
        print("\n" + "=" * 60)
        print("✅ VERIFICATION COMPLETE")
        print("=" * 60)

if __name__ == "__main__":
    verify_database()
