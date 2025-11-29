"""
Скрипт для сбора исторических погодных данных из Open-Meteo API
Астана: 2018-2025
Open-Meteo - бесплатный API без ключа
"""

import requests
import pandas as pd
import os
from datetime import datetime, timedelta

# Астана координаты
ASTANA_LAT = 51.1694
ASTANA_LON = 71.4491

# Папка для данных
DATA_DIR = "data/raw/openmeteo"

# Open-Meteo Historical API
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def ensure_data_dir():
    """Создать папку для данных"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Создана папка: {DATA_DIR}")


def fetch_weather_chunk(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Получить погодные данные за период (max ~2 года на запрос)
    
    Args:
        start_date: Начало периода (YYYY-MM-DD)
        end_date: Конец периода (YYYY-MM-DD)
    
    Returns:
        DataFrame с почасовыми данными
    """
    params = {
        "latitude": ASTANA_LAT,
        "longitude": ASTANA_LON,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": [
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
            "wind_gusts_10m",
        ],
        "timezone": "Asia/Almaty"
    }
    
    print(f"  Запрос: {start_date} → {end_date}...")
    
    try:
        response = requests.get(ARCHIVE_URL, params=params, timeout=120)
        response.raise_for_status()
        data = response.json()
        
        if "hourly" in data:
            hourly = data["hourly"]
            df = pd.DataFrame(hourly)
            df["time"] = pd.to_datetime(df["time"])
            print(f"  ✓ Получено {len(df)} записей")
            return df
        else:
            print(f"  ✗ Нет данных в ответе")
            return pd.DataFrame()
            
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        return pd.DataFrame()


def collect_full_history(start_year: int = 2018, end_date: str = None) -> pd.DataFrame:
    """
    Собрать полную историю погоды по частям (2 года max на запрос)
    
    Args:
        start_year: Начальный год
        end_date: Конечная дата (по умолчанию вчера)
    
    Returns:
        DataFrame со всеми данными
    """
    if end_date is None:
        # Open-Meteo archive обычно отстаёт на 5-7 дней
        end_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    print("=" * 60)
    print("Open-Meteo Historical Weather Collection")
    print(f"Локация: Астана ({ASTANA_LAT}, {ASTANA_LON})")
    print(f"Период: {start_year}-01-01 → {end_date}")
    print("=" * 60)
    
    all_data = []
    current_start = datetime(start_year, 1, 1)
    final_end = datetime.strptime(end_date, "%Y-%m-%d")
    
    while current_start < final_end:
        # Chunk по 2 года (730 дней max для API)
        chunk_end = min(current_start + timedelta(days=700), final_end)
        
        df_chunk = fetch_weather_chunk(
            current_start.strftime("%Y-%m-%d"),
            chunk_end.strftime("%Y-%m-%d")
        )
        
        if not df_chunk.empty:
            all_data.append(df_chunk)
        
        current_start = chunk_end + timedelta(days=1)
    
    if all_data:
        df_full = pd.concat(all_data, ignore_index=True)
        df_full = df_full.drop_duplicates(subset=["time"]).sort_values("time")
        print(f"\n✓ Всего собрано: {len(df_full)} записей")
        return df_full
    
    return pd.DataFrame()


def save_to_csv(df: pd.DataFrame, filename: str = None):
    """Сохранить данные в CSV"""
    if df.empty:
        print("Нет данных для сохранения")
        return
    
    ensure_data_dir()
    
    if filename is None:
        filename = "astana_weather_historical.csv"
    
    filepath = os.path.join(DATA_DIR, filename)
    
    # Переименуем колонки в более понятные имена
    column_mapping = {
        "time": "timestamp_local",
        "temperature_2m": "temp_c",
        "relative_humidity_2m": "humidity_pct",
        "dew_point_2m": "dew_point_c",
        "apparent_temperature": "feels_like_c",
        "precipitation": "precip_mm",
        "rain": "rain_mm",
        "snowfall": "snow_cm",
        "snow_depth": "snow_depth_m",
        "weather_code": "weather_code",
        "pressure_msl": "pressure_msl_hpa",
        "surface_pressure": "surface_pressure_hpa",
        "cloud_cover": "cloud_cover_pct",
        "wind_speed_10m": "wind_speed_ms",
        "wind_direction_10m": "wind_dir_deg",
        "wind_gusts_10m": "wind_gust_ms",
    }
    
    df_save = df.rename(columns=column_mapping)
    
    # Добавим метаданные
    df_save["city"] = "Astana"
    df_save["country_code"] = "KZ"
    df_save["lat"] = ASTANA_LAT
    df_save["lon"] = ASTANA_LON
    df_save["data_source"] = "open-meteo"
    
    df_save.to_csv(filepath, index=False)
    
    print(f"\n{'='*60}")
    print(f"Сохранено в: {filepath}")
    print(f"Период: {df_save['timestamp_local'].min()} → {df_save['timestamp_local'].max()}")
    print(f"Записей: {len(df_save)}")
    print("=" * 60)
    
    return filepath


def show_summary(df: pd.DataFrame):
    """Показать сводку по данным"""
    if df.empty:
        return
    
    print("\n📊 Сводка по погодным данным:")
    print("-" * 40)
    
    # Переименуем для отображения
    cols = {
        "temperature_2m": "Температура (°C)",
        "relative_humidity_2m": "Влажность (%)",
        "wind_speed_10m": "Скорость ветра (м/с)",
        "precipitation": "Осадки (мм)",
    }
    
    for col, name in cols.items():
        if col in df.columns:
            print(f"{name}:")
            print(f"  min: {df[col].min():.1f}, max: {df[col].max():.1f}, avg: {df[col].mean():.1f}")


if __name__ == "__main__":
    # Собираем данные с 2018 года
    df = collect_full_history(start_year=2018)
    
    if not df.empty:
        show_summary(df)
        save_to_csv(df)
    else:
        print("Не удалось собрать данные")
