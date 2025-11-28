"""
Скрипт для сбора данных с AQICN API и сохранения в CSV
"""

import requests
import json
import csv
import os
from datetime import datetime

# API конфигурация
API_TOKEN = "d59d891eb5c761c98d06962f8294037535e8d1d7"
BASE_URL = "https://api.waqi.info"

# Папка для данных
DATA_DIR = "data/aqicn"

# Города Центральной Азии для мониторинга
CITIES = {
    "astana": {"name": "Astana", "country": "KZ"},
    "almaty": {"name": "Almaty", "country": "KZ"},
    "tashkent": {"name": "Tashkent", "country": "UZ"},
    "bishkek": {"name": "Bishkek", "country": "KG"},
}


def ensure_data_dir():
    """Создать папку для данных если нет"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Создана папка: {DATA_DIR}")


def fetch_city_data(city_key):
    """Получить данные для города"""
    url = f"{BASE_URL}/feed/{city_key}/?token={API_TOKEN}"
    
    try:
        response = requests.get(url, timeout=30)
        data = response.json()
        
        if data.get('status') == 'ok':
            return data.get('data')
        else:
            print(f"  Ошибка для {city_key}: {data.get('data', 'Unknown error')}")
            return None
            
    except Exception as e:
        print(f"  Ошибка запроса для {city_key}: {e}")
        return None


def parse_aqicn_data(city_key, raw_data):
    """Преобразовать сырые данные в структурированный формат"""
    if not raw_data:
        return None
    
    city_info = CITIES.get(city_key, {"name": city_key, "country": "XX"})
    
    # Время измерения
    time_data = raw_data.get('time', {})
    timestamp_utc = time_data.get('iso', datetime.utcnow().isoformat())
    
    # Координаты
    geo = raw_data.get('city', {}).get('geo', [None, None])
    
    # Индивидуальные показатели загрязнения (iaqi)
    iaqi = raw_data.get('iaqi', {})
    
    record = {
        'timestamp_utc': timestamp_utc,
        'timestamp_local': time_data.get('s'),
        'city': city_info['name'],
        'country_code': city_info['country'],
        'station_name': raw_data.get('city', {}).get('name', ''),
        'station_idx': raw_data.get('idx'),
        'lat': geo[0] if len(geo) > 0 else None,
        'lon': geo[1] if len(geo) > 1 else None,
        
        # AQI
        'aqi': raw_data.get('aqi'),
        'dominant_pollutant': raw_data.get('dominentpol'),
        
        # Загрязнители (из iaqi)
        'pm25': iaqi.get('pm25', {}).get('v'),
        'pm10': iaqi.get('pm10', {}).get('v'),
        'o3': iaqi.get('o3', {}).get('v'),
        'no2': iaqi.get('no2', {}).get('v'),
        'so2': iaqi.get('so2', {}).get('v'),
        'co': iaqi.get('co', {}).get('v'),
        
        # Метеоданные
        'temp_c': iaqi.get('t', {}).get('v'),
        'humidity_pct': iaqi.get('h', {}).get('v'),
        'pressure_hpa': iaqi.get('p', {}).get('v'),
        'wind_ms': iaqi.get('w', {}).get('v'),
        'wind_gust_ms': iaqi.get('wg', {}).get('v'),
        'dew_point_c': iaqi.get('dew', {}).get('v'),
        
        # Метаданные
        'data_source': 'aqicn',
        'collected_at': datetime.utcnow().isoformat()
    }
    
    return record


def save_to_csv(records, filename=None):
    """Сохранить записи в CSV"""
    if not records:
        print("Нет данных для сохранения")
        return
    
    ensure_data_dir()
    
    if filename is None:
        date_str = datetime.utcnow().strftime('%Y%m%d')
        filename = f"aqicn_data_{date_str}.csv"
    
    filepath = os.path.join(DATA_DIR, filename)
    
    # Проверяем существует ли файл
    file_exists = os.path.exists(filepath)
    
    # Записываем
    with open(filepath, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        
        if not file_exists:
            writer.writeheader()
        
        writer.writerows(records)
    
    print(f"Сохранено {len(records)} записей в {filepath}")
    return filepath


def collect_all_cities():
    """Собрать данные со всех городов"""
    print("=" * 60)
    print(f"Сбор данных AQICN - {datetime.utcnow().isoformat()}")
    print("=" * 60)
    
    records = []
    
    for city_key, city_info in CITIES.items():
        print(f"\nЗапрос данных для {city_info['name']}...")
        
        raw_data = fetch_city_data(city_key)
        
        if raw_data:
            record = parse_aqicn_data(city_key, raw_data)
            if record:
                records.append(record)
                print(f"  ✓ AQI: {record['aqi']}, PM2.5: {record['pm25']}, Temp: {record['temp_c']}°C")
        else:
            print(f"  ✗ Нет данных")
    
    return records


def get_forecast_data(city_key="astana"):
    """Получить прогноз для города"""
    print(f"\n" + "=" * 60)
    print(f"Прогноз для {city_key}")
    print("=" * 60)
    
    raw_data = fetch_city_data(city_key)
    
    if raw_data and 'forecast' in raw_data:
        forecast = raw_data['forecast'].get('daily', {})
        
        print("\nПрогноз PM2.5:")
        for day in forecast.get('pm25', []):
            print(f"  {day['day']}: avg={day['avg']}, min={day['min']}, max={day['max']}")
        
        print("\nПрогноз PM10:")
        for day in forecast.get('pm10', []):
            print(f"  {day['day']}: avg={day['avg']}, min={day['min']}, max={day['max']}")
        
        return forecast
    
    return None


def show_current_status():
    """Показать текущий статус качества воздуха"""
    print("\n" + "=" * 60)
    print("ТЕКУЩЕЕ КАЧЕСТВО ВОЗДУХА")
    print("=" * 60)
    
    for city_key, city_info in CITIES.items():
        raw_data = fetch_city_data(city_key)
        
        if raw_data:
            aqi = raw_data.get('aqi', 'N/A')
            dominant = raw_data.get('dominentpol', 'N/A')
            
            # Определяем категорию AQI
            if isinstance(aqi, int):
                if aqi <= 50:
                    status = "🟢 Good"
                elif aqi <= 100:
                    status = "🟡 Moderate"
                elif aqi <= 150:
                    status = "🟠 Unhealthy for Sensitive"
                elif aqi <= 200:
                    status = "🔴 Unhealthy"
                elif aqi <= 300:
                    status = "🟣 Very Unhealthy"
                else:
                    status = "🟤 Hazardous"
            else:
                status = "❓ Unknown"
            
            print(f"\n{city_info['name']}, {city_info['country']}:")
            print(f"  AQI: {aqi} - {status}")
            print(f"  Dominant pollutant: {dominant}")
            
            iaqi = raw_data.get('iaqi', {})
            if iaqi.get('t'):
                print(f"  Temperature: {iaqi['t']['v']}°C")
            if iaqi.get('h'):
                print(f"  Humidity: {iaqi['h']['v']}%")


if __name__ == "__main__":
    # Показать текущий статус
    show_current_status()
    
    # Собрать и сохранить данные
    print("\n")
    records = collect_all_cities()
    
    if records:
        save_to_csv(records)
    
    # Показать прогноз для Астаны
    get_forecast_data("astana")
    
    print("\n" + "=" * 60)
    print("Готово!")
    print("=" * 60)
