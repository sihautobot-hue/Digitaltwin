# config.py
# Model 4 (Version 3): Day-Ahead Inventory Shortage Forecasting
# Antarctica Digital Twin | Scientific ML Pipeline

import os

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DATA_DIR    = os.path.normpath(os.path.join(BASE_DIR, "..", "..", "data"))
MODELS_DIR  = os.path.join(BASE_DIR, "models_v3")
RESULTS_DIR = os.path.join(BASE_DIR, "results_v3")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(FIGURES_DIR, exist_ok=True)

TARGET_RAW   = "inventory_shortage_items"
TARGET_NAME  = "inventory_shortage_tomorrow"   # Binary flag: inventory_shortage_items[t+1] > 0
RANDOM_SEED  = 42

# Chronological Split Configuration
SPLIT_CONFIG = {
    "train_end_year": 2019,
    "val_start_year": 2020,
    "val_end_year":   2021,
    "test_start_year": 2022,
    "test_end_year":  2022,
}

# Forecast-Safe Features (Strictly Known at 18:00 on Day t)
FEATURE_COLUMNS = [
    # Station & Time
    "station_enc",
    "year", "month", "quarter", "day_of_year",
    "month_sin", "month_cos", "doy_sin", "doy_cos",
    "season_enc", "is_polar_night", "is_polar_day",
    
    # Inventory Health & Stock State at 18:00 Cutoff (Day t)
    "inv_health_lag0",
    "inv_health_lag1",
    "inv_health_lag7",
    "inv_health_roll7_mean",
    "inv_health_roll14_mean",
    "inv_health_trend_7d",
    "critical_items_lag0",
    "critical_items_lag1",
    "critical_items_roll7_mean",
    "low_items_lag0",
    "low_items_lag1",
    "low_items_roll7_mean",
    "inventory_risk_lag0",
    "inv_risk_roll7_mean",
    
    # Historical Shortage Telemetry (Shift-Then-Roll from Day t backwards)
    "shortage_items_lag0",
    "shortage_items_lag1",
    "shortage_items_lag2",
    "shortage_items_lag7",
    "shortage_items_lag14",
    "shortage_roll3_mean",
    "shortage_roll7_mean",
    "shortage_roll14_mean",
    "shortage_roll30_mean",
    "shortage_trend_7d",
    "shortage_binary_lag0",
    "shortage_days_in_past_7",
    "shortage_days_in_past_30",
    
    # Supply Chain & Inbound Shipping Schedule (Known State at 18:00 Day t)
    "inv_orders_pending_lag0",
    "inv_eta_days_lag0",
    "delayed_shipments_lag0",
    "inv_batch_count_lag0",
    "expired_items_lag0",
    "expired_quantity_lag0",
    "days_since_shipment_received",
    "is_shipping_season",
    "days_into_shipping_season",
    "days_until_shipping_season",
    "shipping_window_open",
    
    # Scheduled Population Roster for Day t+1
    "scheduled_population",
    "scheduled_occupancy_percent",
    "scheduled_scientists",
    "scheduled_engineers",
    "scheduled_technicians",
    "scheduled_logistics",
    "scheduled_medical",
    "pop_lag1",
    "pop_roll14_mean",
    "pop_trend_7d",
    
    # Day-Ahead NWP Weather Forecast for Day t+1
    "fc_temperature_c",
    "fc_wind_speed_kmh",
    "fc_wind_gust_kmh",
    "fc_weather_severity",
    "fc_solar_radiation_wm2",
    "fc_solar_daylight_hours",
    "fc_heating_degree_days",
    "fc_blizzard_risk",
    "fc_is_extreme_weather",
    
    # Historical Equipment & Maintenance Spares Demand Proxies (Observed on Day t)
    "gen_runtime_lag0",
    "gen_output_lag0",
    "active_gen_lag0",
    "power_risk_lag0",
    "fuel_risk_lag0",
    "water_risk_lag0",
    "water_plant_util_lag0",
    "risk_score_lag0",
    "station_health_lag0",
]

# 4 Algorithm Model Configurations
MODEL_CONFIGS = {
    "XGBoost": {
        "n_estimators": 500,
        "max_depth": 5,
        "learning_rate": 0.03,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_weight": 3,
        "gamma": 0.1,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": RANDOM_SEED,
        "eval_metric": "logloss",
        "n_jobs": -1,
    },
    "LightGBM": {
        "n_estimators": 500,
        "num_leaves": 31,
        "max_depth": 6,
        "learning_rate": 0.03,
        "subsample": 0.85,
        "colsample_bytree": 0.85,
        "min_child_samples": 20,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
        "verbosity": -1,
    },
    "RandomForest": {
        "n_estimators": 250,
        "max_depth": 10,
        "min_samples_split": 5,
        "min_samples_leaf": 2,
        "max_features": "sqrt",
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
    },
    "CatBoost": {
        "iterations": 500,
        "depth": 6,
        "learning_rate": 0.03,
        "l2_leaf_reg": 3.0,
        "random_seed": RANDOM_SEED,
        "verbose": 0,
        "thread_count": -1,
    },
}
