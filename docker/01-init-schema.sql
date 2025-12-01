-- ===========================================
-- AAQIS Database Initialization Script
-- Creates the unified_data table structure
-- Data is loaded from seed_data.sql.gz
-- ===========================================

-- Create unified_data table
CREATE TABLE IF NOT EXISTS unified_data (
    id SERIAL PRIMARY KEY,
    timestamp_utc TIMESTAMP NOT NULL,
    location VARCHAR(100) DEFAULT 'Astana',
    
    -- Air Quality Parameters
    pm25 DECIMAL(10, 2),
    pm10 DECIMAL(10, 2),
    no2 DECIMAL(10, 4),
    o3 DECIMAL(10, 4),
    so2 DECIMAL(10, 4),
    co DECIMAL(10, 4),
    
    -- Weather Parameters
    temperature_c DECIMAL(5, 2),
    humidity_pct DECIMAL(5, 2),
    pressure_hpa DECIMAL(7, 2),
    wind_speed_ms DECIMAL(5, 2),
    wind_direction_deg DECIMAL(5, 2),
    precipitation_mm DECIMAL(5, 2),
    cloud_cover_pct DECIMAL(5, 2),
    
    -- Temporal Features
    hour INTEGER,
    day_of_week INTEGER,
    day_of_month INTEGER,
    month INTEGER,
    season VARCHAR(20),
    is_weekend BOOLEAN,
    is_heating_season BOOLEAN,
    
    -- Data Source Tracking
    pm25_source VARCHAR(50),
    weather_source VARCHAR(50),
    completeness_score DECIMAL(5, 4),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_unified_data_timestamp ON unified_data(timestamp_utc);
CREATE INDEX IF NOT EXISTS idx_unified_data_pm25 ON unified_data(pm25);
CREATE INDEX IF NOT EXISTS idx_unified_data_month ON unified_data(month);
CREATE INDEX IF NOT EXISTS idx_unified_data_hour ON unified_data(hour);

-- Log
DO $$
BEGIN
    RAISE NOTICE 'AAQIS: Table unified_data created successfully';
END $$;
