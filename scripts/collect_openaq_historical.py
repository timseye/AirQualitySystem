"""
Скрипт для сбора исторических данных с OpenAQ API
Астана: 2018 - 2025
"""

import requests
import json
import csv
import os
from datetime import datetime, timedelta

# API конфигурация
API_KEY = "c5fb53161f8c1a4a07723fbb9a025c04b61471501b7c7f6b4839def76e1b08bd"
BASE_URL = "https://api.openaq.org/v3"
HEADERS = {"X-API-Key": API_KEY}

# Папка для данных
DATA_DIR = "data/openaq"

# Станции для сбора данных
STATIONS = {
    "astana": {
        "location_id": 7094,
        "sensor_id": 20512,  # PM2.5
        "name": "Astana",
        "country": "KZ"
    }
}


def ensure_data_dir():
    """Создать папку для данных"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Создана папка: {DATA_DIR}")


def fetch_measurements(sensor_id, date_from=None, date_to=None, limit=1000, page=1):
    """Получить измерения для сенсора"""
    url = f"{BASE_URL}/sensors/{sensor_id}/measurements"
    
    params = {
        "limit": limit,
        "page": page
    }
    
    if date_from:
        params["datetime_from"] = date_from
    if date_to:
        params["datetime_to"] = date_to
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=60)
        data = response.json()
        
        if 'results' in data:
            return data['results'], data.get('meta', {})
        else:
            print(f"Ошибка: {data}")
            return [], {}
            
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return [], {}


def collect_all_historical_data(sensor_id, city_name):
    """Собрать все исторические данные для сенсора"""
    print(f"\n{'='*60}")
    print(f"Сбор данных для {city_name} (sensor_id={sensor_id})")
    print(f"{'='*60}")
    
    all_measurements = []
    page = 1
    limit = 1000
    
    while True:
        print(f"  Страница {page}...")
        measurements, meta = fetch_measurements(sensor_id, limit=limit, page=page)
        
        if not measurements:
            break
        
        all_measurements.extend(measurements)
        print(f"  Получено: {len(measurements)} записей (всего: {len(all_measurements)})")
        
        # Проверяем есть ли ещё данные
        found = meta.get('found', '0')
        if found == '>1000':
            # Есть ещё данные
            page += 1
            if page > 100:  # Защита от бесконечного цикла
                print("  Достигнут лимит страниц")
                break
        else:
            break
    
    print(f"\nВсего собрано: {len(all_measurements)} измерений")
    return all_measurements


def parse_measurement(m, city_info):
    """Преобразовать измерение в структурированный формат"""
    period = m.get('period', {})
    datetime_from = period.get('datetimeFrom', {})
    
    return {
        'timestamp_utc': datetime_from.get('utc', ''),
        'timestamp_local': datetime_from.get('local', ''),
        'city': city_info['name'],
        'country_code': city_info['country'],
        'location_id': city_info['location_id'],
        'sensor_id': city_info['sensor_id'],
        'parameter': m.get('parameter', {}).get('name', ''),
        'value': m.get('value'),
        'units': m.get('parameter', {}).get('units', ''),
        'data_quality': 'OK' if not m.get('flagInfo', {}).get('hasFlags') else 'FLAGGED'
    }


def save_to_csv(measurements, city_info, filename=None):
    """Сохранить данные в CSV"""
    if not measurements:
        print("Нет данных для сохранения")
        return
    
    ensure_data_dir()
    
    if filename is None:
        filename = f"openaq_{city_info['name'].lower()}_historical.csv"
    
    filepath = os.path.join(DATA_DIR, filename)
    
    # Парсим данные
    records = [parse_measurement(m, city_info) for m in measurements]
    
    # Сортируем по времени
    records.sort(key=lambda x: x['timestamp_utc'])
    
    # Записываем
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
    
    print(f"\nСохранено {len(records)} записей в {filepath}")
    
    # Статистика
    if records:
        first_date = records[0]['timestamp_utc'][:10]
        last_date = records[-1]['timestamp_utc'][:10]
        print(f"Период: {first_date} — {last_date}")
    
    return filepath


def get_station_info(location_id):
    """Получить информацию о станции"""
    url = f"{BASE_URL}/locations/{location_id}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        data = response.json()
        
        if 'results' in data and data['results']:
            return data['results'][0]
    except Exception as e:
        print(f"Ошибка: {e}")
    
    return None


def show_station_info(location_id):
    """Показать информацию о станции"""
    info = get_station_info(location_id)
    
    if info:
        print(f"\nИнформация о станции:")
        print(f"  ID: {info.get('id')}")
        print(f"  Название: {info.get('name')}")
        print(f"  Страна: {info.get('country', {}).get('name')}")
        print(f"  Провайдер: {info.get('provider', {}).get('name')}")
        print(f"  Координаты: {info.get('coordinates')}")
        print(f"  Сенсоры:")
        for sensor in info.get('sensors', []):
            param = sensor.get('parameter', {})
            print(f"    - {param.get('name')} ({param.get('units')}), ID: {sensor.get('id')}")
        return info
    
    return None


if __name__ == "__main__":
    print("="*60)
    print("OpenAQ Historical Data Collector")
    print("="*60)
    
    for city_key, city_info in STATIONS.items():
        # Показать информацию о станции
        show_station_info(city_info['location_id'])
        
        # Собрать все данные
        measurements = collect_all_historical_data(
            city_info['sensor_id'], 
            city_info['name']
        )
        
        # Сохранить в CSV
        if measurements:
            save_to_csv(measurements, city_info)
    
    print("\n" + "="*60)
    print("Готово!")
    print("="*60)
