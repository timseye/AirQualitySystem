"""
Скрипт для поиска всех сенсоров OpenAQ в Астане
и сбора всех доступных параметров (PM2.5, PM10, NO2, O3, SO2, CO)
"""

import requests
import json
import csv
import os
from datetime import datetime

# API конфигурация
API_KEY = "c5fb53161f8c1a4a07723fbb9a025c04b61471501b7c7f6b4839def76e1b08bd"
BASE_URL = "https://api.openaq.org/v3"
HEADERS = {"X-API-Key": API_KEY}

DATA_DIR = "data/raw/openaq"

# Астана координаты и радиус поиска
ASTANA_LAT = 51.1694
ASTANA_LON = 71.4491
SEARCH_RADIUS_KM = 50  # километров


def search_locations_near_astana():
    """Найти все станции мониторинга рядом с Астаной"""
    print("=" * 60)
    print("Поиск станций OpenAQ рядом с Астаной")
    print(f"Координаты: {ASTANA_LAT}, {ASTANA_LON}")
    print(f"Радиус поиска: {SEARCH_RADIUS_KM} км")
    print("=" * 60)
    
    # Поиск по координатам
    url = f"{BASE_URL}/locations"
    params = {
        "coordinates": f"{ASTANA_LAT},{ASTANA_LON}",
        "radius": SEARCH_RADIUS_KM * 1000,  # в метрах
        "limit": 100
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=60)
        data = response.json()
        
        if "results" in data:
            locations = data["results"]
            print(f"\n✓ Найдено {len(locations)} станций\n")
            return locations
        else:
            print(f"Ошибка: {data}")
            return []
            
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return []


def search_kazakhstan_locations():
    """Найти все станции в Казахстане"""
    print("\n" + "=" * 60)
    print("Поиск всех станций OpenAQ в Казахстане")
    print("=" * 60)
    
    url = f"{BASE_URL}/locations"
    params = {
        "countries_id": 123,  # Kazakhstan ID в OpenAQ
        "limit": 100
    }
    
    # Альтернативный поиск по коду страны
    url2 = f"{BASE_URL}/countries"
    
    try:
        # Сначала найдём ID Казахстана
        resp = requests.get(url2, headers=HEADERS, timeout=30)
        countries = resp.json().get("results", [])
        
        kz_id = None
        for c in countries:
            if c.get("code") == "KZ":
                kz_id = c.get("id")
                print(f"Kazakhstan ID: {kz_id}")
                break
        
        if kz_id:
            params["countries_id"] = kz_id
            response = requests.get(url, params=params, headers=HEADERS, timeout=60)
            data = response.json()
            
            if "results" in data:
                locations = data["results"]
                print(f"\n✓ Найдено {len(locations)} станций в Казахстане\n")
                return locations
                
    except Exception as e:
        print(f"Ошибка: {e}")
    
    return []


def get_location_details(location_id: int) -> dict:
    """Получить детальную информацию о станции"""
    url = f"{BASE_URL}/locations/{location_id}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        data = response.json()
        
        if "results" in data and data["results"]:
            return data["results"][0]
    except Exception as e:
        print(f"Ошибка: {e}")
    
    return {}


def print_location_info(location: dict):
    """Красиво вывести информацию о станции"""
    print("-" * 50)
    print(f"📍 {location.get('name', 'Unknown')}")
    print(f"   ID: {location.get('id')}")
    print(f"   Провайдер: {location.get('provider', {}).get('name', 'N/A')}")
    
    coords = location.get('coordinates', {})
    print(f"   Координаты: {coords.get('latitude')}, {coords.get('longitude')}")
    
    # Сенсоры и параметры
    sensors = location.get('sensors', [])
    if sensors:
        print(f"   Сенсоры ({len(sensors)}):")
        for sensor in sensors:
            param = sensor.get('parameter', {})
            print(f"      • {param.get('name', 'N/A')} ({param.get('units', '')}) - sensor_id: {sensor.get('id')}")
    
    # Даты данных
    datetime_first = location.get('datetimeFirst', {})
    datetime_last = location.get('datetimeLast', {})
    if datetime_first:
        print(f"   Первые данные: {datetime_first.get('local', 'N/A')}")
    if datetime_last:
        print(f"   Последние данные: {datetime_last.get('local', 'N/A')}")


