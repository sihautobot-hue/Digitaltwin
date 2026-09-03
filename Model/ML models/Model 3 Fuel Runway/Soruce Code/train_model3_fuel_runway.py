"""
train_model3_fuel_runway.py
---------------------------
Model 3 V2: Fuel Runway Prediction
Target: fuel_days_remaining (continuous days)

Architecture: LightGBM
Key V2 Improvements:
  - Enforced shipping season context (no-arrival months 4-10)
  - Days-since-refuel rolling feature
  - Multi-run corpus improves rare event coverage
  - CHP waste heat reduces fuel rate (physical coupling)
  - Fuel trend as leading indicator

Note on Leakage:
  fuel_days_remaining = fuel_stock / fuel_consumed_today.
  We use fuel_stock_lag1 (yesterday's stock) and
  fuel_roll7_mean (rolling average consumption) rather than
  today's exact consumed value, which would be leakage for forecasting.

Antarctica Digital Twin | SIH Project — Version 2 Models
"""

import os, sys, json, logging, pickle, warnings
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Model3-FuelRunway")

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
SHARED_DIR  = os.path.join(SCRIPT_DIR, "..", "shared")
sys.path.insert(0, SHARED_DIR)

MODELS_DIR  = os.path.join(SCRIPT_DIR, "models")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
from corpus_builder import prepare_dataset

TARGET = "fuel_days_remaining"

# Clip target to 365 days (beyond that it's not operationally meaningful)
TARGET_CLIP = 365.0

# ══════════════════════════════════════════════════════════════════════════════
# LEAKAGE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
# EXCLUDED:
#   - fuel_consumed_today_liters = exact same-day consumption → trivial target derivation
#   - fuel_efficiency_l_per_kwh  = derived from today's consumption
# INCLUDED:
#   - fuel_stock_liters:  current stock level — NOT leakage for fuel_days_remaining
#     because runway = stock / projected_rate (stock is one input, rate is the other)
#   - fuel_roll7_mean: rolling consumption average ≠ today's consumption

FEATURES = [
    "station_enc",
    "year", "month", "quarter", "day_of_year",
    "month_sin", "month_cos", "doy_sin", "doy_cos",
    "is_shipping_season",
    "season_enc", "weather_enc",
    "temperature_c", "wind_speed_kmh", "weather_severity",
    "snow_depth_cm", "solar_radiation_wm2", "solar_daylight_hours",
    "wind_chill_c", "katabatic_index",
    "temperature_c_lag1", "temperature_c_roll7", "temperature_c_roll30",
    "weather_severity_lag1", "weather_severity_roll7",
    # Current fuel state (stock is an input to runway, not the target itself)
    "fuel_stock_liters",
    "fuel_stock_lag1",
    "fuel_stock_trend3",
    "days_since_refuel",
    # Fuel shipment context (V2 shipping season awareness)
    "fuel_shipments_pending",
    "fuel_eta_days",
    "refuel_event",
    # Rolling consumption rate (no today's exact value)
    "fuel_consumed_lag1",
    "fuel_consumed_lag7",
    "fuel_roll3_mean",
    "fuel_roll7_mean",
    "fuel_roll14_mean",
    # Generator context (drives consumption rate)
    "generator_output_kw",
    "generator_runtime_hours",
    "active_generators",
    "gen_energy_proxy",
    "gen_status_enc",
    # Power & load
    "total_load_kw", "load_lag1", "load_roll7_mean",
    "solar_generation_kw", "solar_roll7_mean",
    "renewable_share_percent",
    "soc_lag1",
    # CHP (reduces fuel consumption rate)
    "chp_lag1", "chp_roll7",
    # Population
    "total_population", "occupancy_percent",
    "pop_lag1", "pop_roll14_mean",
    # Risk signals
    "fuel_risk_lag1", "risk_lag1",
]


def mape(y_true, y_pred):
    mask = y_true > 0.5
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def evaluate(name, y_true, y_pred):
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mp   = mape(y_true, y_pred)
    logger.info("[%s] MAE=%.2f days  RMSE=%.2f days  R²=%.4f  MAPE=%.2f%%", name, mae, rmse, r2, mp)
    return {"mae": round(mae, 3), "rmse": round(rmse, 3), "r2": round(r2, 6), "mape_pct": round(mp, 3)}


def train():
    logger.info("=" * 60)
    logger.info("MODEL 3 — Fuel Runway Prediction (V2)")
    logger.info("=" * 60)

    train_df, val_df, test_df = prepare_dataset(use_cache=True)

    def prep(df):
        avail = [f for f in FEATURES if f in df.columns]
        X = df[avail].copy()
        for c in X.select_dtypes("bool"): X[c] = X[c].astype(int)
        X = X.fillna(0)
        y = np.clip(df[TARGET].values, 0, TARGET_CLIP)
        return X, y, avail

    X_train, y_train, feat_cols = prep(train_df)
    X_val,   y_val,   _         = prep(val_df)
    X_test,  y_test,  _         = prep(test_df)

    logger.info("Train: %d | Val: %d | Test: %d | Features: %d",
                len(X_train), len(X_val), len(X_test), len(feat_cols))

    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_train)
    X_va_s = scaler.transform(X_val)
    X_te_s = scaler.transform(X_test)

    params = {
        "objective": "regression_l1",
        "metric": "mae",
        "num_leaves": 127,
        "learning_rate": 0.04,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_samples": 20,
        "reg_alpha": 0.1,
        "reg_lambda": 0.1,
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
        "verbosity": -1,
    }

    ds_train = lgb.Dataset(X_tr_s, label=y_train, feature_name=feat_cols)
    ds_val   = lgb.Dataset(X_va_s, label=y_val,   reference=ds_train)
    logger.info("Training LightGBM ...")
    model = lgb.train(
        params, ds_train, num_boost_round=2000,
        valid_sets=[ds_val],
        callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(200)],
    )

    metrics = {
        "train": evaluate("TRAIN", y_train, model.predict(X_tr_s)),
        "val":   evaluate("VAL",   y_val,   model.predict(X_va_s)),
        "test":  evaluate("TEST",  y_test,  model.predict(X_te_s)),
        "best_iteration": model.best_iteration,
        "target_clip_days": TARGET_CLIP,
        "num_features": len(feat_cols),
    }

    fi = pd.DataFrame({
        "feature": feat_cols,
        "importance": model.feature_importance("gain"),
    }).sort_values("importance", ascending=False)
    logger.info("Top 10:\n%s", fi.head(10).to_string(index=False))

    with open(os.path.join(MODELS_DIR, "lgbm_fuel_runway.pkl"),  "wb") as f: pickle.dump(model, f)
    with open(os.path.join(MODELS_DIR, "scaler_runway.pkl"),     "wb") as f: pickle.dump(scaler, f)
    with open(os.path.join(MODELS_DIR, "features_runway.json"),  "w") as f: json.dump(feat_cols, f, indent=2)
    with open(os.path.join(RESULTS_DIR,"metrics_runway.json"),   "w") as f: json.dump(metrics, f, indent=2)
    fi.to_csv(os.path.join(RESULTS_DIR, "fi_runway.csv"), index=False)

    logger.info("Model 3 complete. Test R²=%.4f  RMSE=%.2f days  MAPE=%.2f%%",
                metrics["test"]["r2"], metrics["test"]["rmse"], metrics["test"]["mape_pct"])


if __name__ == "__main__":
    train()
