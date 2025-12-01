# Data Collection and Database Loading Log
## Diploma Thesis: Air Quality Intelligence System (AAQIS)

**Author:** timseye  
**University:** Astana IT University  
**Date:** November 30 - December 1, 2025  
**Purpose:** Complete technical log of data pipeline for thesis Chapter 3 (Methodology)

> **Related Documentation:**
> - [Implementation Log](implementation_log.md) - Django backend & frontend implementation
> - [README](../README.md) - Project overview and quick start
> - [TODO](../TODO.md) - Project status and roadmap

---

## Table of Contents
1. [Project Overview](#1-project-overview)
2. [Data Sources Summary](#2-data-sources-summary)
3. [Environment Setup](#3-environment-setup)
4. [Data Collection Phase](#4-data-collection-phase)
5. [Database Setup](#5-database-setup)
6. [ETL Pipeline v1 (Initial Loading)](#6-etl-pipeline-v1-initial-loading)
7. [ETL Pipeline v2 (Normalization)](#7-etl-pipeline-v2-normalization)
8. [Final Database Schema](#8-final-database-schema)
9. [Data Quality Report](#9-data-quality-report)
10. [Scripts Reference](#10-scripts-reference)
11. [Troubleshooting Log](#11-troubleshooting-log)
12. [Reproducibility Guide](#12-reproducibility-guide)
13. [Next Steps](#13-next-steps)

---

## 1. Project Overview

### 1.1 Research Goal
Develop an AI-powered air quality forecasting system for Astana using:
- Historical PM2.5/PM10 data
- Meteorological parameters
- LSTM and SVR machine learning models

### 1.2 Data Requirements
| Requirement | Solution |
|-------------|----------|
| PM2.5 ground-truth | OpenAQ (US Embassy sensor) |
| Multi-pollutant data | CAMS reanalysis (PM2.5, PM10, NO2, O3, SO2, CO) |
| Weather features | Open-Meteo historical API |
| Time period | 2018-2025 (7+ years) |
| Temporal resolution | Hourly |

### 1.3 Technology Stack
- **Database:** PostgreSQL 14
- **Language:** Python 3.12
- **ML Framework:** TensorFlow/Keras, scikit-learn
- **Web Framework:** Django 4.x
- **Data Processing:** pandas, xarray, SQLAlchemy

---

## 2. Data Sources Summary

### Final Dataset Statistics (December 1, 2025)

| Source | Table | Records | Period | Parameters |
|--------|-------|---------|--------|------------|
| OpenAQ | measurements | 24,746 | Jul 2018 - Mar 2025 | PM2.5 |
| CAMS | measurements | 40,912 | Jan 2018 - Dec 2024 | PM2.5, PM10 |
| Open-Meteo | weather | 69,192 | Jan 2018 - Nov 2025 | 15+ weather vars |
| **Unified** | unified_data | **69,192** | Jan 2018 - Nov 2025 | All features |

### Data Quality Summary
- **Excellent (≥90% complete):** 54.1% of records
- **Fair (50-70% complete):** 45.9% of records
- **Total coverage:** ~7 years of hourly data

---

## 3. Environment Setup

### 3.1 Virtual Environment
```bash
# Location
/home/timseye/AirQualitySystem/.venv

# Activation
cd /home/timseye/AirQualitySystem
source .venv/bin/activate

# Python version
python --version  # Python 3.12.x
```

### 3.2 Required Python Packages

**For Data Collection:**
```bash
pip install requests pandas cdsapi
```

**For NetCDF Processing (CAMS):**
```bash
pip install xarray h5netcdf netCDF4 cfgrib
```

**For Database Operations:**
```bash
pip install sqlalchemy psycopg2-binary
```

**Complete Installation:**
```bash
pip install requests pandas cdsapi xarray h5netcdf netCDF4 cfgrib sqlalchemy psycopg2-binary
```

### 3.3 Package Notes
| Package | Purpose | Note |
|---------|---------|------|
| `requests` | HTTP API calls | OpenAQ, Open-Meteo |
| `pandas` | DataFrame operations | Core data manipulation |
| `cdsapi` | CAMS API client | Requires ~/.cdsapirc |
| `xarray` | NetCDF reading | Multi-dimensional arrays |
| `h5netcdf` | NetCDF4 backend | Required by xarray |
| `netCDF4` | Alternative backend | Fallback option |
| `sqlalchemy` | Database ORM | PostgreSQL abstraction |
| `psycopg2-binary` | PostgreSQL adapter | Pre-compiled, no libpq-dev needed |

---

## 4. Data Collection Phase

### 4.1 OpenAQ Historical Data (PM2.5)

**Source:** U.S. Embassy Air Quality Monitor, Astana  
**API:** OpenAQ v3 API (https://api.openaq.org/v3)  
**Script:** `scripts/collect_openaq_historical.py`

**API Configuration:**
```python
API_KEY = "c5fb53161f8c1a4a07723fbb9a025c04b61471501b7c7f6b4839def76e1b08bd"
BASE_URL = "https://api.openaq.org/v3"
LOCATION_ID = 7094  # US Embassy Astana
SENSOR_ID = 20512   # PM2.5 sensor
```

**Execution:**
```bash
source .venv/bin/activate
python scripts/collect_openaq_historical.py
```

**Collection Logic:**
1. Paginated API requests (1000 records per page)
2. Iterate through all pages until no more data
3. Parse JSON response → structured records
4. Save to CSV with deduplication

**Output:**
- **File:** `data/raw/openaq/openaq_astana_historical.csv`
- **Records:** 29,012 (raw), 24,746 (after cleaning)
- **Period:** 2018-07-27 to 2025-03-04
- **Gap:** 2020-2021 (station temporarily offline)

**CSV Structure:**
```csv
timestamp_utc,timestamp_local,city,country_code,location_id,sensor_id,parameter,value,units,data_quality
2018-07-27T16:00:00Z,2018-07-27T22:00:00+06:00,Astana,KZ,7094,20512,pm25,31.0,µg/m³,OK
```

---

### 4.2 Open-Meteo Weather Data

**Source:** Open-Meteo Historical Archive API  
**API:** https://archive-api.open-meteo.com/v1/archive  
**Script:** `scripts/collect_openmeteo_weather.py`

**No API Key Required** (free service)

**API Parameters:**
```python
ASTANA_LAT = 51.1694
ASTANA_LON = 71.4491
TIMEZONE = "Asia/Almaty"

HOURLY_PARAMS = [
    "temperature_2m",
    "relative_humidity_2m",
    "dew_point_2m",
    "apparent_temperature",
    "precipitation",
    "rain",
    "snowfall",
    "snow_depth",
    "weather_code",
    "pressure_msl",
    "surface_pressure",
    "cloud_cover",
    "wind_speed_10m",
    "wind_direction_10m",
    "wind_gusts_10m"
]
```

**Execution:**
```bash
python scripts/collect_openmeteo_weather.py
```

**Collection Logic:**
1. Split request into 700-day chunks (API limit ~2 years)
2. Iterate through chunks: 2018-01-01 → present
3. Concatenate all DataFrames
4. Save to CSV

**Output:**
- **File:** `data/raw/openmeteo/astana_weather_historical.csv`
- **Records:** 69,192 hourly measurements
- **Period:** 2018-01-01 to 2025-11-22
- **Size:** ~5 MB

**CSV Structure:**
```csv
timestamp_local,temp_c,humidity_pct,dew_point_c,feels_like_c,precip_mm,rain_mm,snow_cm,snow_depth_m,weather_code,pressure_msl_hpa,surface_pressure_hpa,cloud_cover_pct,wind_speed_ms,wind_dir_deg,wind_gust_ms,city,country_code,lat,lon,data_source
2018-01-01T00:00:00,-18.5,82,-21.3,-25.1,0.0,0.0,0.0,0.15,3,1032.1,996.5,75,3.2,270,5.8,Astana,KZ,51.1694,71.4491,open-meteo
```

---

### 4.3 CAMS Reanalysis Data (Multi-Pollutant)

**Source:** Copernicus Atmosphere Monitoring Service (CAMS)  
**Dataset:** CAMS Global Reanalysis (EAC4)  
**API:** Climate Data Store (CDS) API  
**Script:** `scripts/download_cams_all.py`

#### 4.3.1 Prerequisites

**1. Register at Copernicus:**
- URL: https://ads.atmosphere.copernicus.eu/
- Accept license terms for "CAMS Global Reanalysis (EAC4)"

**2. Get API Key:**
- Profile → API Key → Copy key

**3. Create API Config:**
```bash
nano ~/.cdsapirc
```

**Content:**
```ini
url: https://ads.atmosphere.copernicus.eu/api
key: bd8ec9b0-437a-413a-9358-2b7d028b3a67
```

#### 4.3.2 Download Configuration

**Spatial Coverage (Astana region):**
```python
ASTANA_BBOX = {
    "north": 52.5,
    "west": 70.0,
    "south": 50.5,
    "east": 73.0
}
```

**Temporal Coverage:**
- Years: 2018-2024 (7 years)
- Quarters: Q1, Q2, Q3, Q4 per year
- Times: 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00

**Variables Downloaded:**

| Type | Variables | Level |
|------|-----------|-------|
| Surface (PM) | particulate_matter_2.5um, particulate_matter_10um | Single level |
| Gases | nitrogen_dioxide, ozone, sulphur_dioxide, carbon_monoxide | 1000 hPa (surface) |

#### 4.3.3 Execution

```bash
# Run in background (takes 2-3 hours)
nohup python scripts/download_cams_all.py > cams_download.log 2>&1 &

# Monitor progress
tail -f cams_download.log
ls data/raw/cams/*.zip | wc -l  # Check file count
```

#### 4.3.4 Output

**Directory:** `data/raw/cams/`

**File Naming Convention:**
```
cams_astana_YYYY_qN_pm.nc.zip   # PM2.5, PM10
cams_astana_YYYY_qN_gas.nc.zip  # NO2, O3, SO2, CO
```

**Files Generated:**
- **Total:** 58 NetCDF zip files
- **Per Year:** 8 files (4 quarters × 2 types)
- **Size:** ~60 MB total (compressed)
- **Period:** 2018-2024

**Example File Structure:**
```bash
$ unzip -l data/raw/cams/cams_astana_2024_q1_pm.nc.zip
Archive:  cams_astana_2024_q1_pm.nc.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
    57916  2025-11-29 18:59   data_sfc.nc
```

---

## 5. Database Setup

### 5.1 PostgreSQL Information

**Pre-existing Database (Django project):**
```
Database: aaqis_db
User: aaqis_user
Password: aaqis_password
Host: localhost
Port: 5432
```

**Credentials Location:** `src/core/settings.py` (line 79)

### 5.2 Connection String

**Format:**
```
postgresql://USER:PASSWORD@HOST:PORT/DATABASE
```

**Our Connection:**
```bash
export PG_CONN_STR="postgresql://aaqis_user:aaqis_password@localhost:5432/aaqis_db"
```

### 5.3 Database Verification

```bash
# Check database exists
sudo -u postgres psql -l

# Output:
#    Name    |   Owner    | Encoding 
# -----------+------------+----------
#  aaqis_db  | aaqis_user | UTF8     
```

### 5.4 Manual Database Creation (if needed)

```sql
-- Connect as postgres superuser
sudo -u postgres psql

-- Create database and user
CREATE DATABASE aaqis_db;
CREATE USER aaqis_user WITH PASSWORD 'aaqis_password';
GRANT ALL PRIVILEGES ON DATABASE aaqis_db TO aaqis_user;

-- Exit
\q
```

---

## 6. ETL Pipeline v1 (Initial Loading)

**Script:** `scripts/load_all_to_postgres.py`  
**Purpose:** Initial bulk load of raw data (deprecated, replaced by v2)

### 6.1 What It Did
1. Load OpenAQ CSV → `openaq_data` table
2. Load Open-Meteo CSV → `weather_data` table  
3. Load CAMS NetCDF → `cams_data` table

### 6.2 Issues Encountered
- Created wide-format tables (thousands of columns)
- pandas `to_sql(method='multi')` caused column explosion
- Not normalized for ML workflows

**Status:** ❌ Deprecated - Use ETL Pipeline v2 instead

---

## 7. ETL Pipeline v2 (Normalization)

**Script:** `scripts/normalize_data.py`  
**SQL Schema:** `scripts/create_normalized_schema.sql`  
**Purpose:** Create ML-ready normalized database structure

### 7.1 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    RAW DATA SOURCES                         │
├─────────────────────────────────────────────────────────────┤
│  OpenAQ CSV    │   CAMS NetCDF   │   Open-Meteo CSV        │
│  (29,012 rows) │   (58 files)     │   (69,192 rows)         │
└───────┬────────┴────────┬─────────┴────────┬───────────────┘
        │                 │                   │
        ▼                 ▼                   ▼
┌─────────────────────────────────────────────────────────────┐
│              TRANSFORM (normalize_data.py)                   │
├─────────────────────────────────────────────────────────────┤
│  • Read CSV/NetCDF files                                    │
│  • Standardize column names                                 │
│  • Convert timestamps to UTC                                │
│  • Remove duplicates & invalid values                       │
│  • Aggregate CAMS grid to single point                      │
│  • Melt wide format → long format                           │
└───────┬────────────────────────────────────┬────────────────┘
        │                                    │
        ▼                                    ▼
┌───────────────────────┐    ┌──────────────────────────────┐
│   measurements        │    │   weather                     │
│   (65,658 records)    │    │   (69,192 records)           │
│   - PM2.5 (openaq)    │    │   - temperature              │
│   - PM2.5 (cams)      │    │   - humidity                 │
│   - PM10 (cams)       │    │   - wind, pressure, etc.     │
└───────────┬───────────┘    └──────────────┬───────────────┘
            │                               │
            └───────────┬───────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │        unified_data               │
        │        (69,192 records)           │
        │                                   │
        │  ML-Ready Features:               │
        │  • pm25, pm10                     │
        │  • temperature, humidity          │
        │  • wind_speed, pressure           │
        │  • hour, day_of_week, month       │
        │  • season, is_weekend             │
        │  • is_heating_season              │
        │  • completeness_score             │
        └───────────────────────────────────┘
```

### 7.2 Execution

```bash
# Set connection string
export PG_CONN_STR="postgresql://aaqis_user:aaqis_password@localhost:5432/aaqis_db"

# Run normalization pipeline
python scripts/normalize_data.py
```

### 7.3 Pipeline Steps

**Step 1: Create Schema**
- Drops existing tables (clean slate)
- Creates `measurements`, `weather`, `unified_data` tables
- Creates indexes and unique constraints

**Step 2: Transform OpenAQ → measurements**
- Read CSV files from `data/raw/openaq/`
- Standardize column names (`units` → `unit`)
- Convert timestamps to UTC (remove timezone info)
- Filter invalid values (negative, NULL)
- Remove duplicates
- Insert in 5000-record chunks

**Step 3: Transform CAMS → measurements**
- Read NetCDF files from `data/raw/cams/*.nc.zip`
- Extract from ZIP archives
- Convert xarray Dataset → pandas DataFrame
- Melt pollutant columns to long format
- Map parameter names (`pm2p5` → `pm25`, etc.)
- Aggregate grid data to single Astana point (mean)
- Insert in chunks

**Step 4: Transform Open-Meteo → weather**
- Read CSV files from `data/raw/openmeteo/`
- Convert local time to UTC (Astana is UTC+6)
- Rename columns to match schema
- Remove duplicates
- Insert in chunks

**Step 5: Create unified_data**
- SQL JOIN: measurements ⟕ weather (FULL OUTER)
- Pivot measurements: rows → columns (pm25, pm10, etc.)
- Calculate temporal features (hour, day_of_week, season)
- Calculate completeness_score (0.0 to 1.0)
- Insert result

### 7.4 Key Code Patterns

**Chunked Insert (avoid memory issues):**
```python
CHUNK_SIZE = 5000

def insert_dataframe(df, table_name, engine):
    total = 0
    for i in range(0, len(df), CHUNK_SIZE):
        chunk = df.iloc[i:i+CHUNK_SIZE]
        with engine.begin() as conn:
            chunk.to_sql(table_name, conn, if_exists='append', index=False)
        total += len(chunk)
    return total
```

**Timestamp Handling (critical for PostgreSQL):**
```python
# Convert to UTC and REMOVE timezone info
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True).dt.tz_localize(None)
```

**CAMS Grid Aggregation:**
```python
# CAMS provides grid data (multiple lat/lon points)
# Aggregate to single value per timestamp
df_agg = df.groupby(['timestamp_utc', 'location', 'parameter', 'data_source']).agg({
    'value': 'mean',  # Average across grid
    'latitude': 'mean',
    'longitude': 'mean',
    ...
}).reset_index()
```

### 7.5 Output Summary

| Table | Records | Description |
|-------|---------|-------------|
| measurements | 65,658 | Air quality (OpenAQ + CAMS) |
| weather | 69,192 | Meteorological data |
| unified_data | 69,192 | ML-ready joined dataset |

---

## 8. Final Database Schema

### 8.1 measurements Table

```sql
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

-- Unique constraint
CREATE UNIQUE INDEX idx_measurements_unique 
ON measurements(timestamp_utc, location, parameter, data_source);
```

**Data Distribution:**
| data_source | parameter | count | min_date | max_date |
|-------------|-----------|-------|----------|----------|
| cams | pm10 | 20,456 | 2018-01-01 | 2024-12-31 |
| cams | pm25 | 20,456 | 2018-01-01 | 2024-12-31 |
| openaq | pm25 | 24,746 | 2018-07-27 | 2025-03-04 |

### 8.2 weather Table

```sql
CREATE TABLE weather (
    id SERIAL PRIMARY KEY,
    timestamp_utc TIMESTAMP NOT NULL,
    location VARCHAR(100) NOT NULL,
    latitude DECIMAL(9,6),
    longitude DECIMAL(9,6),
    
    -- Temperature
    temperature_c DECIMAL(5,2),
    feels_like_c DECIMAL(5,2),
    dew_point_c DECIMAL(5,2),
    
    -- Humidity/Precipitation
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
```

### 8.3 unified_data Table (ML-Ready)

```sql
CREATE TABLE unified_data (
    id SERIAL PRIMARY KEY,
    timestamp_utc TIMESTAMP NOT NULL,
    location VARCHAR(100) NOT NULL,
    
    -- Target Variables (Air Quality)
    pm25 DECIMAL(12,6),
    pm10 DECIMAL(12,6),
    no2 DECIMAL(12,6),
    o3 DECIMAL(12,6),
    so2 DECIMAL(12,6),
    co DECIMAL(12,6),
    
    -- Feature Variables (Weather)
    temperature_c DECIMAL(5,2),
    humidity_pct INTEGER,
    pressure_hpa DECIMAL(7,2),
    wind_speed_ms DECIMAL(5,2),
    wind_direction_deg INTEGER,
    precipitation_mm DECIMAL(6,2),
    cloud_cover_pct INTEGER,
    
    -- Temporal Features (for ML)
    hour INTEGER,           -- 0-23
    day_of_week INTEGER,    -- 0=Sunday, 6=Saturday
    day_of_month INTEGER,   -- 1-31
    month INTEGER,          -- 1-12
    season VARCHAR(10),     -- winter, spring, summer, autumn
    is_weekend BOOLEAN,
    is_heating_season BOOLEAN,  -- Oct-Apr (Astana climate)
    
    -- Metadata
    pm25_source VARCHAR(50),    -- openaq, cams
    weather_source VARCHAR(50), -- open-meteo
    completeness_score DECIMAL(3,2),  -- 0.00 to 1.00
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 8.4 Helper Views

```sql
-- Latest 24 hours
CREATE VIEW v_latest_measurements AS ...

-- Daily averages
CREATE VIEW v_daily_averages AS ...

-- Data quality report
CREATE VIEW v_data_quality AS ...
```

---

## 9. Data Quality Report

### 9.1 Completeness Score Formula

```sql
completeness_score = 
    0.30 × (pm25 IS NOT NULL) +
    0.20 × (temperature IS NOT NULL) +
    0.15 × (humidity IS NOT NULL) +
    0.15 × (wind_speed IS NOT NULL) +
    0.10 × (pressure IS NOT NULL) +
    0.10 × (pm10 IS NOT NULL)
```

### 9.2 Quality Distribution

| Quality Level | Count | Percentage |
|---------------|-------|------------|
| Excellent (≥0.9) | 37,428 | 54.1% |
| Fair (0.5-0.7) | 31,764 | 45.9% |

### 9.3 Date Coverage

| Table | From | To |
|-------|------|-----|
| measurements | 2018-01-01 | 2025-03-04 |
| weather | 2017-12-31 | 2025-11-22 |
| unified_data | 2017-12-31 | 2025-11-22 |

### 9.4 Known Data Gaps

1. **OpenAQ 2020-2021:** US Embassy sensor was offline
2. **CAMS 2025:** Reanalysis data not yet available for 2025
3. **Weather pre-2018:** Available but not collected

---

## 10. Scripts Reference

### 10.1 Data Collection Scripts

| Script | Purpose | Output |
|--------|---------|--------|
| `collect_openaq_historical.py` | Fetch PM2.5 from OpenAQ API | `data/raw/openaq/*.csv` |
| `collect_openmeteo_weather.py` | Fetch weather from Open-Meteo | `data/raw/openmeteo/*.csv` |
| `download_cams_all.py` | Download CAMS NetCDF files | `data/raw/cams/*.nc.zip` |
| `search_openaq_sensors.py` | Find OpenAQ sensor IDs | Console output |

### 10.2 Database Scripts

| Script | Purpose | Note |
|--------|---------|------|
| `create_normalized_schema.sql` | SQL schema definition | Run by normalize_data.py |
| `normalize_data.py` | Main ETL pipeline | **Primary script** |
| `load_all_to_postgres.py` | Old ETL (deprecated) | Don't use |
| `verify_database.py` | Check database contents | Diagnostic |
| `cleanup_and_reload.py` | Reset and reload | Emergency reset |

### 10.3 Usage Examples

**Collect all data from scratch:**
```bash
source .venv/bin/activate

# 1. OpenAQ (fast, ~5 min)
python scripts/collect_openaq_historical.py

# 2. Open-Meteo (fast, ~2 min)
python scripts/collect_openmeteo_weather.py

# 3. CAMS (slow, ~2-3 hours)
nohup python scripts/download_cams_all.py > cams_download.log 2>&1 &
```

**Load data to database:**
```bash
export PG_CONN_STR="postgresql://aaqis_user:aaqis_password@localhost:5432/aaqis_db"
python scripts/normalize_data.py
```

**Verify data:**
```bash
python scripts/verify_database.py
```

---

## 11. Troubleshooting Log

### 11.1 PostgreSQL Issues

**Problem:** `psycopg2` compilation error
```
fatal error: pg_config.h: No such file or directory
```
**Solution:** Use pre-compiled binary
```bash
pip install psycopg2-binary
```

**Problem:** Database not found
```
FATAL: database "airquality" does not exist
```
**Solution:** Use correct database name `aaqis_db`

**Problem:** Password authentication failed
```
FATAL: password authentication failed for user "aaqis_user"
```
**Solution:** Found password in `src/core/settings.py` line 79: `aaqis_password`

### 11.2 NetCDF Issues

**Problem:** xarray can't read NetCDF
```
ValueError: found the following matches with the input file in xarray's IO backends: ['h5netcdf']
```
**Solution:**
```bash
pip install h5netcdf netCDF4
```

### 11.3 pandas to_sql Issues

**Problem:** `method='multi'` creates thousands of columns
```
'value_m29011': 10.0, 'unit_m29011': 'µg/m³' ...
```
**Root Cause:** `method='multi'` tries to batch insert but misinterprets DataFrame structure

**Solution:** Remove `method='multi'`, use chunked inserts:
```python
# BAD - causes column explosion
df.to_sql('table', conn, method='multi')

# GOOD - chunked inserts
for i in range(0, len(df), CHUNK_SIZE):
    chunk = df.iloc[i:i+CHUNK_SIZE]
    chunk.to_sql('table', conn, if_exists='append', index=False)
```

### 11.4 Timestamp Issues

**Problem:** Duplicate key violation on timestamps
```
duplicate key value violates unique constraint "idx_measurements_unique"
```
**Root Cause:** Timezone-aware timestamps converted inconsistently

**Solution:** Always remove timezone before inserting:
```python
df['timestamp_utc'] = pd.to_datetime(df['timestamp_utc'], utc=True).dt.tz_localize(None)
```

### 11.5 CAMS Grid Data Issue

**Problem:** Multiple records per timestamp (grid points)
**Root Cause:** CAMS provides spatial grid (lat/lon matrix)

**Solution:** Aggregate to single point per timestamp:
```python
df_agg = df.groupby(['timestamp_utc', 'parameter']).agg({'value': 'mean'})
```

---

## 12. Reproducibility Guide

### 12.1 Clone and Setup

```bash
# Clone repository
git clone <repo_url>
cd AirQualitySystem

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 12.2 Collect Data

```bash
# OpenAQ (needs API key in script)
python scripts/collect_openaq_historical.py

# Open-Meteo (no key needed)
python scripts/collect_openmeteo_weather.py

# CAMS (needs ~/.cdsapirc)
python scripts/download_cams_all.py
```

### 12.3 Setup Database

```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE aaqis_db;
CREATE USER aaqis_user WITH PASSWORD 'aaqis_password';
GRANT ALL PRIVILEGES ON DATABASE aaqis_db TO aaqis_user;
\q
```

### 12.4 Run ETL

```bash
export PG_CONN_STR="postgresql://aaqis_user:aaqis_password@localhost:5432/aaqis_db"
python scripts/normalize_data.py
```

### 12.5 Verify

```bash
python scripts/verify_database.py

# Or directly in PostgreSQL
psql -U aaqis_user -d aaqis_db
SELECT COUNT(*) FROM unified_data;
```

---

## 13. Next Steps

### 13.1 Exploratory Data Analysis
- [ ] Create `notebooks/01_eda.ipynb`
- [ ] Time series visualization
- [ ] Correlation analysis (PM2.5 vs weather)
- [ ] Seasonal patterns
- [ ] Missing value analysis

### 13.2 Feature Engineering
- [ ] Lag features (t-1, t-6, t-24)
- [ ] Rolling averages (24h, 7d)
- [ ] AQI calculation
- [ ] Weather feature combinations

### 13.3 ML Model Development
- [ ] Baseline models (persistence, moving average)
- [ ] SVR (Support Vector Regression)
- [ ] LSTM neural network
- [ ] Hyperparameter tuning
- [ ] Model comparison (RMSE, MAE, R²)

### 13.4 Web Dashboard
- [ ] Django REST API endpoints
- [ ] Real-time data display
- [ ] Forecast visualization
- [ ] Historical trends

---

## Appendix A: File Structure

```
AirQualitySystem/
├── data/
│   ├── raw/
│   │   ├── openaq/
│   │   │   └── openaq_astana_historical.csv (29,012 records)
│   │   ├── openmeteo/
│   │   │   └── astana_weather_historical.csv (69,192 records)
│   │   ├── cams/
│   │   │   ├── cams_astana_2018_q1_pm.nc.zip
│   │   │   ├── cams_astana_2018_q1_gas.nc.zip
│   │   │   └── ... (58 files total)
│   │   └── .gitkeep
│   └── processed/
│       └── .gitkeep
├── scripts/
│   ├── collect_openaq_historical.py
│   ├── collect_openmeteo_weather.py
│   ├── download_cams_all.py
│   ├── normalize_data.py          # Main ETL
│   ├── create_normalized_schema.sql
│   ├── verify_database.py
│   └── ...
├── docs/
│   └── data_collection_log.md     # This file
├── notebooks/
│   └── (EDA notebooks)
├── src/
│   └── (Django application)
├── .venv/                          # Virtual environment (gitignored)
└── requirements.txt
```

---

## Appendix B: Complete Command History

```bash
# === ENVIRONMENT SETUP ===
cd /home/timseye/AirQualitySystem
python -m venv .venv
source .venv/bin/activate
pip install requests pandas cdsapi xarray h5netcdf netCDF4 sqlalchemy psycopg2-binary

# === DATA COLLECTION ===
# OpenAQ
python scripts/collect_openaq_historical.py

# Open-Meteo  
python scripts/collect_openmeteo_weather.py

# CAMS (configure API first)
nano ~/.cdsapirc  # Add: url: https://ads.atmosphere.copernicus.eu/api
                  #      key: YOUR_KEY
nohup python scripts/download_cams_all.py > cams_download.log 2>&1 &
tail -f cams_download.log

# === DATABASE ===
# Verify PostgreSQL
sudo -u postgres psql -l

# Set connection string
export PG_CONN_STR="postgresql://aaqis_user:aaqis_password@localhost:5432/aaqis_db"

# Run ETL pipeline
python scripts/normalize_data.py

# Verify results
python scripts/verify_database.py

# Direct SQL verification
psql -U aaqis_user -d aaqis_db -c "SELECT COUNT(*) FROM unified_data;"
```

---

**Document Version:** 2.0  
**Last Updated:** December 1, 2025  
**Status:** Data pipeline complete ✅

**Change Log:**
- v1.0 (Nov 30): Initial data collection documentation
- v2.0 (Dec 1): Added normalization pipeline, schema details, troubleshooting
