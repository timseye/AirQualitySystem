"""
Скрипт для проверки OpenAQ API и сбора данных
"""

import requests
import json

# OpenAQ API v3
BASE_URL = "https://api.openaq.org/v3"
API_KEY = "c5fb53161f8c1a4a07723fbb9a025c04b61471501b7c7f6b4839def76e1b08bd"

# Заголовки для авторизации
HEADERS = {
    "X-API-Key": API_KEY
}

def search_kazakhstan_locations():
    """Поиск станций в Казахстане"""
    print("=" * 60)
    print("1. Поиск станций в Казахстане (OpenAQ)")
    print("=" * 60)
    
    # Поиск по стране
    url = f"{BASE_URL}/locations"
    params = {
        "countries_id": 113,  # Kazakhstan ISO
        "limit": 100
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        data = response.json()
        
        if 'results' in data:
            locations = data['results']
            print(f"Найдено станций: {len(locations)}")
            
            for loc in locations[:20]:  # первые 20
                name = loc.get('name', 'Unknown')
                city = loc.get('locality', 'N/A')
                sensors = loc.get('sensors', [])
                print(f"  - {name} ({city}) | Сенсоров: {len(sensors)}")
            
            return data
        else:
            print(f"Ответ: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"Ошибка: {e}")
    
    return None


def search_astana_locations():
    """Поиск станций в Астане"""
    print("\n" + "=" * 60)
    print("2. Поиск станций в Астане/Нур-Султан")
    print("=" * 60)
    
    # Поиск по координатам Астаны (радиус 25км - максимум)
    url = f"{BASE_URL}/locations"
    params = {
        "coordinates": "51.1694,71.4491",  # Астана
        "radius": 25000,  # 25км (максимум)
        "limit": 50
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        data = response.json()
        
        if 'results' in data:
            locations = data['results']
            print(f"Найдено станций в радиусе 50км от Астаны: {len(locations)}")
            
            for loc in locations:
                loc_id = loc.get('id')
                name = loc.get('name', 'Unknown')
                provider = loc.get('provider', {}).get('name', 'N/A')
                coords = loc.get('coordinates', {})
                sensors = loc.get('sensors', [])
                
                print(f"\n  ID: {loc_id}")
                print(f"  Название: {name}")
                print(f"  Провайдер: {provider}")
                print(f"  Координаты: {coords}")
                print(f"  Сенсоры: {[s.get('parameter', {}).get('name') for s in sensors]}")
            
            return locations
        else:
            print(f"Ответ: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"Ошибка: {e}")
    
    return None


def get_measurements_for_location(location_id, limit=100):
    """Получить измерения для станции"""
    print(f"\n" + "=" * 60)
    print(f"3. Получение данных для станции ID={location_id}")
    print("=" * 60)
    
    url = f"{BASE_URL}/locations/{location_id}/measurements"
    params = {
        "limit": limit
    }
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        data = response.json()
        
        if 'results' in data:
            measurements = data['results']
            print(f"Получено измерений: {len(measurements)}")
            
            if measurements:
                print("\nПримеры данных:")
                for m in measurements[:5]:
                    param = m.get('parameter', {}).get('name', 'N/A')
                    value = m.get('value')
                    unit = m.get('parameter', {}).get('units', '')
                    time = m.get('datetime', {}).get('utc', 'N/A')
                    print(f"  {time} | {param}: {value} {unit}")
            
            return measurements
        else:
            print(f"Ответ: {json.dumps(data, indent=2)}")
            
    except Exception as e:
        print(f"Ошибка: {e}")
    
    return None


def check_countries():
    """Проверить ID Казахстана"""
    print("\n" + "=" * 60)
    print("0. Поиск ID страны Казахстан")
    print("=" * 60)
    
    url = f"{BASE_URL}/countries"
    params = {"limit": 200}
    
    try:
        response = requests.get(url, params=params, headers=HEADERS, timeout=30)
        data = response.json()
        
        if 'results' in data:
            for country in data['results']:
                if 'kazakh' in country.get('name', '').lower() or country.get('code') == 'KZ':
                    print(f"Найден: {country}")
                    return country.get('id')
        
    except Exception as e:
        print(f"Ошибка: {e}")
    
    return None


if __name__ == "__main__":
    # Сначала найдем ID Казахстана
    kz_id = check_countries()
    
    # Поиск станций в Казахстане
    search_kazakhstan_locations()
    
    # Поиск станций в Астане
    astana_locations = search_astana_locations()
    
    # Если нашли станции, получим данные с первой
    if astana_locations:
        first_loc_id = astana_locations[0].get('id')
        if first_loc_id:
            get_measurements_for_location(first_loc_id)
    
    print("\n" + "=" * 60)
    print("Готово!")
    print("=" * 60)
