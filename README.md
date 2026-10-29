# Weather Report: Historical Climate Analysis & Trends

An interactive climate analytics application that evaluates long-term temperature anomalies, warming trends, and extreme weather metrics across global cities.

## Data Source
- **Provider:** [Open-Meteo Historical Weather API](https://open-meteo.com/en/docs/historical-weather-api)
- **Geocoding:** [Open-Meteo Geocoding API](https://open-meteo.com/en/docs/geocoding-api)
- **Timeframe:** 1960 to present
- **Climatological Baseline:** 1961–1990 (WMO standard)

## Project Structure
```text
weather-report/
├── README.md            # Project description, setup, usage
├── requirements.txt     # Pinned Python dependencies
├── .gitignore           # Ignored artifacts, virtual envs, and data cache
├── app.py               # Streamlit application UI
├── data/                # Local cache directory for fetched CSV records
└── src/
    ├── __init__.py
    ├── config.py        # City coordinates, baseline years, thresholds
    ├── fetch.py         # Geocoding, API ingestion, local caching, error handling
    ├── processing.py    # Resampling, cleaning, pivots
    ├── analysis.py      # Statistical regressions, anomalies, extremes
    └── plots.py         # Matplotlib and Seaborn visualization functions