"""
Main Streamlit application for the Climate Analysis Dashboard.
Interactive visualization of historical temperature trends, anomalies, and extremes.
Includes custom city geocoding, live map, export options, and side-by-side city comparison.
"""
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from src.config import DEFAULT_CITIES
from src.data_processing import (
    calculate_baseline,
    compute_temperature_anomalies,
    create_monthly_matrix,
    resample_annual,
)
from src.fetch import fetch_weather_data
from src.plots import plot_monthly_heatmap, plot_temperature_anomalies

# Page configuration
st.set_page_config(
    page_title="Global Climate Analysis Dashboard",
    page_icon="🌍",
    layout="wide",
)

st.title("🌍 Global Climate & Temperature Trend Dashboard")
st.markdown(
    "Interactive exploration of historical daily weather data (1960–2025) "
    "sourced from **Open-Meteo**, referenced against the WMO climatological baseline (1961–1990)."
)

# ---------------------------------------------------------
# Sidebar Controls & Feature 1: Custom City Search
# ---------------------------------------------------------
st.sidebar.header("Configuration & Filters")

available_cities = list(DEFAULT_CITIES.keys())
selected_city_default = st.sidebar.selectbox("Select Default City", options=available_cities, index=0)

custom_city = st.sidebar.text_input(
    "Or search any city in the world:",
    placeholder="e.g. Tunis, New York, Berlin",
).strip()

# If custom city is entered, use it; otherwise fallback to selectbox
selected_city = custom_city if custom_city else selected_city_default

min_year = 1960
max_year = 2025
year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(1960, 2025),
)

# ---------------------------------------------------------
# Data Loading & Processing
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def get_city_data(city: str) -> pd.DataFrame:
    return fetch_weather_data(city)

try:
    with st.spinner(f"Loading data for {selected_city}..."):
        raw_df = get_city_data(selected_city)
except Exception as err:
    st.error(f"Could not load data for '{selected_city}': {err}")
    st.stop()

# Filter by selected year range
raw_df["date"] = pd.to_datetime(raw_df["date"])
filtered_df = raw_df[
    (raw_df["date"].dt.year >= year_range[0]) & (raw_df["date"].dt.year <= year_range[1])
]

# Baseline and anomalies
baseline_val = calculate_baseline(raw_df)
anomalies_df = compute_temperature_anomalies(filtered_df)
annual_df = resample_annual(filtered_df)

# ---------------------------------------------------------
# Feature 2: Interactive Location Map in Sidebar
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("📍 Location Coordinates")
lat = float(raw_df["latitude"].iloc[0])
lon = float(raw_df["longitude"].iloc[0])
st.sidebar.caption(f"Lat: `{lat:.4f}` | Lon: `{lon:.4f}`")

map_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
st.sidebar.map(map_df, zoom=4)

# ---------------------------------------------------------
# Feature 3: Download Button in Sidebar
# ---------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("💾 Export Data")
csv_data = anomalies_df.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(
    label=f"📥 Download {selected_city} Anomalies (CSV)",
    data=csv_data,
    file_name=f"{selected_city.lower()}_anomalies_{year_range[0]}_{year_range[1]}.csv",
    mime="text/csv",
)

# ---------------------------------------------------------
# Top Metric KPI Cards
# ---------------------------------------------------------
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="Climatological Baseline (1961–1990)",
        value=f"{baseline_val:.2f} °C",
    )

with col2:
    recent_mean = annual_df["temperature_2m_mean"].iloc[-1]
    last_year = int(annual_df["year"].iloc[-1])
    st.metric(
        label=f"Mean Temperature ({last_year})",
        value=f"{recent_mean:.2f} °C",
    )

with col3:
    recent_anomaly = anomalies_df["anomaly"].iloc[-1]
    st.metric(
        label=f"Latest Anomaly ({last_year})",
        value=f"{recent_anomaly:+.2f} °C",
        delta=f"{recent_anomaly:+.2f} °C",
        delta_color="inverse",
    )

with col4:
    total_precip_recent = annual_df["precipitation_sum"].iloc[-1]
    st.metric(
        label=f"Total Rainfall ({last_year})",
        value=f"{total_precip_recent:.0f} mm",
    )

st.markdown("---")

# ---------------------------------------------------------
# Main Visualizations & Feature 4: Side-by-Side Comparison
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Temperature Anomalies",
    "🗺️ Monthly Heatmap",
    "🆚 Compare Two Cities",
    "📊 City Summary Table",
])

with tab1:
    st.subheader(f"Temperature Anomalies relative to 1961–1990 Baseline — {selected_city}")
    fig_anom, _ = plot_temperature_anomalies(anomalies_df, selected_city)
    st.pyplot(fig_anom)
    plt.close(fig_anom)

with tab2:
    st.subheader(f"Monthly Temperature Climatology — {selected_city}")
    matrix_df = create_monthly_matrix(filtered_df)
    fig_heat, _ = plot_monthly_heatmap(matrix_df, selected_city)
    st.pyplot(fig_heat)
    plt.close(fig_heat)

with tab3:
    st.subheader("Direct Comparison: City A vs City B")
    cmp_col1, cmp_col2 = st.columns(2)
    with cmp_col1:
        city_a = st.selectbox("Select First City", options=available_cities, index=0, key="cmp_city_a")
    with cmp_col2:
        city_b = st.selectbox("Select Second City", options=available_cities, index=1, key="cmp_city_b")

    df_a = get_city_data(city_a)
    df_b = get_city_data(city_b)

    anom_a = compute_temperature_anomalies(df_a)
    anom_b = compute_temperature_anomalies(df_b)

    fig_cmp, ax_cmp = plt.subplots(figsize=(12, 5))
    ax_cmp.plot(
        anom_a["year"],
        anom_a["anomaly_rolling_5y"],
        label=f"{city_a} (5-yr rolling anomaly)",
        color="#d73027",
        linewidth=2.5,
    )
    ax_cmp.plot(
        anom_b["year"],
        anom_b["anomaly_rolling_5y"],
        label=f"{city_b} (5-yr rolling anomaly)",
        color="#4575b4",
        linewidth=2.5,
    )
    ax_cmp.axhline(0, color="gray", linestyle="--", linewidth=1.0)
    ax_cmp.set_title(f"Warming Trajectory Comparison: {city_a} vs {city_b}", fontsize=13, fontweight="bold")
    ax_cmp.set_xlabel("Year")
    ax_cmp.set_ylabel("Temperature Anomaly (°C)")
    ax_cmp.grid(True, linestyle=":", alpha=0.6)
    ax_cmp.legend(frameon=True)
    st.pyplot(fig_cmp)
    plt.close(fig_cmp)

with tab4:
    st.subheader("Cross-City Statistical Climate Summary (1960–2025)")
    metrics_path = Path("data/climate_summary_metrics.csv")
    if metrics_path.exists():
        summary_metrics = pd.read_csv(metrics_path)
        st.dataframe(
            summary_metrics.style.format({
                "warming_rate_per_decade": "{:+.3f} °C/decade",
                "p_value": "{:.2e}",
                "r_squared": "{:.3f}",
                "avg_tropical_nights_early": "{:.1f}",
                "avg_tropical_nights_recent": "{:.1f}",
                "avg_heatwave_days_early": "{:.1f}",
                "avg_heatwave_days_recent": "{:.1f}",
            }),
            use_container_width=True,
        )
    else:
        st.info("Run `python -m src.analysis` in your terminal to generate the cross-city metrics table.")