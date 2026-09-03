"""
config.py
---------
Model 5 (Version 3): Day-Ahead Battery State of Charge (SoC) Forecasting
Antarctica Digital Twin | Bharati & Maitri Research Stations

FORECAST CONTRACT:
  - Prediction Timestamp: 18:00 Station Local Time on Day t
  - Forecast Horizon: End of Day t+1 (24-hour lead forecast of battery SoC %)
  - Target: battery_soc_percent at Day t+1
  - Information Boundary:
      ALLOWED (Known at 18:00 on Day t):
        * Battery SoC history up to Day t (soc_lag1, lag2, lag3, lag7, lag14)
        * Shifted trailing rolling statistics (roll3, roll7, roll14, roll30 means; roll7, roll14 stds; trend3, trend7)
        * Battery discharge telemetry observed up to Day t (discharge_lag1, roll7, roll14)
        * Historical electrical load up to Day t (load_lag1, lag2, lag3, lag7, roll7, roll14, trend3)
        * Historical generator dispatch up to Day t (generator_output_lag1, runtime_lag1, roll7)
        * Historical CHP waste heat recovery up to Day t (chp_heat_lag1, roll7)
        * Historical solar generation up to Day t (solar_gen_lag1, roll7)
        * Fuel stock reserve buffer at 18:00 cutoff on Day t (fuel_stock_lag1)
        * Scheduled population & roster for Day t+1 (scheduled_population, occupancy_pct, scientists, engineers, technicians, medical, pop_lag1, pop_trend7)
        * Day-ahead Numerical Weather Prediction (NWP) forecast for Day t+1 (fc_temperature_c, fc_wind_speed_kmh, fc_wind_gust_kmh, fc_solar_radiation_wm2, fc_solar_daylight_hours, fc_solar_elevation_deg, fc_snowfall_cm, fc_snow_depth_cm, fc_weather_severity, fc_weather_type_enc, fc_wind_chill_c, fc_heating_degree_days)
        * Astronomical solar geometry & calendar for Day t+1 (station_enc, month_sin/cos, doy_sin/cos, dow_sin/cos, quarter, is_shipping_season, is_polar_night, is_polar_day)
      FORBIDDEN (LEAKAGE):
        * Same-day charging power / energy (battery_charge_kw, charge energy on Day t+1)
        * Same-day discharging power / energy (battery_discharge_kw on Day t+1)
        * Same-day battery power flows (battery_to_load_kwh on Day t+1)
        * Same-day solar allocation (solar_to_load_kwh, solar_energy_kwh on Day t+1)
        * Same-day generator dispatch (generator_output_kw, generator_runtime_hours, active_generators on Day t+1)
        * Same-day electrical load (total_load_kw, heating_load_kw, sub-loads on Day t+1)
        * Same-day renewable generation (solar_generation_kw on Day t+1)
        * Same-day energy balances (daily_load_energy_kwh, generator_energy_kwh, unserved_energy_kwh on Day t+1)
        * Post-event operational outcomes (power_shortage_event, overload_flag, load_shedding_kwh on Day t+1)
        * Derived ratios / target derivatives (soc_delta using future SoC, renewable_share_percent on Day t+1)
"""

import os

# ── Directory Layout ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "data"))

MODELS_DIR = os.path.join(BASE_DIR, "models")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# ── Target Configuration ──────────────────────────────────────────────────────
TARGET_RAW = "battery_soc_percent"
TARGET_FORECAST = "battery_soc_percent_lead1"  # Target at end of Day t+1

RANDOM_SEED = 42

