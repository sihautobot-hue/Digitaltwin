"""
train_model1_power.py
---------------------
Model 1 V2: Power Load Forecasting
Target: total_load_kw (continuous kW)

Architecture: LightGBM (upgraded from RandomForest/XGBoost)
Reason: LightGBM handles large corpora efficiently, supports native
        categorical features, and produces excellent results on
        multi-step regression with temporal lag features.

Antarctica Digital Twin | SIH Project — Version 2 Models
"""

import os
import sys
import json
import logging
import pickle
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Tuple

import lightgbm as lgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import TimeSeriesSplit

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Model1-Power")

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR  = os.path.join(SCRIPT_DIR, "..", "shared")
sys.path.insert(0, SHARED_DIR)

MODELS_DIR  = os.path.join(SCRIPT_DIR, "models")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
os.makedirs(MODELS_DIR,  exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

from corpus_builder import prepare_dataset

# ── Target ─────────────────────────────────────────────────────────────────────
TARGET = "total_load_kw"

# ══════════════════════════════════════════════════════════════════════════════
# FEATURE SELECTION — LEAKAGE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
# EXCLUDED (direct target leakage):
#   - daily_load_energy_kwh = total_load_kw × 24  (algebraic identity)
#   - generator_energy_kwh  = total_load_kw approx (energy balance)
#   - unserved_energy_kwh   = computed from load and supply
#   - solar_to_load_kwh     = energy balance downstream of load
#   - battery_to_load_kwh   = energy balance downstream
#   - overload_flag         = Boolean derived from load > capacity (uses load)
#   - load_shedding_kwh     = directly from load shortfall
#   - power_shortage_event  = derived from load
#
# INCLUDED WITH CAUTION:
#   - accommodation_load_kw etc. are sub-components. They are causal INPUTS to
#     total_load_kw in the physical model. In a real station these would be
#     meter readings available before the aggregated total is computed (OK).
#     However to avoid trivial solutions we EXCLUDE sub-loads that sum to target.
#     We keep weather, population, and the generator-side context only.

FEATURES = [
    # Station identity
    "station_enc",
    # Time
    "year", "month", "day_of_year", "quarter",
    "month_sin", "month_cos", "doy_sin", "doy_cos",
    "is_shipping_season", "is_polar_night", "is_polar_day",
    # Season & weather regime
    "season_enc", "weather_enc",
    "temperature_c", "wind_speed_kmh", "wind_gust_kmh",
    "humidity_percent", "pressure_hpa",
    "snow_depth_cm", "snowfall_cm", "visibility_m",
    "solar_radiation_wm2", "solar_daylight_hours", "solar_elevation_deg",
    "weather_severity",
    # Derived weather
    "wind_chill_c", "katabatic_index", "snow_transport_index",
    "temperature_c_lag1", "temperature_c_lag3", "temperature_c_lag7",
    "temperature_c_roll7", "temperature_c_roll30",
    "wind_speed_kmh_lag1", "wind_speed_kmh_roll7",
    "weather_severity_lag1", "weather_severity_roll7",
    # Population (drives load level)
    "total_population", "occupancy_percent",
    "scientists", "engineers", "technicians", "medical",
    "pop_lag1", "pop_delta", "pop_roll14_mean", "per_capita_load",
    # Solar (available generation context)
    "solar_generation_kw", "solar_roll7_mean",
    # Battery context
    "soc_lag1", "soc_lag7", "soc_roll7", "soc_delta",
    # Power history lags — fundamental for load forecasting
    "load_lag1", "load_lag2", "load_lag3", "load_lag7", "load_lag14",
    "load_roll3_mean", "load_roll7_mean", "load_roll14_mean", "load_roll30_mean",
    "load_roll3_std", "load_roll7_std",
    # Heating physical drivers
    "chp_lag1", "chp_roll7",
    # Risk signals
    "risk_lag1", "power_risk_lag1",
    # CHP waste heat available to supplement heating
    "chp_waste_heat_kw",
]


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def evaluate(name: str, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mape_pct = mape(y_true, y_pred)
    metrics = {"mae": round(mae, 4), "rmse": round(rmse, 4), "r2": round(r2, 6), "mape_pct": round(mape_pct, 4)}
    logger.info("[%s] MAE=%.3f  RMSE=%.3f  R²=%.4f  MAPE=%.2f%%", name, mae, rmse, r2, mape_pct)
    return metrics


# ══════════════════════════════════════════════════════════════════════════════
# MAIN TRAINING
# ══════════════════════════════════════════════════════════════════════════════

def train() -> None:
    # 1. Load data
    logger.info("=" * 60)
    logger.info("MODEL 1 — Power Load Forecasting (V2)")
    logger.info("=" * 60)
    logger.info("Loading corpus from V2 Digital Twin datasets ...")
    train_df, val_df, test_df = prepare_dataset(use_cache=True)

    def prep(df):
        available = [f for f in FEATURES if f in df.columns]
        X = df[available].copy()
        for col in X.select_dtypes(include="bool"):
            X[col] = X[col].astype(int)
        X = X.fillna(0)
        y = df[TARGET].values
        return X, y, available

    X_train, y_train, feature_cols = prep(train_df)
    X_val,   y_val,   _            = prep(val_df)
    X_test,  y_test,  _            = prep(test_df)

    logger.info("Train: %d rows | Val: %d | Test: %d", len(X_train), len(X_val), len(X_test))
    logger.info("Feature count: %d", len(feature_cols))

    # 2. Scaler (LightGBM is tree-based, scaling optional but kept for compatibility)
    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_val_s   = scaler.transform(X_val)
    X_test_s  = scaler.transform(X_test)

    # 3. LightGBM with early stopping on validation set
    lgb_params = {
        "objective":        "regression",
        "metric":           "mae",
        "n_estimators":     2000,
        "learning_rate":    0.04,
        "num_leaves":       127,
        "max_depth":        -1,
        "min_child_samples": 20,
        "subsample":        0.8,
        "colsample_bytree": 0.8,
        "reg_alpha":        0.1,
        "reg_lambda":       0.1,
        "random_state":     RANDOM_SEED,
        "n_jobs":           -1,
        "verbosity":        -1,
    }

    logger.info("Training LightGBM with early stopping ...")
    lgb_ds_train = lgb.Dataset(X_train_s, label=y_train, feature_name=feature_cols)
    lgb_ds_val   = lgb.Dataset(X_val_s,   label=y_val,   reference=lgb_ds_train)

    callbacks = [lgb.early_stopping(50, verbose=False), lgb.log_evaluation(200)]
    model = lgb.train(
        {k: v for k, v in lgb_params.items() if k != "n_estimators"},
        lgb_ds_train,
        num_boost_round=lgb_params["n_estimators"],
        valid_sets=[lgb_ds_val],
        callbacks=callbacks,
    )

    # 4. Evaluate
    metrics = {
        "train": evaluate("TRAIN", y_train, model.predict(X_train_s)),
        "val":   evaluate("VAL",   y_val,   model.predict(X_val_s)),
        "test":  evaluate("TEST",  y_test,  model.predict(X_test_s)),
        "best_iteration": model.best_iteration,
        "num_features": len(feature_cols),
    }

    # 5. Feature importance
    fi = pd.DataFrame({
        "feature":    feature_cols,
        "importance": model.feature_importance(importance_type="gain"),
    }).sort_values("importance", ascending=False)
    logger.info("Top 10 features:\n%s", fi.head(10).to_string(index=False))

    # 6. Save artifacts
    model_path   = os.path.join(MODELS_DIR,  "lgbm_power.pkl")
    scaler_path  = os.path.join(MODELS_DIR,  "scaler_power.pkl")
    features_path= os.path.join(MODELS_DIR,  "features_power.json")
    metrics_path = os.path.join(RESULTS_DIR, "metrics_power.json")
    fi_path      = os.path.join(RESULTS_DIR, "feature_importance_power.csv")

    with open(model_path,  "wb") as f: pickle.dump(model,  f)
    with open(scaler_path, "wb") as f: pickle.dump(scaler, f)
    with open(features_path, "w") as f: json.dump(feature_cols, f, indent=2)
    with open(metrics_path,  "w") as f: json.dump(metrics, f, indent=2)
    fi.to_csv(fi_path, index=False)

    logger.info("Model saved: %s", model_path)
    logger.info("Test R²=%.4f | RMSE=%.3f kW | MAPE=%.2f%%",
                metrics["test"]["r2"], metrics["test"]["rmse"], metrics["test"]["mape_pct"])
    logger.info("Model 1 (Power Load Forecast) training complete.")


if __name__ == "__main__":
    train()
