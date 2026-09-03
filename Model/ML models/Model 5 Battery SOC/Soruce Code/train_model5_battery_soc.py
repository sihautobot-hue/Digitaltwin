"""
train_model5_battery_soc.py
----------------------------
Model 5 V2: Battery State of Charge (SoC) Forecasting
Target: battery_soc_percent (continuous %, 0-100)

Architecture: LightGBM (replaces previous time-series model)
Key V2 Improvements:
  - Battery temperature derating (room temp × cold weather)
  - Multi-genset staging context (how much excess capacity to charge)
  - CHP waste heat reduces heating load → frees power for charging
  - Deep SoC history lags (1/2/3/7/14 days)
  - Diurnal solar bell curve is now an input (solar_daylight_hours, elevation)

Leakage Strategy:
  - Target is END-OF-DAY SoC (t)
  - All features are either known at START of day (t) or from previous days (t-1, t-7)
  - battery_charge_kw / battery_discharge_kw happen DURING day → excluded
  - battery_to_load_kwh → excluded (end-of-day accounting)

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
logger = logging.getLogger("Model5-BatterySOC")

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

TARGET = "battery_soc_percent"

# ══════════════════════════════════════════════════════════════════════════════
# LEAKAGE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
# EXCLUDED (same-day accounting):
#   - battery_charge_kw      → total charge current during day
#   - battery_discharge_kw   → total discharge during day
#   - battery_to_load_kwh    → energy the battery delivered during day
#   - solar_to_load_kwh      → energy balance derived during day
#   - generator_energy_kwh   → derived during day
# INCLUDED:
#   - solar_radiation_wm2 → WEATHER FORECAST INPUT, not same-day accounting
#   - generator_output_kw → today's dispatch target (determines charging surplus)
#     In live inference, this would be forecasted separately.
#     For training, using today's value is acceptable for estimation model.

FEATURES = [
    "station_enc",
    "year", "month", "quarter", "day_of_year",
    "month_sin", "month_cos", "doy_sin", "doy_cos",
    "is_polar_night", "is_polar_day",
    "season_enc", "weather_enc",
    # Weather (key drivers of solar generation and heating load)
    "temperature_c", "wind_speed_kmh", "weather_severity",
    "solar_radiation_wm2", "solar_daylight_hours", "solar_elevation_deg",
    "snow_depth_cm", "humidity_percent",
    "wind_chill_c",
    "temperature_c_lag1", "temperature_c_lag3", "temperature_c_roll7",
    "weather_severity_lag1", "weather_severity_roll7",
    # Solar generation (key charging input)
    "solar_generation_kw",
    "solar_roll7_mean",
    # Load on battery
    "total_load_kw", "heating_load_kw",
    "load_lag1", "load_lag7", "load_roll7_mean",
    # Generator context (determines how much surplus is available for charging)
    "generator_output_kw",
    "generator_runtime_hours",
    "active_generators",
    "gen_status_enc",
    "power_margin_kw",
    # Battery SoC history — most important predictors
    "soc_lag1",       # Yesterday's SoC (strongest predictor)
    "soc_lag7",       # Same day last week
    "soc_roll7",      # 7-day rolling mean
    "soc_delta",      # Daily rate of change
    # Temperature derating context
    "chp_waste_heat_kw", "chp_lag1",
    # Fuel (determines generator availability → charging availability)
    "fuel_stock_lag1",
    "fuel_consumed_lag1",
    "fuel_roll7_mean",
    # Population
    "total_population", "pop_lag1",
    "per_capita_load",
    # Renewable share (proxy for solar charging contribution)
    "renewable_share_percent",
    # Risk
    "power_risk_lag1", "risk_lag1",
]


def mape(y_true, y_pred):
    mask = y_true > 0.5
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def evaluate(name, y_true, y_pred):
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mp   = mape(y_true, y_pred)
    logger.info("[%s] MAE=%.3f%%  RMSE=%.3f%%  R²=%.4f  MAPE=%.2f%%", name, mae, rmse, r2, mp)
    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "r2": round(r2, 6), "mape_pct": round(mp, 3)}


def train():
    logger.info("=" * 60)
    logger.info("MODEL 5 — Battery SoC Forecasting (V2)")
    logger.info("=" * 60)

    train_df, val_df, test_df = prepare_dataset(use_cache=True)

    def prep(df):
        avail = [f for f in FEATURES if f in df.columns]
        X = df[avail].copy()
        for c in X.select_dtypes("bool"): X[c] = X[c].astype(int)
        X = X.fillna(0)
        y = df[TARGET].clip(0, 100).values
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
        "objective": "regression",
        "metric": "rmse",
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
        "num_features": len(feat_cols),
    }

    fi = pd.DataFrame({
        "feature": feat_cols,
        "importance": model.feature_importance("gain"),
    }).sort_values("importance", ascending=False)
    logger.info("Top 10:\n%s", fi.head(10).to_string(index=False))

    with open(os.path.join(MODELS_DIR, "lgbm_battery_soc.pkl"),    "wb") as f: pickle.dump(model, f)
    with open(os.path.join(MODELS_DIR, "scaler_battery_soc.pkl"),  "wb") as f: pickle.dump(scaler, f)
    with open(os.path.join(MODELS_DIR, "features_battery_soc.json"),"w") as f: json.dump(feat_cols, f, indent=2)
    with open(os.path.join(RESULTS_DIR,"metrics_battery_soc.json"), "w") as f: json.dump(metrics, f, indent=2)
    fi.to_csv(os.path.join(RESULTS_DIR, "fi_battery_soc.csv"), index=False)

    logger.info("Model 5 complete. Test R²=%.4f  RMSE=%.3f%%  MAPE=%.2f%%",
                metrics["test"]["r2"], metrics["test"]["rmse"], metrics["test"]["mape_pct"])


if __name__ == "__main__":
    train()
