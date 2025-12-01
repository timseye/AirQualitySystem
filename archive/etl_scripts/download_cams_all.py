"""
Загрузка и обработка всех данных CAMS для Астаны (2018-2024)

CAMS EAC4 variables:
- Single level (surface): PM2.5, PM10
- Multi-level (need pressure_level): NO2, O3, SO2, CO
"""

import cdsapi
import os
import zipfile
import xarray as xr
import pandas as pd
from datetime import datetime

DATA_DIR = "data/raw/cams"

ASTANA_BBOX = {
    "north": 52.5,
    "west": 70.0,
    "south": 50.5,
    "east": 73.0
}

# Single level (surface) variables - these work with netcdf
SINGLE_LEVEL_VARS = [
    "particulate_matter_2.5um",
    "particulate_matter_10um",
]

# Multi-level variables - need pressure level 1000 hPa (surface) or model level 60
MULTI_LEVEL_VARS = [
    "nitrogen_dioxide",
    "ozone",
    "sulphur_dioxide",
    "carbon_monoxide",
]


def download_year(year: int):
    """Загрузить данные за год - отдельно PM и газы"""
    
    # Разбиваем на кварталы для надежности
    quarters = [
        (f"{year}-01-01", f"{year}-03-31"),
        (f"{year}-04-01", f"{year}-06-30"),
        (f"{year}-07-01", f"{year}-09-30"),
        (f"{year}-10-01", f"{year}-12-31"),
    ]
    
    files = []
    client = cdsapi.Client()
    
    for i, (start, end) in enumerate(quarters, 1):
        # 1. Download PM (single level)
        pm_filename = f"cams_astana_{year}_q{i}_pm.nc.zip"
        pm_filepath = os.path.join(DATA_DIR, pm_filename)
        
        if os.path.exists(pm_filepath):
            print(f"  Q{i} PM: уже скачано")
            files.append(pm_filepath)
        else:
            print(f"  Q{i} PM: {start} → {end}...")
            
            request = {
                "variable": SINGLE_LEVEL_VARS,
                "date": f"{start}/{end}",
                "time": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
                "area": [ASTANA_BBOX["north"], ASTANA_BBOX["west"], ASTANA_BBOX["south"], ASTANA_BBOX["east"]],
                "data_format": "netcdf_zip"
            }
            
            try:
                client.retrieve("cams-global-reanalysis-eac4", request, pm_filepath)
                files.append(pm_filepath)
                print(f"      ✓ PM готово")
            except Exception as e:
                print(f"      ✗ Ошибка PM: {e}")
        
        # 2. Download gases (multi-level, 1000 hPa = surface)
        gas_filename = f"cams_astana_{year}_q{i}_gas.nc.zip"
        gas_filepath = os.path.join(DATA_DIR, gas_filename)
        
        if os.path.exists(gas_filepath):
            print(f"  Q{i} Gas: уже скачано")
            files.append(gas_filepath)
        else:
            print(f"  Q{i} Gas: {start} → {end}...")
            
            request = {
                "variable": MULTI_LEVEL_VARS,
                "pressure_level": ["1000"],  # Surface level
                "date": f"{start}/{end}",
                "time": ["00:00", "03:00", "06:00", "09:00", "12:00", "15:00", "18:00", "21:00"],
                "area": [ASTANA_BBOX["north"], ASTANA_BBOX["west"], ASTANA_BBOX["south"], ASTANA_BBOX["east"]],
                "data_format": "netcdf_zip"
            }
            
            try:
                client.retrieve("cams-global-reanalysis-eac4", request, gas_filepath)
                files.append(gas_filepath)
                print(f"      ✓ Gas готово")
            except Exception as e:
                print(f"      ✗ Ошибка Gas: {e}")
    
    return files


def download_all_years():
    """Загрузить все годы"""
    print("=" * 60)
    print("CAMS Global Reanalysis - Загрузка данных")
    print("=" * 60)
    
    all_files = []
    
    for year in range(2018, 2025):
        print(f"\n{year}:")
        files = download_year(year)
        all_files.extend(files)
    
    print(f"\n✓ Всего файлов: {len(all_files)}")
    return all_files


if __name__ == "__main__":
    os.makedirs(DATA_DIR, exist_ok=True)
    download_all_years()