# ── Forecast-Safe Feature Schema (Day t+1 Pre-Forecast Features) ───────────────
FEATURE_COLUMNS = [
    # Station Identity
    "station_enc",                 # 0 = Maitri, 1 = Bharati
    
    # Astronomical Solar Geometry & Calendar for Day t+1
    "month_sin", "month_cos",
    "doy_sin", "doy_cos",
    "dow_sin", "dow_cos",
    "quarter",
    "is_shipping_season",          # Nov–Mar operational window
    "is_polar_night",              # Sun stays below horizon (0 solar daylight)
    "is_polar_day",                # 24h continuous solar daylight
    
    # Day-Ahead NWP Weather Forecast for Day t+1
    "fc_temperature_c",            # Forecast ambient temperature (°C)
    "fc_wind_speed_kmh",           # Forecast wind speed (km/h)
    "fc_wind_gust_kmh",            # Forecast wind gust (km/h)
    "fc_solar_radiation_wm2",      # Forecast solar irradiance (W/m²)
    "fc_solar_daylight_hours",     # Forecast daylight duration (hours)
    "fc_solar_elevation_deg",      # Noon solar elevation angle (degrees)
    "fc_snowfall_cm",              # Forecast snowfall (cm)
    "fc_snow_depth_cm",            # Forecast snow depth (cm)
    "fc_weather_severity",         # Weather severity index [0–1]
    "fc_weather_type_enc",         # Weather regime ordinal encoding (0–5)
    "fc_wind_chill_c",             # Forecast wind chill index (°C)
    "fc_heating_degree_days",      # Heating demand driver: max(0, 18 - fc_temperature_c)
    
    # Battery State of Charge History (Strictly t <= 0, observed up to 18:00 Day t)
    "soc_lag1",                    # SoC at 18:00 Day t (%)
    "soc_lag2",                    # SoC on Day t-1 (%)
    "soc_lag3",                    # SoC on Day t-2 (%)
    "soc_lag7",                    # SoC on Day t-6 (%)
    "soc_lag14",                   # SoC on Day t-13 (%)
    "soc_roll3_mean",              # 3-day rolling mean SoC (shifted)
    "soc_roll7_mean",              # 7-day rolling mean SoC (shifted)
    "soc_roll14_mean",             # 14-day rolling mean SoC (shifted)
    "soc_roll30_mean",             # 30-day rolling mean SoC (shifted)
    "soc_trend_3d",                # 3-day SoC rate of change (soc_lag1 - soc_lag3)
    "soc_trend_7d",                # 7-day SoC rate of change (soc_lag1 - soc_lag7)
    "soc_roll7_std",               # 7-day rolling SoC volatility
    "soc_roll14_std",              # 14-day rolling SoC volatility
    
    # Battery Discharge & Telemetry History (Strictly t <= 0)
    "battery_discharge_lag1",      # Discharge power observed on Day t (kW)
    "battery_discharge_roll7_mean",# 7-day rolling mean discharge (kW)
    "battery_discharge_roll14_mean",# 14-day rolling mean discharge (kW)
    
    # Historical Observed Weather & Thermal Persistence (Observed up to Day t)
    "obs_temp_lag1",               # Temperature observed on Day t (°C)
    "obs_temp_lag2",               # Temperature observed on Day t-1 (°C)
    "obs_temp_lag3",               # Temperature observed on Day t-2 (°C)
    "obs_temp_roll7_mean",         # 7-day rolling mean temperature (°C)
    "obs_temp_trend3",             # 3-day temperature gradient
    "obs_wind_lag1",               # Wind speed observed on Day t (km/h)
    "obs_weather_sev_lag1",        # Weather severity on Day t
    "obs_weather_sev_roll7",       # 7-day rolling mean weather severity
    
    # Scheduled Station Population for Day t+1
    "scheduled_population",        # Total personnel scheduled on station
    "scheduled_occupancy_pct",     # Station occupancy percentage (%)
    "scheduled_scientists",        # Research personnel count
    "scheduled_engineers",         # Engineering & operations count
    "scheduled_technicians",       # Technical maintenance count
    "scheduled_medical",           # Medical staff count
    "pop_lag1",                    # Station population on Day t
    "pop_trend7",                  # 7-day population change
    
    # Electrical Demand History (Strictly t <= 0)
    "load_lag1",                   # Observed electrical load on Day t (kW)
    "load_lag2",                   # Observed electrical load on Day t-1 (kW)
    "load_lag3",                   # Observed electrical load on Day t-2 (kW)
    "load_lag7",                   # Observed electrical load on Day t-6 (kW)
    "load_roll7_mean",             # 7-day rolling mean electrical load (kW)
    "load_roll14_mean",            # 14-day rolling mean electrical load (kW)
    "load_trend3",                 # 3-day load gradient
    
    # Historical Generator & CHP Support (Strictly t <= 0)
    "generator_output_lag1",       # Generator output on Day t (kW)
    "generator_runtime_lag1",      # Generator runtime on Day t (hours)
    "generator_roll7_mean",        # 7-day rolling mean generator output (kW)
    "chp_heat_lag1",               # CHP thermal recovery on Day t (kW)
    "chp_heat_roll7_mean",         # 7-day rolling mean CHP heat (kW)
    "fuel_stock_lag1",             # Fuel reserve buffer at 18:00 cutoff (Liters)
    
    # Historical Renewable Generation (Strictly t <= 0)
    "solar_gen_lag1",              # Solar power generated on Day t (kW)
    "solar_gen_roll7_mean",        # 7-day rolling mean solar generation (kW)
]

# ── Split Years ───────────────────────────────────────────────────────────────
TRAIN_YEAR_RANGE = (2003, 2019)
VAL_YEAR_RANGE = (2020, 2021)
TEST_YEAR = 2022

# ── Weather Encoding ──────────────────────────────────────────────────────────
ORDINAL_WEATHER = {
    "CLEAR": 0,
    "NORMAL": 1,
    "HIGH_WIND": 2,
    "HEAVY_SNOW": 3,
    "WHITEOUT": 4,
    "BLIZZARD": 5,
}

# ── Model Hyperparameters (Tuned for Day-Ahead SoC Forecasting) ───────────────
MODEL_CONFIGS = {
    "XGBoost": {
        "n_estimators": 400,
        "max_depth": 5,
        "learning_rate": 0.03,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_weight": 3,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
    },
    "LightGBM": {
        "n_estimators": 400,
        "max_depth": 6,
        "num_leaves": 31,
        "learning_rate": 0.03,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_samples": 20,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
        "verbose": -1,
    },
    "Random Forest": {
        "n_estimators": 300,
        "max_depth": 14,
        "min_samples_split": 5,
        "min_samples_leaf": 3,
        "max_features": "sqrt",
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
    },
    "CatBoost": {
        "iterations": 450,
        "depth": 6,
        "learning_rate": 0.03,
        "l2_leaf_reg": 3.0,
        "random_seed": RANDOM_SEED,
        "verbose": 0,
        "thread_count": -1,
    },
}

# ── Operational Stress Test Regimes ───────────────────────────────────────────
REGIMES = {
    "Winter": lambda df: df["month"].isin([4, 5, 6, 7, 8, 9]) | (df["is_polar_night"] == 1),
    "Summer": lambda df: df["month"].isin([11, 12, 1, 2]) | (df["is_polar_day"] == 1),
    "Storm Days": lambda df: df["fc_wind_speed_kmh"] >= 65.0,
    "Low Battery SoC": lambda df: df["soc_lag1"] < 40.0,
    "High Battery SoC": lambda df: df["soc_lag1"] >= 74.0,
    "High Population": lambda df: df["scheduled_population"] >= 40,
    "Normal Operation": lambda df: (
        (df["fc_wind_speed_kmh"] < 65.0) &
        (df["soc_lag1"] >= 40.0) &
        (df["soc_lag1"] < 74.0) &
        (df["scheduled_population"] < 40)
    ),
}
