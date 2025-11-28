# Central Asia AQ-Weather-Mobility (Hourly)

**Version:** 0.1 (starter scaffold)  
**Geography:** Central Asia — Uzbekistan, Kazakhstan, Kyrgyzstan, Tajikistan, Turkmenistan  
**Resolution:** Hourly (primary), with a daily mobility proxy.  
**Time window (target):** 2019-01-01 — 2025-08-26 (expandable)

## Contents
- `schema.csv` — column definitions
- `cities.csv` — initial city list (can be extended or filtered by station coverage)
- `sample_hourly.csv` — tiny synthetic sample to show the format

## Sources (planned for real build)
- Air quality: OpenAQ v3 API (open data aggregator of reference monitors & low-cost sensors)
- Weather: Meteostat (hourly weather observations from national services), optional ERA5 for gaps
- Mobility proxy / traffic:
  - 2020–2022: Apple Mobility Trends (ended 2022‑04‑14), Google Community Mobility (ended 2022‑10‑15)
  - 2019–present: VIIRS Day/Night Band (daily radiance) as open mobility proxy
  - City GTFS/vehicle GPS where available (e.g., Astana bus GPS research dataset)
- Dust / aerosols: MERRA‑2 or CAMS (dust AOD@550nm), optionally MODIS/VIIRS fire hotspots

## Licensing
- OpenAQ: follow source license & attribution.
- Meteostat: CC BY‑NC 4.0; redistribution with restrictions — see terms. For Kaggle (non‑commercial), include attribution.
- VIIRS DNB & MERRA‑2/CAMS: open for research, follow NASA/ECMWF attribution rules.
- This combined dataset: CC BY 4.0 (for the *derived* features & joins, excluding any upstream license overrides).

## Known caveats
- Station coverage differs by city/country; some cities may have only PM sensors.
- Units may vary per source; we standardize PM in μg/m³; gases in ppb.
- Mobility proxy is a proxy (not direct congestion). Real `traffic_index` is null unless an open hourly source exists.

## Suggested tasks
- Forecast PM2.5/PM10 (1–72h), nowcasting, anomaly detection, causal analysis (dust storms, holidays).
- Model cards: include feature importance, SHAP on weather & mobility.

## Suggested splits
- Time‑based split: train ≤ 2024‑12‑31, val 2025‑01‑01..2025‑05‑31, test 2025‑06‑01..2025‑08‑26.

## Changelog
- 0.1 — scaffold released with schema & synthetic sample.
