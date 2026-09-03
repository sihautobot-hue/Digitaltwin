# config.py  ? Model 6 V3: Day-Ahead Operational Risk Forecasting
# Forecast Contract:
#   Prediction timestamp : 18:00 Station Local Time on Day t
#   Horizon              : Day t+1
#   Target               : future_operational_anomaly
#                          = OperationalAnomaly.shift(-1) per station
#   Definition           : OperationalAnomaly = 1 if ANY of
#                          power_shortage_event | fuel_shortage_event |
#                          water_emergency | communication_outage_event | overload_flag

import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR  = os.path.join(BASE_DIR, "models_v3")
RESULTS_DIR = os.path.join(BASE_DIR, "results_v3")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
DATA_DIR    = r"C:\Users\krish\source\SIH\data"

for d in [MODELS_DIR, RESULTS_DIR, FIGURES_DIR]:
    os.makedirs(d, exist_ok=True)

# ---------------------------------------------------------------------------
# Data files (5 simulation runs)
# ---------------------------------------------------------------------------
DATA_FILES = [
    os.path.join(DATA_DIR, f"station_summary_{i}.csv") for i in range(1, 6)
]

# ---------------------------------------------------------------------------
# Target definition
# ---------------------------------------------------------------------------
TARGET_NAME = "future_operational_anomaly"

# Source event columns that compose OperationalAnomaly at time t
ANOMALY_SOURCE_COLS = [
    "power_shortage_event",
    "fuel_shortage_event",
    "water_emergency",
    "communication_outage_event",
    "overload_flag",
]

# ---------------------------------------------------------------------------
# Chronological split years
# ---------------------------------------------------------------------------
TRAIN_YEARS = list(range(2003, 2020))   # 2003?2019
VAL_YEARS   = [2020, 2021]
TEST_YEARS  = [2022]

# ---------------------------------------------------------------------------
# Random seed
# ---------------------------------------------------------------------------
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Safe Feature Schema (forecast-safe as of 18:00 Day t ? NO LEAKAGE)
# These are the feature column names AFTER feature engineering.
# ---------------------------------------------------------------------------
FEATURE_COLS = [
    # --- Historical anomaly behaviour ---
    "anomaly_lag1",
    "anomaly_lag2",
    "anomaly_lag3",
    "anomaly_lag7",
    "anomaly_roll7_mean",
    "anomaly_roll14_mean",
    "anomaly_roll30_mean",
    "anomaly_roll7_std",
    "anomaly_ema7",
    "anomaly_frequency30",
    "anomaly_streak",             # consecutive anomaly days leading to t
    "anomaly_free_streak",        # consecutive clean days leading to t

    # --- Fuel system (state at start of day t) ---
    "fuel_stock_lag1",
    "fuel_stock_roll7_mean",
    "fuel_stock_roll14_mean",
    "fuel_stock_trend7",
    "fuel_days_remaining_lag1",
    "fuel_days_remaining_roll7",
    "days_since_refuel",
    "fuel_shipments_pending_lag1",
    "fuel_eta_days_lag1",
    "fuel_critical_flag",         # 1 if fuel_days_remaining < 10

    # --- Battery history ---
    "battery_soc_lag1",
    "battery_soc_lag3",
    "battery_soc_roll7_mean",
    "battery_soc_roll7_std",
    "battery_soc_trend7",
    "battery_soc_low_flag",       # 1 if battery_soc < 20%
    "battery_discharge_lag1",

    # --- Power system history ---
    "power_margin_lag1",
    "power_margin_roll7_mean",
    "power_shortage_lag1",
    "power_shortage_roll7_mean",
    "overload_lag1",
    "overload_roll7_mean",
    "generator_output_lag1",
    "generator_output_roll7_mean",
    "renewable_share_lag1",
    "renewable_share_roll7_mean",

    # --- Inventory system history ---
    "inventory_health_lag1",
    "inventory_health_roll7_mean",
    "inventory_health_roll14_mean",
    "inventory_health_trend7",
    "critical_items_lag1",
    "critical_items_roll7_mean",
    "inventory_orders_pending_lag1",
    "inventory_eta_days_lag1",
    "days_since_last_delivery",
    "inventory_shortage_lag1",

    # --- Water system history ---
    "water_storage_lag1",
    "water_storage_roll7_mean",
    "water_days_remaining_lag1",
    "water_emergency_lag1",
    "water_shortage_lag1",

    # --- Communication history ---
    "communication_outage_lag1",
    "communication_outage_roll7_mean",
    "offline_duration_lag1",
    "signal_quality_lag1",
    "signal_quality_roll7_mean",
    "bandwidth_lag1",
    "packet_loss_lag1",

    # --- Weather observations (observed through Day t) ---
    "temperature_lag1",
    "temperature_roll7_mean",
    "temperature_roll7_min",
    "extreme_cold_flag",          # 1 if temperature < -30C
    "wind_speed_lag1",
    "wind_speed_roll7_mean",
    "wind_gust_lag1",
    "snowfall_lag1",
    "snowfall_roll7_mean",
    "visibility_lag1",
    "weather_severity_lag1",
    "weather_severity_roll7_mean",
    "storm_flag",                 # 1 if weather_severity > 0.7

    # --- Weather forecasts for Day t+1 ---
    "fc_temperature",
    "fc_wind_speed",
    "fc_wind_gust",
    "fc_snowfall",
    "fc_pressure",
    "fc_visibility",
    "fc_weather_severity",
    "fc_solar_daylight_hours",

    # --- Crew schedule ---
    "scheduled_population",
    "scheduled_scientists",
    "scheduled_engineers",
    "high_population_flag",       # 1 if scheduled_population >= 35

    # --- Calendar ---
    "month",
    "day_of_year",
    "doy_sin",
    "doy_cos",
    "month_sin",
    "month_cos",
    "season_enc",
    "polar_night_flag",
    "polar_day_flag",
    "year",
    "station_enc",
]

NUM_FEATURES = len(FEATURE_COLS)

# ---------------------------------------------------------------------------
# Model hyperparameters
# ---------------------------------------------------------------------------
MODEL_PARAMS = {
    "XGBoost": {
        "n_estimators": 500,
        "max_depth": 5,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 5,
        "scale_pos_weight": 9,      # ~1/prevalence for imbalance
        "eval_metric": "aucpr",
        "use_label_encoder": False,
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
        "verbosity": 0,
    },
    "LightGBM": {
        "n_estimators": 500,
        "max_depth": 5,
        "learning_rate": 0.05,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_samples": 20,
        "is_unbalance": True,
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
        "verbose": -1,
    },
    "CatBoost": {
        "iterations": 500,
        "depth": 5,
        "learning_rate": 0.05,
        "auto_class_weights": "Balanced",
        "random_seed": RANDOM_SEED,
        "verbose": 0,
    },
    "RandomForest": {
        "n_estimators": 300,
        "max_depth": 10,
        "min_samples_leaf": 10,
        "class_weight": "balanced",
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
    },
}
