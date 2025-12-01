-- ============================================================================
-- Normalized Schema for AAQIS (Air Quality Intelligence System)
-- Purpose: Create clean, normalized tables for ML and analysis
-- ============================================================================

-- Drop existing normalized tables if they exist
DROP TABLE IF EXISTS unified_data CASCADE;
DROP TABLE IF EXISTS weather CASCADE;
DROP TABLE IF EXISTS measurements CASCADE;

-- ============================================================================
-- 1. MEASUREMENTS TABLE (Normalized Air Quality Data)
-- Combines OpenAQ + CAMS into single time-series format
-- ============================================================================
CREATE TABLE measurements (
    id SERIAL PRIMARY KEY,
    timestamp_utc TIMESTAMP NOT NULL,
    location VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    parameter VARCHAR(50) NOT NULL,  -- pm25, pm10, no2, o3, so2, co
    value DECIMAL(12,6) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    data_source VARCHAR(50) NOT NULL,  -- openaq, cams
    data_quality VARCHAR(20),
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for fast queries
CREATE INDEX idx_measurements_timestamp ON measurements(timestamp_utc);
CREATE INDEX idx_measurements_parameter ON measurements(parameter);
CREATE INDEX idx_measurements_location ON measurements(location);
CREATE INDEX idx_measurements_composite ON measurements(timestamp_utc, location, parameter);

-- Unique constraint to prevent duplicates
CREATE UNIQUE INDEX idx_measurements_unique 
ON measurements(timestamp_utc, location, parameter, data_source);

COMMENT ON TABLE measurements IS 'Normalized air quality measurements from all sources';


-- ============================================================================
-- 2. WEATHER TABLE (Normalized Meteorological Data)
-- From Open-Meteo
-- ============================================================================
CREATE TABLE weather (
    id SERIAL PRIMARY KEY,
    timestamp_utc TIMESTAMP NOT NULL,
    location VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    
    -- Temperature metrics
    temperature_c DECIMAL(5,2),
    feels_like_c DECIMAL(5,2),
    dew_point_c DECIMAL(5,2),
    
    -- Humidity and precipitation
    humidity_pct INTEGER,
    precipitation_mm DECIMAL(6,2),
    rain_mm DECIMAL(6,2),
    snow_cm DECIMAL(6,2),
    snow_depth_m DECIMAL(6,2),
    
    -- Pressure
    pressure_msl_hpa DECIMAL(7,2),
    surface_pressure_hpa DECIMAL(7,2),
    
    -- Wind
    wind_speed_ms DECIMAL(5,2),
    wind_direction_deg INTEGER,
    wind_gust_ms DECIMAL(5,2),
    
    -- Other
    cloud_cover_pct INTEGER,
    weather_code INTEGER,
    
    data_source VARCHAR(50) NOT NULL,
    source_file VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_weather_timestamp ON weather(timestamp_utc);
CREATE INDEX idx_weather_location ON weather(location);

-- Unique constraint
CREATE UNIQUE INDEX idx_weather_unique 
ON weather(timestamp_utc, location, data_source);

COMMENT ON TABLE weather IS 'Normalized meteorological data from Open-Meteo';


-- ============================================================================
-- 3. UNIFIED_DATA TABLE (ML-Ready Dataset)
-- Combines measurements + weather for machine learning
-- One row per timestamp with all features
-- ============================================================================
CREATE TABLE unified_data (
    id SERIAL PRIMARY KEY,
    timestamp_utc TIMESTAMP NOT NULL,
    location VARCHAR(100) NOT NULL,
    
    -- Air Quality Pollutants
    pm25 DECIMAL(12,6),
    pm10 DECIMAL(12,6),
    no2 DECIMAL(12,6),
    o3 DECIMAL(12,6),
    so2 DECIMAL(12,6),
    co DECIMAL(12,6),
    
    -- Weather Features
    temperature_c DECIMAL(5,2),
    humidity_pct INTEGER,
    pressure_hpa DECIMAL(7,2),
    wind_speed_ms DECIMAL(5,2),
    wind_direction_deg INTEGER,
    precipitation_mm DECIMAL(6,2),
    cloud_cover_pct INTEGER,
    
    -- Temporal Features (for ML)
    hour INTEGER,
    day_of_week INTEGER,  -- 0=Monday, 6=Sunday
    day_of_month INTEGER,
    month INTEGER,
    season VARCHAR(10),  -- winter, spring, summer, autumn
    is_weekend BOOLEAN,
    is_heating_season BOOLEAN,  -- Oct-Apr for Astana
    
    -- Data Completeness
    pm25_source VARCHAR(50),
    weather_source VARCHAR(50),
    completeness_score DECIMAL(3,2),  -- 0.0 to 1.0
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_unified_timestamp ON unified_data(timestamp_utc);
CREATE INDEX idx_unified_location ON unified_data(location);
CREATE INDEX idx_unified_pm25 ON unified_data(pm25) WHERE pm25 IS NOT NULL;
CREATE INDEX idx_unified_complete ON unified_data(completeness_score) 
WHERE completeness_score >= 0.8;

-- Unique constraint
CREATE UNIQUE INDEX idx_unified_unique 
ON unified_data(timestamp_utc, location);

COMMENT ON TABLE unified_data IS 'ML-ready unified dataset with all features';


-- ============================================================================
-- 4. HELPER VIEWS
-- ============================================================================

-- View: Latest measurements (last 24 hours)
CREATE OR REPLACE VIEW v_latest_measurements AS
SELECT 
    timestamp_utc,
    location,
    parameter,
    value,
    unit,
    data_source
FROM measurements
WHERE timestamp_utc >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp_utc DESC, parameter;

COMMENT ON VIEW v_latest_measurements IS 'Air quality measurements from last 24 hours';


-- View: Daily averages
CREATE OR REPLACE VIEW v_daily_averages AS
SELECT 
    DATE(timestamp_utc) as date,
    location,
    parameter,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value,
    COUNT(*) as measurement_count
FROM measurements
GROUP BY DATE(timestamp_utc), location, parameter
ORDER BY date DESC, parameter;

COMMENT ON VIEW v_daily_averages IS 'Daily aggregated air quality statistics';


-- View: Data quality report
CREATE OR REPLACE VIEW v_data_quality AS
SELECT 
    data_source,
    parameter,
    COUNT(*) as total_records,
    COUNT(CASE WHEN value IS NOT NULL THEN 1 END) as valid_records,
    ROUND(100.0 * COUNT(CASE WHEN value IS NOT NULL THEN 1 END) / COUNT(*), 2) as completeness_pct,
    MIN(timestamp_utc) as first_record,
    MAX(timestamp_utc) as last_record
FROM measurements
GROUP BY data_source, parameter
ORDER BY data_source, parameter;

COMMENT ON VIEW v_data_quality IS 'Data quality metrics by source and parameter';


-- ============================================================================
-- 5. GRANT PERMISSIONS
-- ============================================================================
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO aaqis_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO aaqis_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO aaqis_user;


-- ============================================================================
-- SCHEMA CREATION COMPLETE
-- ============================================================================
