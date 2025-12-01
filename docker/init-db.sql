-- ===========================================
-- AAQIS Database Initialization Script
-- Creates the unified_data table with sample data
-- ===========================================

-- Create unified_data table if not exists
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

-- Insert sample data if table is empty
-- This provides demo data for the dashboard
INSERT INTO unified_data (
    timestamp_utc, location, pm25, pm10, temperature_c, humidity_pct, 
    pressure_hpa, wind_speed_ms, hour, month, season, is_weekend, is_heating_season,
    pm25_source, weather_source, completeness_score
)
SELECT 
    generate_series(
        '2024-01-01 00:00:00'::timestamp,
        '2025-03-04 11:00:00'::timestamp,
        '1 hour'::interval
    ) as timestamp_utc,
    'Astana' as location,
    -- PM2.5 with seasonal and diurnal patterns
    GREATEST(1, 
        15 + 
        10 * sin(2 * pi() * (EXTRACT(MONTH FROM generate_series) - 1) / 12) + -- seasonal
        5 * sin(2 * pi() * (EXTRACT(HOUR FROM generate_series) - 8) / 24) + -- diurnal
        random() * 10 -- noise
    )::decimal(10,2) as pm25,
    -- PM10
    GREATEST(1,
        25 + 
        15 * sin(2 * pi() * (EXTRACT(MONTH FROM generate_series) - 1) / 12) +
        random() * 15
    )::decimal(10,2) as pm10,
    -- Temperature (seasonal)
    (5 - 25 * cos(2 * pi() * (EXTRACT(MONTH FROM generate_series) - 1) / 12) + random() * 5)::decimal(5,2) as temperature_c,
    -- Humidity
    (60 + 20 * sin(2 * pi() * (EXTRACT(MONTH FROM generate_series) - 7) / 12) + random() * 10)::decimal(5,2) as humidity_pct,
    -- Pressure
    (1013 + random() * 30 - 15)::decimal(7,2) as pressure_hpa,
    -- Wind speed
    (5 + random() * 10)::decimal(5,2) as wind_speed_ms,
    -- Hour
    EXTRACT(HOUR FROM generate_series)::integer as hour,
    -- Month
    EXTRACT(MONTH FROM generate_series)::integer as month,
    -- Season
    CASE 
        WHEN EXTRACT(MONTH FROM generate_series) IN (12, 1, 2) THEN 'winter'
        WHEN EXTRACT(MONTH FROM generate_series) IN (3, 4, 5) THEN 'spring'
        WHEN EXTRACT(MONTH FROM generate_series) IN (6, 7, 8) THEN 'summer'
        ELSE 'autumn'
    END as season,
    -- Is weekend
    EXTRACT(DOW FROM generate_series) IN (0, 6) as is_weekend,
    -- Is heating season (Oct-Apr)
    EXTRACT(MONTH FROM generate_series) IN (1, 2, 3, 4, 10, 11, 12) as is_heating_season,
    -- Sources
    'demo' as pm25_source,
    'demo' as weather_source,
    0.95 as completeness_score
FROM generate_series(
    '2024-01-01 00:00:00'::timestamp,
    '2025-03-04 11:00:00'::timestamp,
    '1 hour'::interval
) 
WHERE NOT EXISTS (SELECT 1 FROM unified_data LIMIT 1);

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'AAQIS database initialized successfully!';
    RAISE NOTICE 'Total records in unified_data: %', (SELECT COUNT(*) FROM unified_data);
END $$;
