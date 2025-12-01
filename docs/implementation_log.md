# 🛠️ Implementation Log - Django Backend & Frontend
## AAQIS - Air Quality Intelligence System

**Author:** timseye  
**University:** Astana IT University  
**Date:** December 1-2, 2025  
**Purpose:** Technical documentation of web application implementation

---

## Table of Contents
1. [Project Architecture](#1-project-architecture)
2. [Directory Structure](#2-directory-structure)
3. [Django Configuration](#3-django-configuration)
4. [Database Models](#4-database-models)
5. [REST API Implementation](#5-rest-api-implementation)
6. [Frontend Templates](#6-frontend-templates)
7. [Docker Configuration](#7-docker-configuration)
8. [Running the Application](#8-running-the-application)

---

## 1. Project Architecture

### Clean Architecture Pattern
The project follows Clean Architecture principles with four layers:

```
┌─────────────────────────────────────────────────┐
│                 PRESENTATION                     │
│         (Views, Templates, Static)               │
├─────────────────────────────────────────────────┤
│                 APPLICATION                      │
│           (API Views, Business Logic)            │
├─────────────────────────────────────────────────┤
│                    DOMAIN                        │
│              (Models, Services)                  │
├─────────────────────────────────────────────────┤
│                INFRASTRUCTURE                    │
│         (Database, External APIs, ML)            │
└─────────────────────────────────────────────────┘
```

### Technology Stack
| Layer | Technology |
|-------|------------|
| Backend | Django 5.2.8, Django REST Framework |
| Database | PostgreSQL 15 (Docker) |
| Frontend | Bootstrap 5.3, Plotly.js |
| Container | Docker, docker-compose |

---

## 2. Directory Structure

### Final Project Structure
```
AirQualitySystem/
├── backend/                        # Django application (renamed from src/)
│   ├── __init__.py
│   ├── core/                       # Project configuration
│   │   ├── __init__.py
│   │   ├── settings.py             # Django settings
│   │   ├── urls.py                 # Root URL configuration
│   │   ├── wsgi.py                 # WSGI entry point
│   │   └── celery.py               # Celery configuration (future)
│   ├── domain/                     # Domain layer - models
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── air_quality.py      # AirQualityMeasurement model
│   │   ├── migrations/
│   │   └── services/
│   ├── application/                # Application layer - business logic
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── urls.py             # API URL routes
│   │   │   ├── views.py            # API overview
│   │   │   └── data_views.py       # Data API endpoints
│   │   └── tasks/
│   ├── infrastructure/             # Infrastructure layer
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── database/
│   │   ├── external_apis/
│   │   └── ml_models/
│   │       └── saved/              # Trained models storage
│   └── presentation/               # Presentation layer - UI
│       ├── __init__.py
│       ├── apps.py
│       ├── urls.py                 # Frontend URL routes
│       ├── views.py                # Template views
│       ├── templates/              # HTML templates
│       │   ├── base.html
│       │   ├── dashboard.html
│       │   ├── patterns.html
│       │   └── about.html
│       └── static/                 # CSS, JS, images
├── archive/
│   └── etl_scripts/                # Archived data collection scripts
├── data/
│   ├── raw/
│   └── processed/
├── docs/
│   ├── data_collection_log.md
│   └── implementation_log.md       # This file
├── tests/
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── pyproject.toml
├── requirements.txt
├── README.md
└── TODO.md
```

### Directory Restructuring (December 1, 2025)

**Changes Made:**
1. Renamed `src/` → `backend/` for clarity
2. Moved ETL scripts to `archive/etl_scripts/`
3. Moved thesis guidelines to `docs/thesis/guidelines/`
4. Updated all imports from `src.*` to `backend.*`

**Files Updated:**
- `backend/core/settings.py` - INSTALLED_APPS
- `backend/core/urls.py` - include paths
- `backend/core/wsgi.py` - application import
- `backend/core/celery.py` - app name
- All `apps.py` files - app names
- `manage.py` - settings module

---

## 3. Django Configuration

### 3.1 settings.py

**File:** `backend/core/settings.py`

```python
"""
Django settings for AAQIS project.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-secret-key-change-in-production')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'corsheaders',
    # Local apps
    'backend.domain',
    'backend.application',
    'backend.infrastructure',
    'backend.presentation',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'backend' / 'presentation' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'backend.core.wsgi.application'

# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'aaqis_db'),
        'USER': os.environ.get('DB_USER', 'aaqis_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'aaqis_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'backend' / 'presentation' / 'static']

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True
```

### 3.2 Root URL Configuration

**File:** `backend/core/urls.py`

```python
"""
Root URL Configuration for AAQIS.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('backend.application.api.urls')),
    path('', include('backend.presentation.urls')),
]
```

### 3.3 App Configurations

Each app has its own `apps.py`:

```python
# backend/domain/apps.py
from django.apps import AppConfig

class DomainConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.domain'

# backend/application/apps.py
class ApplicationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.application'

# backend/infrastructure/apps.py
class InfrastructureConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.infrastructure'

# backend/presentation/apps.py
class PresentationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'backend.presentation'
```

---

## 4. Database Models

### 4.1 Air Quality Model

**File:** `backend/domain/models/air_quality.py`

```python
"""
Air Quality Domain Models.
Represents the core data structure for air quality measurements.
"""
from django.db import models


class AirQualityMeasurement(models.Model):
    """
    Represents a single air quality measurement.
    Based on unified_data table schema.
    """
    timestamp_utc = models.DateTimeField(db_index=True)
    location = models.CharField(max_length=100, default='Astana')
    
    # Air Quality Parameters
    pm25 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    pm10 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    no2 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    o3 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    so2 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    co = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    
    # Weather Parameters
    temperature_c = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    humidity_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    pressure_hpa = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    wind_speed_ms = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    wind_direction_deg = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    precipitation_mm = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    cloud_cover_pct = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    
    # Temporal Features
    hour = models.IntegerField(null=True)
    day_of_week = models.IntegerField(null=True)
    day_of_month = models.IntegerField(null=True)
    month = models.IntegerField(null=True)
    season = models.CharField(max_length=20, null=True)
    is_weekend = models.BooleanField(null=True)
    is_heating_season = models.BooleanField(null=True)
    
    # Data Source Tracking
    pm25_source = models.CharField(max_length=50, null=True)
    weather_source = models.CharField(max_length=50, null=True)
    completeness_score = models.DecimalField(max_digits=5, decimal_places=4, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'unified_data'
        managed = False  # Table already exists from ETL
        ordering = ['-timestamp_utc']
        indexes = [
            models.Index(fields=['timestamp_utc']),
            models.Index(fields=['pm25']),
        ]
    
    def __str__(self):
        return f"{self.location} - {self.timestamp_utc} - PM2.5: {self.pm25}"
```

### 4.2 Existing Database Tables

The database was created by ETL scripts with the following schema:

**Table: `unified_data`** (69,192 records)
| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| timestamp_utc | TIMESTAMP | UTC timestamp |
| location | VARCHAR | City name |
| pm25 | DECIMAL | PM2.5 µg/m³ |
| pm10 | DECIMAL | PM10 µg/m³ |
| no2 | DECIMAL | NO2 concentration |
| o3 | DECIMAL | O3 concentration |
| so2 | DECIMAL | SO2 concentration |
| co | DECIMAL | CO concentration |
| temperature_c | DECIMAL | Temperature °C |
| humidity_pct | DECIMAL | Relative humidity % |
| pressure_hpa | DECIMAL | Pressure hPa |
| wind_speed_ms | DECIMAL | Wind speed m/s |
| wind_direction_deg | DECIMAL | Wind direction degrees |
| precipitation_mm | DECIMAL | Precipitation mm |
| cloud_cover_pct | DECIMAL | Cloud cover % |
| hour | INT | Hour of day (0-23) |
| day_of_week | INT | Day of week (0-6) |
| day_of_month | INT | Day of month |
| month | INT | Month (1-12) |
| season | VARCHAR | Season name |
| is_weekend | BOOLEAN | Weekend flag |
| is_heating_season | BOOLEAN | Heating season flag |
| pm25_source | VARCHAR | Data source for PM2.5 |
| weather_source | VARCHAR | Data source for weather |
| completeness_score | DECIMAL | Data completeness |
| created_at | TIMESTAMP | Record creation time |

---

## 5. REST API Implementation

### 5.1 API URL Configuration

**File:** `backend/application/api/urls.py`

```python
"""
API URL Configuration.
All endpoints are prefixed with /api/
"""
from django.urls import path
from . import views
from . import data_views

urlpatterns = [
    path('', views.api_root, name='api-root'),
    path('current/', data_views.current_data, name='current-data'),
    path('timeseries/', data_views.timeseries_data, name='timeseries-data'),
    path('statistics/', data_views.statistics, name='statistics'),
    path('daily/', data_views.daily_averages, name='daily-averages'),
    path('hourly-pattern/', data_views.hourly_pattern, name='hourly-pattern'),
    path('monthly-pattern/', data_views.monthly_pattern, name='monthly-pattern'),
    path('correlation/', data_views.correlation_data, name='correlation-data'),
]
```

### 5.2 Data Views (API Endpoints)

**File:** `backend/application/api/data_views.py`

```python
"""
API views for AAQIS Dashboard.
Provides REST endpoints for air quality data visualization.
"""
from datetime import datetime, timedelta
from decimal import Decimal
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_GET


def convert_decimal(value):
    """Convert Decimal to float for JSON serialization."""
    if isinstance(value, Decimal):
        return float(value)
    return value


def dictfetchall(cursor):
    """Return all rows from a cursor as a list of dicts."""
    columns = [col[0] for col in cursor.description]
    return [
        {col: convert_decimal(val) for col, val in zip(columns, row)}
        for row in cursor.fetchall()
    ]


@require_GET
def api_overview(request):
    """API overview and available endpoints."""
    return JsonResponse({
        'name': 'AAQIS API',
        'version': '1.0',
        'endpoints': {
            '/api/current/': 'Current air quality data',
            '/api/timeseries/': 'Time series data for charts',
            '/api/statistics/': 'Summary statistics',
            '/api/daily/': 'Daily averages',
        }
    })


@require_GET
def current_data(request):
    """Get the most recent air quality reading."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                timestamp_utc,
                pm25, pm25_source,
                pm10, no2, so2, o3, co,
                temperature_c, humidity_pct,
                wind_speed_ms, pressure_hpa
            FROM unified_data
            WHERE pm25 IS NOT NULL
            ORDER BY timestamp_utc DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
    
    if not row:
        return JsonResponse({'error': 'No data available'}, status=404)
    
    pm25 = convert_decimal(row[1])
    aqi = calculate_aqi(pm25) if pm25 else None
    category = get_aqi_category(pm25) if pm25 else 'unknown'
    
    return JsonResponse({
        'timestamp': row[0].isoformat() if row[0] else None,
        'pm25': pm25,
        'pm25_source': row[2],
        'pm10': convert_decimal(row[3]),
        'no2': convert_decimal(row[4]),
        'so2': convert_decimal(row[5]),
        'o3': convert_decimal(row[6]),
        'co': convert_decimal(row[7]),
        'aqi': aqi,
        'category': category,
        'weather': {
            'temperature': convert_decimal(row[8]),
            'humidity': convert_decimal(row[9]),
            'wind_speed': convert_decimal(row[10]),
            'pressure': convert_decimal(row[11]),
        }
    })


@require_GET
def timeseries_data(request):
    """Get time series data for charts."""
    days = int(request.GET.get('days', 7))
    parameter = request.GET.get('parameter', 'pm25')
    days = min(days, 365)
    
    param_map = {
        'pm25': 'pm25',
        'pm10': 'pm10',
        'temperature': 'temperature_c',
        'humidity': 'humidity_pct',
        'wind_speed': 'wind_speed_ms',
    }
    
    db_column = param_map.get(parameter, 'pm25')
    
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT timestamp_utc, {db_column} as value
            FROM unified_data
            WHERE {db_column} IS NOT NULL
              AND timestamp_utc >= NOW() - INTERVAL '{days} days'
            ORDER BY timestamp_utc ASC
        """)
        rows = cursor.fetchall()
    
    return JsonResponse({
        'parameter': parameter,
        'unit': get_unit(parameter),
        'data': [
            {'timestamp': row[0].isoformat(), 'value': convert_decimal(row[1])}
            for row in rows
        ]
    })


@require_GET
def statistics(request):
    """Get summary statistics."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                COUNT(*) as total_records,
                MIN(timestamp_utc) as first_record,
                MAX(timestamp_utc) as last_record,
                AVG(pm25) as avg_pm25,
                MIN(pm25) as min_pm25,
                MAX(pm25) as max_pm25,
                STDDEV(pm25) as std_pm25
            FROM unified_data
            WHERE pm25 IS NOT NULL
        """)
        overall = dictfetchall(cursor)[0]
        
        # AQI distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN pm25 <= 12 THEN 'Good'
                    WHEN pm25 <= 35.4 THEN 'Moderate'
                    WHEN pm25 <= 55.4 THEN 'Unhealthy for Sensitive'
                    WHEN pm25 <= 150.4 THEN 'Unhealthy'
                    WHEN pm25 <= 250.4 THEN 'Very Unhealthy'
                    ELSE 'Hazardous'
                END as category,
                COUNT(*) as count
            FROM unified_data
            WHERE pm25 IS NOT NULL
            GROUP BY 1
        """)
        distribution = dictfetchall(cursor)
    
    return JsonResponse({
        'overall': overall,
        'aqi_distribution': distribution
    })


@require_GET
def hourly_pattern(request):
    """Get average PM2.5 by hour of day."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT hour, AVG(pm25) as avg_pm25, AVG(temperature_c) as avg_temp
            FROM unified_data
            WHERE pm25 IS NOT NULL
            GROUP BY hour
            ORDER BY hour
        """)
        rows = dictfetchall(cursor)
    return JsonResponse({'data': rows})


@require_GET
def monthly_pattern(request):
    """Get average PM2.5 by month."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT month, AVG(pm25) as avg_pm25, COUNT(*) as count
            FROM unified_data
            WHERE pm25 IS NOT NULL
            GROUP BY month
            ORDER BY month
        """)
        rows = dictfetchall(cursor)
    
    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for row in rows:
        row['month_name'] = month_names[int(row['month'])]
    
    return JsonResponse({'data': rows})


# Helper functions
def calculate_aqi(pm25):
    """Calculate US EPA AQI from PM2.5 concentration."""
    if pm25 is None:
        return None
    pm25 = float(pm25)
    
    breakpoints = [
        (0, 12.0, 0, 50),
        (12.1, 35.4, 51, 100),
        (35.5, 55.4, 101, 150),
        (55.5, 150.4, 151, 200),
        (150.5, 250.4, 201, 300),
        (250.5, 500.4, 301, 500),
    ]
    
    for bp_lo, bp_hi, i_lo, i_hi in breakpoints:
        if bp_lo <= pm25 <= bp_hi:
            return round(((i_hi - i_lo) / (bp_hi - bp_lo)) * (pm25 - bp_lo) + i_lo)
    
    return 500 if pm25 > 500.4 else 0


def get_aqi_category(pm25):
    """Get AQI category from PM2.5."""
    if pm25 is None:
        return 'unknown'
    pm25 = float(pm25)
    if pm25 <= 12:
        return 'good'
    elif pm25 <= 35.4:
        return 'moderate'
    elif pm25 <= 55.4:
        return 'unhealthy_sensitive'
    elif pm25 <= 150.4:
        return 'unhealthy'
    elif pm25 <= 250.4:
        return 'very_unhealthy'
    else:
        return 'hazardous'


def get_unit(parameter):
    """Get unit for parameter."""
    units = {
        'pm25': 'µg/m³',
        'pm10': 'µg/m³',
        'temperature': '°C',
        'humidity': '%',
        'wind_speed': 'm/s',
    }
    return units.get(parameter, '')
```

### 5.3 API Endpoints Summary

| Endpoint | Method | Parameters | Description |
|----------|--------|------------|-------------|
| `/api/` | GET | - | API overview |
| `/api/current/` | GET | - | Latest AQI reading |
| `/api/timeseries/` | GET | `days`, `parameter` | Time series data |
| `/api/statistics/` | GET | - | Summary statistics |
| `/api/daily/` | GET | `days` | Daily averages |
| `/api/hourly-pattern/` | GET | - | Hourly pattern |
| `/api/monthly-pattern/` | GET | - | Monthly pattern |
| `/api/correlation/` | GET | `limit` | Correlation data |

---

## 6. Frontend Templates

### 6.1 Template Structure

```
backend/presentation/templates/
├── base.html           # Base layout with Bootstrap 5
├── dashboard.html      # Main dashboard page
├── patterns.html       # Data patterns analysis
└── about.html          # Project information
```

### 6.2 Base Template

**File:** `backend/presentation/templates/base.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}AAQIS{% endblock %}</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    <!-- Bootstrap Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css" rel="stylesheet">
    <!-- Plotly.js -->
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    
    <style>
        body {
            background-color: #1a1a2e;
            color: #eee;
            min-height: 100vh;
        }
        .navbar {
            background-color: #16213e !important;
        }
        .card {
            background-color: #1f2937;
            border: none;
            border-radius: 12px;
        }
        /* AQI Color Classes */
        .aqi-good { background: linear-gradient(135deg, #00e400, #00c000); }
        .aqi-moderate { background: linear-gradient(135deg, #ffff00, #cccc00); color: #333; }
        .aqi-unhealthy-sensitive { background: linear-gradient(135deg, #ff7e00, #cc6600); }
        .aqi-unhealthy { background: linear-gradient(135deg, #ff0000, #cc0000); }
        .aqi-very-unhealthy { background: linear-gradient(135deg, #8f3f97, #6a2c70); }
        .aqi-hazardous { background: linear-gradient(135deg, #7e0023, #5c0019); }
    </style>
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar navbar-expand-lg navbar-dark">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="bi bi-wind"></i> AAQIS
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/"><i class="bi bi-speedometer2"></i> Dashboard</a>
                <a class="nav-link" href="/patterns/"><i class="bi bi-graph-up"></i> Patterns</a>
                <a class="nav-link" href="/about/"><i class="bi bi-info-circle"></i> About</a>
            </div>
            <span class="navbar-text ms-3">
                <i class="bi bi-geo-alt"></i> {{ city }}, Kazakhstan
            </span>
        </div>
    </nav>

    <!-- Main Content -->
    <main class="container py-4">
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    <footer class="text-center py-3 mt-4">
        <small class="text-muted">
            AAQIS - Air Quality Intelligence System for Astana<br>
            Data sources: OpenAQ, Open-Meteo, CAMS | Astana IT University Diploma Project 2025
        </small>
    </footer>

    <!-- Bootstrap JS -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    {% block scripts %}{% endblock %}
</body>
</html>
```

### 6.3 Dashboard Template

**File:** `backend/presentation/templates/dashboard.html`

Key sections:
1. **AQI Card** - Current air quality with color coding
2. **Weather Card** - Temperature, humidity, wind, pressure
3. **Statistics Card** - Data statistics summary
4. **Time Period Selector** - 7 Days, 30 Days, 90 Days, 1 Year
5. **PM2.5 Time Series Chart** - Plotly.js line chart
6. **Daily Average Chart** - Bar chart with min/max
7. **AQI Distribution** - Pie chart
8. **Health Recommendations** - Based on current AQI

**JavaScript API Calls:**
```javascript
// Fetch current data
fetch('/api/current/')
    .then(response => response.json())
    .then(data => updateDashboard(data));

// Fetch time series
fetch(`/api/timeseries/?days=${days}&parameter=pm25`)
    .then(response => response.json())
    .then(data => renderTimeseriesChart(data));

// Fetch daily averages
fetch(`/api/daily/?days=${days}`)
    .then(response => response.json())
    .then(data => renderDailyChart(data));
```

### 6.4 Patterns Template

**File:** `backend/presentation/templates/patterns.html`

Charts included:
1. **Diurnal Pattern** - PM2.5 by hour of day with temperature overlay
2. **Seasonal Pattern** - Monthly averages bar chart
3. **PM2.5 vs Temperature** - Scatter plot
4. **PM2.5 vs Wind Speed** - Scatter plot
5. **Dual-Axis Time Series** - PM2.5 and temperature over time

### 6.5 About Template

**File:** `backend/presentation/templates/about.html`

Sections:
- Project description and goals
- Data sources table
- Technology stack with icons
- Academic context
- AQI Scale reference (US EPA)
- WHO Guidelines (2021)
- External resources links

### 6.6 Presentation Views

**File:** `backend/presentation/views.py`

```python
"""
Presentation layer views for AAQIS Dashboard.
Renders HTML templates for the web interface.
"""
from django.shortcuts import render


def dashboard(request):
    """Main dashboard view."""
    context = {
        'city': 'Astana',
        'page_title': 'Dashboard',
    }
    return render(request, 'dashboard.html', context)


def patterns(request):
    """Data patterns analysis view."""
    context = {
        'city': 'Astana',
        'page_title': 'Patterns',
    }
    return render(request, 'patterns.html', context)


def about(request):
    """About page view."""
    context = {
        'city': 'Astana',
        'page_title': 'About',
    }
    return render(request, 'about.html', context)
```

**File:** `backend/presentation/urls.py`

```python
"""
Presentation layer URL configuration.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('patterns/', views.patterns, name='patterns'),
    path('about/', views.about, name='about'),
]
```

---

## 7. Docker Configuration

### 7.1 Dockerfile

**File:** `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

### 7.2 Docker Compose

**File:** `docker-compose.yml`

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    container_name: aaqis_postgres
    environment:
      POSTGRES_DB: aaqis_db
      POSTGRES_USER: aaqis_user
      POSTGRES_PASSWORD: aaqis_password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U aaqis_user -d aaqis_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  web:
    build: .
    container_name: aaqis_web
    ports:
      - "8000:8000"
    environment:
      - DJANGO_DEBUG=True
      - DB_HOST=db
      - DB_NAME=aaqis_db
      - DB_USER=aaqis_user
      - DB_PASSWORD=aaqis_password
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - .:/app

volumes:
  postgres_data:
```

---

## 8. Running the Application

### 8.1 Development Mode

**Terminal 1 - Start PostgreSQL:**
```bash
cd ~/AirQualitySystem
sudo docker start aaqis_postgres
```

**Terminal 2 - Start Django:**
```bash
cd ~/AirQualitySystem
source .venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

**Access:**
- Dashboard: http://localhost:8000/
- Patterns: http://localhost:8000/patterns/
- About: http://localhost:8000/about/
- API: http://localhost:8000/api/

### 8.2 Docker Mode (Full Stack)

```bash
cd ~/AirQualitySystem
docker-compose up -d
```

### 8.3 Database Connection

```
Host: localhost
Port: 5432
Database: aaqis_db
User: aaqis_user
Password: aaqis_password
```

**Connection String:**
```
postgresql://aaqis_user:aaqis_password@localhost:5432/aaqis_db
```

---

## 9. Troubleshooting

### 9.1 Common Issues

**Issue:** "column 'timestamp' does not exist"
**Solution:** Use `timestamp_utc` instead of `timestamp` in SQL queries.

**Issue:** "TypeError: unsupported operand type(s) for *: 'float' and 'decimal.Decimal'"
**Solution:** Convert Decimal to float before arithmetic operations:
```python
pm25 = float(pm25)
```

**Issue:** "column 'category' does not exist"
**Solution:** Cannot use alias in ORDER BY CASE. Use `GROUP BY 1` and repeat CASE in ORDER BY.

### 9.2 Database Verification

```bash
PGPASSWORD=aaqis_password psql -h localhost -U aaqis_user -d aaqis_db -c "SELECT COUNT(*) FROM unified_data;"
```

Expected output: `69192`

---

## 10. Screenshots

### Dashboard
- AQI = 42 (Good) - Green card
- Weather: -8.3°C, 84% humidity, 14.7 m/s wind
- PM2.5 time series chart
- Health recommendations

### Patterns Page
- Diurnal pattern showing morning/evening peaks
- Seasonal pattern with higher winter values
- Scatter plots showing negative temperature correlation
- Dual-axis time series

### About Page
- Project description
- Data sources table
- Technology stack icons
- AQI scale and WHO guidelines

---

*Document created: December 2, 2025*
*Last updated: December 2, 2025*
