"""
API views for AAQIS Dashboard.
Provides REST endpoints for air quality data visualization.
Updated to match actual database schema.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from django.http import JsonResponse
from django.db import connection
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page


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
    
    # Calculate AQI
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
    # Parse parameters
    days = int(request.GET.get('days', 7))
    parameter = request.GET.get('parameter', 'pm25')
    
    # Limit to reasonable range
    days = min(days, 365)
    
    # Map parameter names to actual DB columns
    param_map = {
        'pm25': 'pm25',
        'pm10': 'pm10',
        'no2': 'no2',
        'so2': 'so2',
        'o3': 'o3',
        'co': 'co',
        'temperature': 'temperature_c',
        'humidity': 'humidity_pct',
        'wind_speed': 'wind_speed_ms',
    }
    
    db_column = param_map.get(parameter, 'pm25')
    
    with connection.cursor() as cursor:
        # Use last available data date instead of NOW() 
        # (data ends March 2025, current date is December 2025)
        cursor.execute(f"""
            SELECT 
                timestamp_utc,
                {db_column} as value
            FROM unified_data
            WHERE {db_column} IS NOT NULL
              AND timestamp_utc >= (
                  SELECT MAX(timestamp_utc) - INTERVAL '{days} days' 
                  FROM unified_data 
                  WHERE {db_column} IS NOT NULL
              )
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
def daily_averages(request):
    """Get daily average PM2.5 for the last N days."""
    days = int(request.GET.get('days', 30))
    days = min(days, 365)
    
    with connection.cursor() as cursor:
        # Use last available data date instead of NOW()
        cursor.execute(f"""
            SELECT 
                DATE(timestamp_utc) as date,
                AVG(pm25) as avg_pm25,
                MIN(pm25) as min_pm25,
                MAX(pm25) as max_pm25,
                AVG(temperature_c) as avg_temp
            FROM unified_data
            WHERE pm25 IS NOT NULL
              AND timestamp_utc >= (
                  SELECT MAX(timestamp_utc) - INTERVAL '{days} days' 
                  FROM unified_data 
                  WHERE pm25 IS NOT NULL
              )
            GROUP BY DATE(timestamp_utc)
            ORDER BY date ASC
        """)
        rows = dictfetchall(cursor)
    
    # Convert date objects to strings
    for row in rows:
        if row.get('date'):
            row['date'] = row['date'].isoformat()
    
    return JsonResponse({
        'days': days,
        'data': rows
    })


@require_GET
def statistics(request):
    """Get summary statistics."""
    with connection.cursor() as cursor:
        # Overall stats
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
                category,
                COUNT(*) as count
            FROM (
                SELECT 
                    CASE 
                        WHEN pm25 <= 12 THEN 'Good'
                        WHEN pm25 <= 35.4 THEN 'Moderate'
                        WHEN pm25 <= 55.4 THEN 'Unhealthy for Sensitive'
                        WHEN pm25 <= 150.4 THEN 'Unhealthy'
                        WHEN pm25 <= 250.4 THEN 'Very Unhealthy'
                        ELSE 'Hazardous'
                    END as category,
                    CASE 
                        WHEN pm25 <= 12 THEN 1
                        WHEN pm25 <= 35.4 THEN 2
                        WHEN pm25 <= 55.4 THEN 3
                        WHEN pm25 <= 150.4 THEN 4
                        WHEN pm25 <= 250.4 THEN 5
                        ELSE 6
                    END as sort_order
                FROM unified_data
                WHERE pm25 IS NOT NULL
            ) categorized
            GROUP BY category, sort_order
            ORDER BY sort_order
        """)
        distribution = dictfetchall(cursor)
    
    # Convert datetime objects to strings
    if overall.get('first_record'):
        overall['first_record'] = overall['first_record'].isoformat()
    if overall.get('last_record'):
        overall['last_record'] = overall['last_record'].isoformat()
    
    return JsonResponse({
        'overall': overall,
        'aqi_distribution': distribution
    })


@require_GET  
def hourly_pattern(request):
    """Get average PM2.5 by hour of day."""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                hour,
                AVG(pm25) as avg_pm25,
                AVG(temperature_c) as avg_temp
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
            SELECT 
                month,
                AVG(pm25) as avg_pm25,
                COUNT(*) as count
            FROM unified_data
            WHERE pm25 IS NOT NULL
            GROUP BY month
            ORDER BY month
        """)
        rows = dictfetchall(cursor)
    
    # Add month names
    month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    for row in rows:
        if row.get('month'):
            row['month_name'] = month_names[int(row['month'])]
    
    return JsonResponse({'data': rows})


@require_GET
def correlation_data(request):
    """Get data for correlation analysis (PM2.5 vs weather)."""
    limit = int(request.GET.get('limit', 1000))
    limit = min(limit, 10000)
    
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT 
                pm25, temperature_c, humidity_pct,
                wind_speed_ms, pressure_hpa
            FROM unified_data
            WHERE pm25 IS NOT NULL 
              AND temperature_c IS NOT NULL
            ORDER BY timestamp_utc DESC
            LIMIT {limit}
        """)
        rows = cursor.fetchall()
    
    return JsonResponse({
        'data': [
            {
                'pm25': convert_decimal(row[0]),
                'temperature': convert_decimal(row[1]),
                'humidity': convert_decimal(row[2]),
                'wind_speed': convert_decimal(row[3]),
                'pressure': convert_decimal(row[4])
            }
            for row in rows
        ]
    })


# Helper functions
def calculate_aqi(pm25):
    """Calculate US EPA AQI from PM2.5 concentration."""
    if pm25 is None:
        return None
    
    # Convert Decimal to float if needed
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
    pm25 = float(pm25)  # Convert Decimal to float if needed
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
        'no2': 'µg/m³',
        'so2': 'µg/m³',
        'o3': 'µg/m³',
        'co': 'mg/m³',
        'temperature': '°C',
        'humidity': '%',
        'wind_speed': 'm/s',
    }
    return units.get(parameter, '')
