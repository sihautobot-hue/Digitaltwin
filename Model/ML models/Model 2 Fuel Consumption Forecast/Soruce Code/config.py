"""
config.py
---------
Model 2 (Version 3): Day-Ahead Station Fuel Consumption Forecasting
Antarctica Digital Twin | SIH Project

FORECAST CONTRACT:
  - Prediction Issued: 18:00 Station Local Time on Day t
  - Target: fuel_consumed_today_liters for Day t+1 (24-hour lead forecast)
  - Information Boundary:
      ALLOWED (Known strictly BEFORE Day t+1 begins):
        * Observed fuel consumption history up to Day t (fuel_lag1, fuel_lag2, ...)
        * Trailing rolling fuel statistics (shifted before rolling: roll3, roll7, roll14, roll30, expanding, trend, std)
        * Current fuel stock level at 18:00 cutoff (Day t)
        * Days since last refueling event
        * Calendar & astronomical geometry for Day t+1 (month, doy, solar declination, polar night/day)
        * Day-ahead Numerical Weather Prediction (NWP) weather forecast for Day t+1
        * Scheduled population & crew roster for Day t+1
        * Battery SoC at 18:00 cutoff (Day t)
        * Historical generator thermal coupling (lag1 CHP waste heat)
        * Station identity (Maitri vs Bharati)
      FORBIDDEN (LEAKAGE):
        * Same-day (Day t+1) generator output (generator_output_kw)
        * Same-day generator runtime hours (generator_runtime_hours)
        * Same-day generator energy (generator_energy_kwh)
        * Same-day active generator staging count (active_generators)
        * Same-day load energy (daily_load_energy_kwh)
        * Same-day generator efficiency (fuel_efficiency_l_per_kwh)
        * Same-day energy balance components (solar_to_load, battery_to_load, unserved_energy)
        * Same-day electrical demand (total_load_kw, heating_load_kw)
        * Derived ratios encoding target (per_capita_load, gen_energy_proxy, renewable_share)
        * Same-day fuel days remaining (fuel_days_remaining = fuel_stock / fuel_consumed)
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "data"))

MODELS_DIR = os.path.join(BASE_DIR, "models_v3")
RESULTS_DIR = os.path.join(BASE_DIR, "results_v3")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

TARGET_RAW = "fuel_consumed_today_liters"
TARGET_NAME = "fuel_consumed_lead1"  # Target: Liters consumed on Day t+1

RANDOM_SEED = 42

# ── Forecast-Safe Pre-Forecast Features (Engineered for Day t+1) ───────────────
FEATURE_COLUMNS = [
    # Station Identity
    "station_enc",              # 0 = Maitri, 1 = Bharati

    # Calendar & Astronomical Geometry (Known exactly in advance for Day t+1)
    "month_sin", "month_cos",
    "doy_sin", "doy_cos",
    "dow_sin", "dow_cos",
    "quarter",
    "is_shipping_season",       # Antarctic shipping season (Nov–Mar)
    "is_polar_night",           # 24h darkness
    "is_polar_day",             # 24h continuous sunlight

    # Day-Ahead Numerical Weather Prediction (NWP) Forecast for Day t+1
    "fc_temperature_c",         # Forecasted mean ambient temperature (°C)
    "fc_wind_speed_kmh",        # Forecasted mean wind speed (km/h)
    "fc_wind_gust_kmh",         # Forecasted wind gust speed (km/h)
    "fc_solar_radiation_wm2",   # Forecasted solar irradiance (W/m²)
    "fc_solar_daylight_hours",  # Astronomical daylight duration (hours)
    "fc_solar_elevation_deg",   # Noon solar elevation angle (degrees)
    "fc_snowfall_cm",           # Forecasted snowfall precipitation (cm)
    "fc_snow_depth_cm",         # Forecasted snow pack depth (cm)
    "fc_weather_severity",      # Forecasted meteorological storm severity [0–1]
    "fc_weather_type_enc",      # Forecasted weather regime ordinal encoding
    "fc_wind_chill_c",          # Forecasted wind chill index (°C)
    "fc_katabatic_index",       # Katabatic wind severity proxy
    "fc_heating_degree_days",   # Heating demand driver: max(0, 18 - fc_temperature_c)

    # Observed Weather & Thermal Persistence (Observed up to Day t)
    "obs_temp_lag1",            # Ambient temperature on Day t
    "obs_temp_lag2",            # Temperature on Day t-1
    "obs_temp_lag3",            # Temperature on Day t-2
    "obs_temp_roll7_mean",      # 7-day rolling mean temperature (shift-then-roll)
    "obs_temp_trend3",          # 3-day temperature trajectory
    "obs_wind_lag1",            # Wind speed on Day t
    "obs_wind_roll7_mean",      # 7-day rolling mean wind speed
    "obs_weather_sev_lag1",     # Weather severity on Day t
    "obs_weather_sev_roll7",    # 7-day rolling mean weather severity

    # Scheduled Station Population Roster for Day t+1
    "scheduled_population",     # Scheduled crew roster count on station
    "scheduled_occupancy_pct",  # Scheduled station capacity utilization (%)
    "scheduled_scientists",     # Scheduled research staff (lab power/heat driver)
    "scheduled_engineers",      # Scheduled operations staff
    "scheduled_technicians",    # Scheduled technical/workshop staff
    "scheduled_medical",        # Scheduled medical staff
    "pop_lag1",                 # Personnel count on Day t
    "pop_trend7",               # 7-day net population shift

    # Historical Fuel Consumption Dynamics (Strictly t <= 0, Shifted Before Rolling)
    "fuel_lag1",                # Fuel consumed on Day t (Liters)
    "fuel_lag2",                # Fuel consumed on Day t-1 (Liters)
    "fuel_lag3",                # Fuel consumed on Day t-2 (Liters)
    "fuel_lag7",                # Fuel consumed same day last week (Liters)
    "fuel_lag14",               # Fuel consumed 2 weeks ago (Liters)
    "fuel_roll3_mean",          # 3-day trailing rolling mean fuel burn (L/day)
    "fuel_roll7_mean",          # 7-day trailing rolling mean fuel burn (L/day)
    "fuel_roll14_mean",         # 14-day trailing rolling mean fuel burn (L/day)
    "fuel_roll30_mean",         # 30-day trailing rolling mean fuel burn (L/day)
    "fuel_expanding_mean",      # Trailing cumulative expanding mean fuel burn (L/day)
    "fuel_roll7_std",           # 7-day trailing fuel consumption volatility
    "fuel_roll14_std",          # 14-day trailing fuel consumption volatility
    "fuel_trend_3d",            # 3-day fuel burn trajectory (fuel_lag1 - fuel_lag3)
    "fuel_trend_7d",            # Weekly fuel burn trajectory (fuel_lag1 - fuel_lag7)

    # Current Fuel Inventory & Logistics State at 18:00 Cutoff (Day t)
    "fuel_stock_start_liters",  # Fuel inventory at 18:00 cutoff (Liters)
    "fuel_stock_lag1",          # Fuel inventory yesterday
    "fuel_stock_drawdown_3d",   # 3-day fuel inventory net drawdown (Liters)
    "days_since_refuel_start",  # Days elapsed since previous refueling
    "fuel_shipments_pending",   # Number of inbound fuel tankers pending
    "fuel_eta_days",            # Estimated days until next scheduled tanker arrival

    # Past Generator & Thermal Telemetry (Observed on Day t, t <= 0)
    "gen_output_lag1",          # Yesterday's generator output (kW)
    "gen_runtime_lag1",         # Yesterday's generator runtime (hours)
    "gen_utilization_lag1",     # Yesterday's generator load factor
    "chp_heat_lag1",            # Generator waste heat recovered on Day t (kW)
    "chp_heat_roll7_mean",      # 7-day rolling mean CHP waste heat (kW)

    # Storage State & Risk at 18:00 Cutoff (Day t)
    "battery_soc_start_pct",    # Battery SoC at 18:00 cutoff (%)
    "soc_lag1",                 # Battery SoC on Day t-1
    "soc_delta_lag1",           # 24-hour battery SoC rate of change
    "fuel_risk_lag1",           # Fuel sub-system risk index on Day t
    "power_risk_lag1",          # Power sub-system risk index on Day t
    "overall_risk_lag1",        # Overall composite station risk index on Day t
    "risk_roll7_mean",          # 7-day trailing rolling mean station risk
]

# ── Chronological Split Windows ───────────────────────────────────────────────
SPLIT_CONFIG = {
    "train_end_year": 2019,     # Train: 2003–2019
    "val_start_year": 2020,     # Validation: 2020–2021
    "val_end_year": 2021,
    "test_year": 2022,          # Test: 2022
}

# ── Algorithm Portfolio Hyperparameters ───────────────────────────────────────
MODEL_CONFIGS = {
    "LinearRegression": {},
    "ElasticNet": {
        "alpha": 0.1,
        "l1_ratio": 0.5,
        "max_iter": 2000,
        "random_state": RANDOM_SEED,
    },
    "RandomForest": {
        "n_estimators": 250,
        "max_depth": 18,
        "min_samples_split": 5,
        "min_samples_leaf": 3,
        "max_features": "sqrt",
        "n_jobs": -1,
        "random_state": RANDOM_SEED,
    },
    "ExtraTrees": {
        "n_estimators": 250,
        "max_depth": 18,
        "min_samples_split": 5,
        "min_samples_leaf": 3,
        "max_features": "sqrt",
        "n_jobs": -1,
        "random_state": RANDOM_SEED,
    },
    "HistGradientBoosting": {
        "max_iter": 500,
        "learning_rate": 0.03,
        "max_depth": 6,
        "min_samples_leaf": 20,
        "l2_regularization": 1.0,
        "random_state": RANDOM_SEED,
    },
    "XGBoost": {
        "n_estimators": 1000,
        "learning_rate": 0.03,
        "max_depth": 6,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "tree_method": "hist",
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
    },
    "LightGBM": {
        "objective": "regression",
        "metric": "rmse",
        "n_estimators": 1500,
        "learning_rate": 0.03,
        "num_leaves": 63,
        "max_depth": 8,
        "min_child_samples": 25,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "reg_alpha": 0.1,
        "reg_lambda": 0.5,
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
        "verbosity": -1,
    },
    "CatBoost": {
        "iterations": 1200,
        "learning_rate": 0.03,
        "depth": 6,
        "l2_leaf_reg": 3.0,
        "random_seed": RANDOM_SEED,
        "verbose": False,
        "thread_count": -1,
    },
}