def collect_sensor_data(sensor_id: int, sensor_name: str, city: str = "Astana"):
    """Собрать все данные для сенсора"""
    print(f"\n  Сбор данных для sensor_id={sensor_id} ({sensor_name})...")
    
    url = f"{BASE_URL}/sensors/{sensor_id}/measurements"
    all_measurements = []
    page = 1
    
    while page <= 50:  # Ограничение на 50 страниц
        params = {"limit": 1000, "page": page}
        
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=60)
            data = response.json()
            
            if "results" in data and data["results"]:
                all_measurements.extend(data["results"])
                
                found = data.get("meta", {}).get("found", 0)
                if found != ">1000":
                    break
                page += 1
            else:
                break
                
        except Exception as e:
            print(f"    Ошибка на странице {page}: {e}")
            break
    
    print(f"    ✓ Получено {len(all_measurements)} записей")
    return all_measurements


def save_all_astana_data(locations: list):
    """Сохранить все данные по Астане"""
    print("\n" + "=" * 60)
    print("Сбор данных со всех станций Астаны")
    print("=" * 60)
    
    all_records = []
    
    for loc in locations:
        loc_name = loc.get('name', 'Unknown')
        loc_id = loc.get('id')
        
        # Фильтруем только Астану
        name_lower = loc_name.lower()
        if 'astana' not in name_lower and 'nur-sultan' not in name_lower:
            continue
        
        print(f"\n📍 {loc_name} (ID: {loc_id})")
        
        sensors = loc.get('sensors', [])
        for sensor in sensors:
            sensor_id = sensor.get('id')
            param = sensor.get('parameter', {})
            param_name = param.get('name', 'unknown')
            param_units = param.get('units', '')
            
            measurements = collect_sensor_data(sensor_id, param_name)
            
            for m in measurements:
                period = m.get('period', {})
                datetime_from = period.get('datetimeFrom', {})
                
                record = {
                    'timestamp_utc': datetime_from.get('utc', ''),
                    'timestamp_local': datetime_from.get('local', ''),
                    'city': 'Astana',
                    'country_code': 'KZ',
                    'location_id': loc_id,
                    'location_name': loc_name,
                    'sensor_id': sensor_id,
                    'parameter': param_name,
                    'value': m.get('value'),
                    'units': param_units,
                }
                all_records.append(record)
    
    if all_records:
        # Сохраняем
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        filepath = os.path.join(DATA_DIR, "openaq_astana_all_params.csv")
        
        df_records = sorted(all_records, key=lambda x: (x['parameter'], x['timestamp_utc']))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=df_records[0].keys())
            writer.writeheader()
            writer.writerows(df_records)
        
        print(f"\n✓ Сохранено {len(df_records)} записей в {filepath}")
        
        # Статистика по параметрам
        params = {}
        for r in df_records:
            p = r['parameter']
            params[p] = params.get(p, 0) + 1
        
        print("\n📊 Статистика по параметрам:")
        for p, count in sorted(params.items()):
            print(f"   {p}: {count} записей")
    
    return all_records


if __name__ == "__main__":
    # 1. Поиск станций рядом с Астаной
    locations = search_locations_near_astana()
    
    # 2. Вывод информации о каждой станции
    if locations:
        print("\n" + "=" * 60)
        print("Детали станций:")
        print("=" * 60)
        
        for loc in locations:
            # Получаем полные детали
            details = get_location_details(loc.get('id'))
            if details:
                print_location_info(details)
    
    # 3. Поиск по всему Казахстану (дополнительно)
    kz_locations = search_kazakhstan_locations()
    
    if kz_locations:
        print("\n" + "=" * 60)
        print("Все станции в Казахстане:")
        print("=" * 60)
        
        for loc in kz_locations:
            details = get_location_details(loc.get('id'))
            if details:
                print_location_info(details)
    
    # 4. Собрать все данные по Астане
    all_locations = locations + [l for l in kz_locations if l not in locations]
    
    print("\n" + "=" * 60)
    user_input = input("Собрать все данные со станций Астаны? (y/n): ")
    if user_input.lower() == 'y':
        save_all_astana_data(all_locations)
    
    print("\n" + "=" * 60)
    print("Готово!")
    print("=" * 60)
