"""
config.py
---------
Model 1 (Version 3): Day-Ahead Station Power Load Forecasting
Antarctica Digital Twin | SIH Project

FORECAST CONTRACT:
  - Prediction Timestamp: 18:00 Station Local Time on Day t
  - Forecast Horizon: Next Day t+1 (00:00 to 23:59 Average Station Load)
  - Target: total_load_kw at Day t+1
  - Information Boundary:
      ALLOWED:
        * Past observed load up to Day t (load_lag1, lag2, etc.)
        * Trailing rolling statistics strictly shifted before rolling
        * Scheduled population & crew breakdown for Day t+1
        * Astronomical solar geometry for Day t+1 (known in advance)
        * Day-ahead Numerical Weather Prediction (NWP) forecasts for Day t+1
        * Station identity & physical topology
        * Energy storage buffer state at 18:00 cutoff (battery SoC, fuel stock)
      FORBIDDEN (LEAKAGE):
        * Same-day sub-load components (accommodation, kitchen, lab, heating, etc.)
        * Same-day generator dispatch (output kW, runtime hours, active units)
        * Same-day battery power flows (charge/discharge kW, battery_to_load)
        * Downstream energy balances (daily_load_energy, generator_energy, unserved_energy)
        * Post-event operational outcomes (overload_flag, load_shedding, power_shortage)
        * Derived ratios encoding target (per_capita_load of Day t+1, renewable_share)
"""

import os

# ── Directory Layout ──────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "data"))

MODELS_DIR = os.path.join(BASE_DIR, "models_v3")
RESULTS_DIR = os.path.join(BASE_DIR, "results_v3")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

# ── Contract Targets ──────────────────────────────────────────────────────────
TARGET_RAW = "total_load_kw"
TARGET_NAME = "total_load_kw_lead1"  # Day t+1 forecast target

RANDOM_SEED = 42

# ── Forecast-Safe Pre-Forecast Features (Engineered for Day t+1) ───────────────
FEATURE_COLUMNS = [
    # Station Identity
    "station_enc",              # 0 = Maitri, 1 = Bharati
    
    # Calendar & Astronomical Solar Geometry (Known exactly for Day t+1)
    "month_sin", "month_cos",
    "doy_sin", "doy_cos",
    "dow_sin", "dow_cos",
    "quarter",
    "is_shipping_season",       # Antarctic operational season (Nov–Mar)
    "is_polar_night",           # Sun stays below horizon (0 solar daylight)
    "is_polar_day",             # Continuous 24h sunlight
    
    # Day-Ahead Numerical Weather Prediction (NWP) Forecast for Day t+1
    "fc_temperature_c",         # Forecasted mean ambient temperature (°C)
    "fc_wind_speed_kmh",        # Forecasted mean wind speed (km/h)
    "fc_wind_gust_kmh",         # Forecasted wind gust (km/h)
    "fc_solar_radiation_wm2",   # Forecasted solar irradiance (W/m²)
    "fc_solar_daylight_hours",  # Astronomical daylight duration (hours)
    "fc_solar_elevation_deg",   # Noon solar elevation angle (degrees)
    "fc_snowfall_cm",           # Forecasted snowfall precipitation (cm)
    "fc_snow_depth_cm",         # Forecasted snow depth (cm)
    "fc_weather_severity",      # Forecasted meteorological severity index [0–1]
    "fc_weather_type_enc",      # Forecasted weather regime ordinal encoding
    "fc_wind_chill_c",          # Forecasted wind chill index (°C)
    "fc_katabatic_index",       # Katabatic wind severity proxy
    "fc_heating_degree_days",   # Heating demand driver: max(0, 18 - fc_temperature_c)
    
    # Historical Observed Weather & Thermal Persistence (Observed up to Day t)
    "obs_temp_lag1",            # Temperature observed on Day t
    "obs_temp_lag2",            # Temperature observed on Day t-1
    "obs_temp_lag3",            # Temperature observed on Day t-2
    "obs_temp_roll7_mean",      # 7-day rolling mean temperature (shift then roll)
    "obs_temp_trend3",          # 3-day temperature gradient (obs_temp_lag1 - obs_temp_lag3)
    "obs_wind_lag1",            # Wind speed observed on Day t
    "obs_wind_roll7_mean",      # 7-day rolling mean wind speed
    "obs_weather_sev_lag1",     # Weather severity on Day t
    "obs_weather_sev_roll7",    # 7-day rolling mean weather severity
    
    # Scheduled Population & Operational Roster for Day t+1
    "scheduled_population",     # Total personnel scheduled on station
    "scheduled_occupancy_pct",  # Scheduled capacity utilization (%)
    "scheduled_scientists",     # Scheduled research staff (lab load driver)
    "scheduled_engineers",      # Scheduled operations staff
    "scheduled_technicians",    # Scheduled technical/maintenance staff
    "scheduled_medical",        # Scheduled medical staff
    "pop_lag1",                 # Personnel count on Day t
    "pop_trend7",               # 7-day population change
    
    # Electrical Demand History (Strictly t <= 0)
    "load_lag1",                # Actual electrical demand on Day t (kW)
    "load_lag2",                # Demand on Day t-1 (kW)
    "load_lag3",                # Demand on Day t-2 (kW)
    "load_lag7",                # Demand on same day last week (kW)
    "load_lag14",               # Demand 2 weeks ago (kW)
    "load_roll3_mean",          # 3-day trailing rolling mean (shift then roll)
    "load_roll7_mean",          # 7-day trailing rolling mean
    "load_roll14_mean",         # 14-day trailing rolling mean
    "load_roll30_mean",         # 30-day trailing rolling mean
    "load_roll7_std",           # 7-day trailing load volatility
    "load_roll14_std",          # 14-day trailing load volatility
    "load_trend_3d",            # 3-day load gradient (load_lag1 - load_lag3)
    "load_trend_7d",            # Weekly load gradient (load_lag1 - load_lag7)
    
    # Storage Buffer State at 18:00 Cutoff Timestamp (Day t)
    "battery_soc_start_pct",    # Battery SoC at 18:00 cutoff (%)
    "soc_lag1",                 # Battery SoC on Day t-1
    "soc_delta_lag1",           # SoC net rate of change
    "fuel_stock_start_liters",  # Fuel inventory at cutoff (L)
    "days_since_refuel_start",  # Days elapsed since last refueling
    
    # Thermal Coupling History (t <= 0)
    "chp_heat_lag1",            # Generator waste heat recovered on Day t (kW)
    "chp_heat_roll7_mean",      # 7-day rolling mean CHP heat
    
    # Pre-Forecast Station Risk State (t <= 0)
    "power_risk_lag1",          # Power sub-system risk index on Day t
    "overall_risk_lag1",        # Overall station composite risk index on Day t
    "risk_roll7_mean",          # 7-day trailing rolling mean risk
]

# ── Chronological Split Windows ───────────────────────────────────────────────
SPLIT_CONFIG = {
    "train_end_year": 2019,     # Train: 2003–2019
    "val_start_year": 2020,     # Validation: 2020–2021
    "val_end_year": 2021,
    "test_year": 2022,          # Hold-Out Test: 2022
}

# ── Model Hyperparameter Configurations ───────────────────────────────────────
MODEL_CONFIGS = {
    "Ridge": {
        "alpha": 10.0,
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
