# 🌬️ AAQIS - Air Quality Intelligence System for Astana

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-5.2-green.svg)](https://djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)](https://postgresql.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A comprehensive system for monitoring, analyzing, and visualizing air quality data in Astana, Kazakhstan. Developed as a diploma thesis at **Astana IT University**.

## 📸 Screenshots

### Dashboard
- Real-time AQI display with color-coded status
- Current weather conditions
- PM2.5 time series charts
- Health recommendations

### Patterns Analysis
- Diurnal (hourly) pollution patterns
- Seasonal (monthly) variations
- PM2.5 vs Temperature/Wind scatter plots
- Dual-axis time series visualization

### About Page
- Project information and data sources
- AQI scale reference (US EPA)
- WHO Guidelines (2021)
- Technology stack

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL 15+ (or Docker)
- Git

### 1. Clone Repository
```bash
git clone https://github.com/timseye/AirQualitySystem.git
cd AirQualitySystem
```

### 2. Setup Python Environment
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### 3. Start PostgreSQL (Docker)
```bash
docker run -d \
  --name aaqis_postgres \
  -e POSTGRES_DB=aaqis_db \
  -e POSTGRES_USER=aaqis_user \
  -e POSTGRES_PASSWORD=aaqis_password \
  -p 5432:5432 \
  postgres:15
```

### 4. Run Django Server
```bash
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### 5. Open Browser
- **Dashboard:** http://localhost:8000/
- **Patterns:** http://localhost:8000/patterns/
- **About:** http://localhost:8000/about/
- **API:** http://localhost:8000/api/

---

## 📊 Data Sources

| Source | Type | Period | Description |
|--------|------|--------|-------------|
| **OpenAQ** | PM2.5 | 2018-2025 | U.S. Embassy ground station |
| **Open-Meteo** | Weather | 2018-2025 | Temperature, humidity, wind, pressure |
| **CAMS** | Reanalysis | 2018-2024 | Copernicus atmospheric data |

**Total Records:** 69,192 hourly observations

---

## 🏗️ Project Structure

```
AirQualitySystem/
├── backend/                    # Django application
│   ├── core/                   # Settings, URLs, WSGI
│   ├── domain/                 # Models (air_quality)
│   ├── application/            # Business logic, API
│   ├── infrastructure/         # DB, external APIs, ML
│   └── presentation/           # Views, templates
├── data/
│   ├── raw/                    # Original data files
│   └── processed/              # Cleaned datasets
├── archive/
│   └── etl_scripts/            # Data collection scripts
├── docs/
│   ├── data_collection_log.md  # Complete ETL documentation
│   └── thesis/                 # LaTeX thesis files
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── pyproject.toml
└── README.md
```

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/` | GET | API overview |
| `/api/current/` | GET | Latest AQI reading |
| `/api/timeseries/` | GET | Time series data |
| `/api/statistics/` | GET | Summary statistics |
| `/api/daily/` | GET | Daily averages |
| `/api/hourly-pattern/` | GET | Hourly pattern |
| `/api/monthly-pattern/` | GET | Monthly pattern |
| `/api/correlation/` | GET | Correlation data |

### Example Response (`/api/current/`)
```json
{
  "timestamp": "2024-03-04T12:00:00",
  "pm25": 16.0,
  "aqi": 42,
  "category": "good",
  "weather": {
    "temperature": -8.3,
    "humidity": 84,
    "wind_speed": 14.7,
    "pressure": 983
  }
}
```

---

## 🗄️ Database Schema

### Main Table: `unified_data`

| Column | Type | Description |
|--------|------|-------------|
| `timestamp_utc` | TIMESTAMP | UTC timestamp |
| `pm25` | DECIMAL | PM2.5 concentration (µg/m³) |
| `pm10` | DECIMAL | PM10 concentration |
| `temperature_c` | DECIMAL | Temperature (°C) |
| `humidity_pct` | DECIMAL | Relative humidity (%) |
| `wind_speed_ms` | DECIMAL | Wind speed (m/s) |
| `pressure_hpa` | DECIMAL | Pressure (hPa) |
| `hour` | INT | Hour of day (0-23) |
| `month` | INT | Month (1-12) |
| `season` | VARCHAR | Season name |
| `is_heating_season` | BOOLEAN | October-April |

---

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Django 5.2, Django REST Framework |
| **Database** | PostgreSQL 15 |
| **Frontend** | Bootstrap 5, Plotly.js |
| **Containerization** | Docker, docker-compose |
| **Data Processing** | pandas, SQLAlchemy |
| **ML (planned)** | TensorFlow/Keras, scikit-learn |

---

## 📈 Data Insights

Based on 7 years of data (2018-2025):

1. **Seasonal Pattern:** PM2.5 is 2-3x higher in winter (heating season) vs summer
2. **Diurnal Pattern:** Peaks at 8-9 AM and 6-8 PM (traffic + heating)
3. **Temperature Correlation:** Negative correlation (-0.4) - colder = more pollution
4. **Wind Effect:** Higher wind speeds reduce PM2.5 concentrations

---

## 📄 Academic Context

**Thesis Title:** "Development of a System for Analyzing and Visualizing Air Quality in Astana Using Data Analysis Techniques"

**University:** Astana IT University  
**Department:** Computer Science  
**Year:** 2025

---

## 📝 Documentation

- [Data Collection Log](docs/data_collection_log.md) - Complete ETL pipeline documentation
- [TODO](TODO.md) - Project roadmap and task tracking

---

## 🔜 Roadmap

- [x] Data collection (OpenAQ, Open-Meteo, CAMS)
- [x] PostgreSQL database setup
- [x] ETL pipeline
- [x] Django backend with REST API
- [x] Bootstrap + Plotly.js dashboard
- [ ] ML forecasting models (LSTM, SVR)
- [ ] Real-time data updates (Celery)
- [ ] Docker Compose deployment
- [ ] Model API integration

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 👤 Author

**timseye** - Astana IT University, 2025

---

## 🙏 Acknowledgments

- [OpenAQ](https://openaq.org/) - Air quality data platform
- [Open-Meteo](https://open-meteo.com/) - Free weather API
- [Copernicus CAMS](https://atmosphere.copernicus.eu/) - Atmospheric reanalysis
- [WHO](https://www.who.int/) - Air quality guidelines
