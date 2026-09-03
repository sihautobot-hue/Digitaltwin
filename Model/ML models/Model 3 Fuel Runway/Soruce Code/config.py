"""
config.py
---------
Model 3 (Version 3): Day-Ahead Fuel Runway Forecasting
Antarctica Digital Twin | SIH Project

MODEL 3 FORECAST CONTRACT
==========================
Prediction Timestamp:    18:00 Station Local Time on Day t
Forecast Horizon:        Day t+1 (fuel runway at the START of Day t+1)
Target Variable:         fuel_days_remaining at Day t+1 (continuous days)
Target Interpretation:   How many days the station can continue operating
                         from the start of Day t+1, given expected fuel
                         consumption rate.
Target Clip:             365.0 days (beyond that is not operationally meaningful)

Information ALLOWED (known at or before 18:00 on Day t):
  * Observed fuel stock in tanks at 18:00 cutoff (fuel_stock_start_liters)
  * Historical fuel consumption lags (fuel_lag1, lag2, lag3, lag7, lag14)
  * Shifted trailing rolling fuel statistics (roll3, 7, 14, 30, expanding, std, trend)
  * Days elapsed since previous refueling event (days_since_refuel_start)
  * Number of pending inbound tanker shipments (fuel_shipments_pending)
  * Estimated days until next tanker arrival (fuel_eta_days)
  * Scheduled crew roster for Day t+1 (scheduled_population, scientists, etc.)
  * Day-ahead Numerical Weather Prediction (NWP) forecasts for Day t+1
  * Astronomical calendar & solar geometry for Day t+1
  * Battery SoC at 18:00 cutoff (Day t)
  * Past generator output and CHP heat recovery (observed on Day t)
  * Historical weather observations (observed lags up to Day t)
  * Station identity (Maitri vs Bharati)

Information FORBIDDEN (leakage):
  * fuel_days_remaining on Day t itself — that IS the target lead-1
  * fuel_consumed_today_liters on Day t+1 — same-day realized burn
  * fuel_efficiency_l_per_kwh — post-hoc ratio derived from target
  * generator_energy_kwh on Day t+1 — downstream dispatch
  * daily_load_energy_kwh on Day t+1 — electrical demand realized on Day t+1
  * gen_energy_proxy (output_kw * runtime_h on Day t+1)
  * generator_output_kw on Day t+1 — same-day dispatch
  * generator_runtime_hours on Day t+1 — same-day operational state
  * active_generators on Day t+1 — same-day staging decision
  * total_load_kw on Day t+1 — simultaneous electrical demand
  * solar_generation_kw on Day t+1 — simultaneous generation
  * battery_to_load_kwh, solar_to_load_kwh — intra-day energy balance
  * unserved_energy_kwh, load_shedding_kwh — post-event curtailment
  * overload_flag, power_shortage_event — post-event flags
  * fuel_stock_liters on Day t+1 — end-of-day stock AFTER consuming t+1
  * refuel_event on Day t+1 — refueling happened during Day t+1
  * same-day weather observations (temperature_c, wind_speed_kmh, etc. on Day t+1)
  * per_capita_load, renewable_share_percent — Day t+1 derived ratios
"""

import os

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "data"))
MODELS_DIR  = os.path.join(BASE_DIR, "models_v3")
RESULTS_DIR = os.path.join(BASE_DIR, "results_v3")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

TARGET_RAW   = "fuel_days_remaining"
TARGET_NAME  = "fuel_runway_lead1"   # fuel_days_remaining at Day t+1
TARGET_CLIP  = 365.0                 # operationally, >1 year runway is same as 1 year
RANDOM_SEED  = 42

# ── Forecast-Safe Features (All Available at 18:00 Cutoff on Day t) ───────────
FEATURE_COLUMNS = [
    # Station topology
    "station_enc",                  # 0 = Maitri, 1 = Bharati

    # Calendar & Astronomical Geometry (deterministic for Day t+1)
    "month_sin", "month_cos",
    "doy_sin", "doy_cos",
    "dow_sin", "dow_cos",
    "quarter",
    "is_shipping_season",           # Maritime access window (Nov–Mar)
    "is_polar_night",               # Continuous darkness
    "is_polar_day",                 # Continuous sunlight
    "fc_solar_elevation_deg",       # Noon solar elevation angle
    "fc_solar_daylight_hours",      # Astronomical daylight duration

    # Day-ahead NWP weather forecast for Day t+1
    "fc_temperature_c",
    "fc_wind_speed_kmh",
    "fc_wind_gust_kmh",
    "fc_solar_radiation_wm2",
    "fc_snowfall_cm",
    "fc_snow_depth_cm",
    "fc_weather_severity",
    "fc_weather_type_enc",
    "fc_wind_chill_c",
    "fc_katabatic_index",
    "fc_heating_degree_days",

    # Historical weather observations up to Day t (lags)
    "obs_temp_lag1",
    "obs_temp_lag2",
    "obs_temp_lag3",
    "obs_temp_roll7_mean",
    "obs_temp_trend3",
    "obs_wind_lag1",
    "obs_wind_roll7_mean",
    "obs_weather_sev_lag1",
    "obs_weather_sev_roll7",

    # Scheduled station population roster for Day t+1
    "scheduled_population",
    "scheduled_occupancy_pct",
    "scheduled_scientists",
    "scheduled_engineers",
    "scheduled_technicians",
    "scheduled_medical",
    "pop_lag1",
    "pop_trend7",

    # Current fuel inventory state at 18:00 cutoff (Day t)
    "fuel_stock_start_liters",
    "fuel_stock_lag1",
    "fuel_stock_drawdown_3d",
    "days_since_refuel_start",
    "fuel_shipments_pending",
    "fuel_eta_days",

    # Historical fuel consumption dynamics (strictly past, shift-then-roll)
    "fuel_lag1",
    "fuel_lag2",
    "fuel_lag3",
    "fuel_lag7",
    "fuel_lag14",
    "fuel_roll3_mean",
    "fuel_roll7_mean",
    "fuel_roll14_mean",
    "fuel_roll30_mean",
    "fuel_expanding_mean",
    "fuel_roll7_std",
    "fuel_roll14_std",
    "fuel_trend_3d",
    "fuel_trend_7d",

    # Historical fuel runway dynamics (strictly past runway, shift-then-roll)
    "runway_lag1",                  # Runway observed on Day t
    "runway_lag2",                  # Runway observed on Day t-1
    "runway_lag7",                  # Runway same day last week
    "runway_roll3_mean",            # 3-day trailing mean runway
    "runway_roll7_mean",            # 7-day trailing mean runway
    "runway_roll14_mean",           # 14-day trailing mean runway
    "runway_trend_3d",              # 3-day runway trend
    "runway_trend_7d",              # Weekly runway trajectory

    # Past generator & thermal telemetry (observed on Day t, t <= 0)
    "gen_output_lag1",
    "gen_runtime_lag1",
    "gen_utilization_lag1",
    "chp_heat_lag1",
    "chp_heat_roll7_mean",

    # Storage buffer state at 18:00 cutoff (Day t)
    "battery_soc_start_pct",
    "soc_lag1",
    "soc_delta_lag1",

    # Risk indices at 18:00 cutoff (Day t)
    "fuel_risk_lag1",
    "power_risk_lag1",
    "overall_risk_lag1",
    "risk_roll7_mean",
]

# ── Chronological Split Configuration ────────────────────────────────────────
SPLIT_CONFIG = {
    "train_end_year": 2019,
    "val_start_year": 2020,
    "val_end_year":   2021,
    "test_year":      2022,
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
