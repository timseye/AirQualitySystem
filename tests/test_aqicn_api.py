"""
Тестовый скрипт для проверки AQICN API
Проверяем какие данные доступны для Астаны
"""

import requests
import json

# Твой API токен
API_TOKEN = "d59d891eb5c761c98d06962f8294037535e8d1d7"

# Базовый URL
BASE_URL = "https://api.waqi.info"


def test_astana_feed():
    """Получить текущие данные по Астане"""
    url = f"{BASE_URL}/feed/astana/?token={API_TOKEN}"
    
    print("=" * 50)
    print("1. Запрос данных для Астаны")
    print("=" * 50)
    
    response = requests.get(url)
    data = response.json()
    
    print(f"Статус: {data.get('status')}")
    print(f"\nПолный ответ:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    return data


def test_geo_search():
    """Поиск станций по координатам Астаны"""
    # Координаты Астаны
    lat, lng = 51.1694, 71.4491
    
    url = f"{BASE_URL}/feed/geo:{lat};{lng}/?token={API_TOKEN}"
    
    print("\n" + "=" * 50)
    print("2. Поиск по координатам Астаны")
    print("=" * 50)
    
    response = requests.get(url)
    data = response.json()
    
    print(f"Статус: {data.get('status')}")
    if data.get('status') == 'ok':
        info = data.get('data', {})
        print(f"Станция: {info.get('city', {}).get('name')}")
        print(f"AQI: {info.get('aqi')}")
    
    return data


def test_search_stations():
    """Поиск всех станций в Казахстане"""
    url = f"{BASE_URL}/search/?keyword=kazakhstan&token={API_TOKEN}"
    
    print("\n" + "=" * 50)
    print("3. Поиск станций в Казахстане")
    print("=" * 50)
    
    response = requests.get(url)
    data = response.json()
    
    print(f"Статус: {data.get('status')}")
    if data.get('status') == 'ok':
        stations = data.get('data', [])
        print(f"Найдено станций: {len(stations)}")
        print("\nСписок станций:")
        for station in stations[:10]:  # первые 10
            print(f"  - {station.get('station', {}).get('name')}")
    
    return data


def test_us_embassy():
    """Проверить данные US Embassy (reference)"""
    # Пробуем разные варианты названия
    keywords = ["US Embassy Astana", "astana us embassy", "nur-sultan embassy"]
    
    print("\n" + "=" * 50)
    print("4. Поиск US Embassy станции")
    print("=" * 50)
    
    for keyword in keywords:
        url = f"{BASE_URL}/search/?keyword={keyword}&token={API_TOKEN}"
        response = requests.get(url)
        data = response.json()
        
        if data.get('status') == 'ok' and data.get('data'):
            print(f"Найдено по '{keyword}':")
            for station in data.get('data', []):
                print(f"  - {station.get('station', {}).get('name')}")


if __name__ == "__main__":
    # Запускаем все тесты
    test_astana_feed()
    test_geo_search()
    test_search_stations()
    test_us_embassy()
    
    print("\n" + "=" * 50)
    print("Готово! Посмотри какие данные доступны.")
    print("=" * 50)
