"""
Скрипт для загрузки данных CAMS Global Reanalysis (EAC4)
для Астаны: PM2.5, PM10, NO2, O3, SO2, CO
Период: 2018-2024 (данные доступны до 2024)

CAMS EAC4 дает реанализ качества воздуха с разрешением ~80км
https://ads.atmosphere.copernicus.eu/datasets/cams-global-reanalysis-eac4
"""

import cdsapi
import os
from datetime import datetime, timedelta

# Папка для данных
DATA_DIR = "data/raw/cams"

# Астана координаты (с запасом для региона)
# North/West/South/East
ASTANA_BBOX = {
    "north": 52.5,
    "west": 70.0,
    "south": 50.5,
    "east": 73.0
}

# Переменные для загрузки
# Single level variables (поверхностные)
SINGLE_LEVEL_VARS = [
    "particulate_matter_2.5um",       # PM2.5
    "particulate_matter_10um",        # PM10
    "nitrogen_dioxide",               # NO2
    "ozone",                          # O3 (surface)
    "sulphur_dioxide",                # SO2
    "carbon_monoxide",                # CO
    "dust_aerosol_optical_depth_550nm",  # Dust AOD
    "total_aerosol_optical_depth_550nm", # Total AOD
]


def ensure_data_dir():
    """Создать папку для данных"""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Создана папка: {DATA_DIR}")


def download_cams_year(year: int, variables: list = None, single_level: bool = True):
    """
    Загрузить данные CAMS за год
    
    Args:
        year: Год (2003-2024 доступны)
        variables: Список переменных
        single_level: True для поверхностных данных
    """
    if variables is None:
        variables = SINGLE_LEVEL_VARS
    
    ensure_data_dir()
    
    print(f"\n{'='*60}")
    print(f"Загрузка CAMS EAC4 за {year}")
    print(f"Переменные: {len(variables)}")
    print(f"Регион: Астана ({ASTANA_BBOX})")
    print(f"{'='*60}")
    
    # Формируем запрос
    # Даты: весь год
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    request = {
        "variable": variables,
        "date": f"{start_date}/{end_date}",
        "time": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
        "area": [
            ASTANA_BBOX["north"],
            ASTANA_BBOX["west"],
            ASTANA_BBOX["south"],
            ASTANA_BBOX["east"]
        ],
        "data_format": "netcdf_zip"  # NetCDF easier to process
    }
    
    # Имя файла
    filename = f"cams_astana_{year}.nc.zip"
    filepath = os.path.join(DATA_DIR, filename)
    
    print(f"\nЗапрос данных...")
    print(f"Это может занять несколько минут...")
    
    try:
        client = cdsapi.Client()
        client.retrieve(
            "cams-global-reanalysis-eac4",
            request,
            filepath
        )
        print(f"\n✓ Сохранено: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        return None


def download_cams_monthly(year: int, month: int, variables: list = None):
    """
    Загрузить данные CAMS за месяц (для больших объемов)
    """
    if variables is None:
        variables = SINGLE_LEVEL_VARS
    
    ensure_data_dir()
    
    # Последний день месяца
    if month == 12:
        last_day = 31
    else:
        next_month = datetime(year, month + 1, 1)
        last_day = (next_month - timedelta(days=1)).day
    
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-{last_day}"
    
    print(f"Загрузка: {start_date} → {end_date}")
    
    request = {
        "variable": variables,
        "date": f"{start_date}/{end_date}",
        "time": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
        "area": [
            ASTANA_BBOX["north"],
            ASTANA_BBOX["west"],
            ASTANA_BBOX["south"],
            ASTANA_BBOX["east"]
        ],
        "data_format": "netcdf_zip"
    }
    
    filename = f"cams_astana_{year}_{month:02d}.nc.zip"
    filepath = os.path.join(DATA_DIR, filename)
    
    try:
        client = cdsapi.Client()
        client.retrieve(
            "cams-global-reanalysis-eac4",
            request,
            filepath
        )
        print(f"  ✓ {filepath}")
        return filepath
        
    except Exception as e:
        print(f"  ✗ Ошибка: {e}")
        return None


def download_all_years(start_year: int = 2018, end_year: int = 2024):
    """
    Загрузить данные за все годы
    
    Note: CAMS EAC4 доступен 2003-01-01 до ~текущий-6месяцев
    """
    print("=" * 60)
    print("CAMS Global Reanalysis (EAC4) Download")
    print(f"Период: {start_year} - {end_year}")
    print("=" * 60)
    
    downloaded = []
    
    for year in range(start_year, end_year + 1):
        filepath = download_cams_year(year)
        if filepath:
            downloaded.append(filepath)
    
    print(f"\n{'='*60}")
    print(f"Загружено файлов: {len(downloaded)}")
    print("=" * 60)
    
    return downloaded


if __name__ == "__main__":
    # Загружаем данные за 2018-2024
    # Начнем с одного года для теста
    print("Тестовая загрузка CAMS за 2024...")
    
    # Можно начать с малого - один месяц
    download_cams_monthly(2024, 1, variables=[
        "particulate_matter_2.5um",
        "particulate_matter_10um",
        "nitrogen_dioxide",
        "ozone",
        "sulphur_dioxide",
        "carbon_monoxide",
    ])
