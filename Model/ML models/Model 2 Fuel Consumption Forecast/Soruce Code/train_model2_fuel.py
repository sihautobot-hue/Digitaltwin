"""
train_model2_fuel.py
--------------------
Model 2 V2: Fuel Consumption Prediction
Target: fuel_consumed_today_liters (continuous Liters/day)

Architecture: LightGBM (upgraded from RandomForest/XGBoost)
Key V2 Improvements:
  - Non-linear SFC from multi-genset staging
  - CHP waste heat coupling
  - Generator startup fuel penalties
  - Active genset count as causal feature
  - Winter sea-ice lockout context

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
logger = logging.getLogger("Model2-Fuel")

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

TARGET = "fuel_consumed_today_liters"

# ══════════════════════════════════════════════════════════════════════════════
# LEAKAGE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
# EXCLUDED (direct leakage):
#   - fuel_days_remaining    = fuel_stock / fuel_consumed_today → direct algebraic leakage
#   - fuel_efficiency_l_per_kwh = fuel_consumed / generator_energy → post-hoc ratio
#   - generator_energy_kwh   = integrated runtime × output (partially leaks if runtime is today's)
#   - chp_waste_heat_kw      = directly derived from today's fuel burn (downstream)
# INCLUDED WITH CAUTION:
#   - generator_runtime_hours: hours the genset ran TODAY. This is an input to the SFC
#     calculation in the simulator. In practice this would be known at end of day
#     but NOT at time of forecasting (forecasting next day). For 1-day-ahead
#     forecasting we use lag1. For "current day estimate" we use today's.
#     This script trains a SAME-DAY estimation model (not forecasting), so runtime is OK.

FEATURES = [
    # Identity
    "station_enc",
    # Time
    "year", "month", "quarter", "day_of_year",
    "month_sin", "month_cos", "doy_sin", "doy_cos",
    "is_shipping_season", "is_polar_night",
    # Season & Weather
    "season_enc", "weather_enc",
    "temperature_c", "wind_speed_kmh", "weather_severity",
    "snow_depth_cm", "solar_radiation_wm2", "solar_daylight_hours",
    "wind_chill_c", "katabatic_index",
    "temperature_c_lag1", "temperature_c_roll7",
    "weather_severity_lag1", "weather_severity_roll7",
    # Generator operations — key causal variables
    "generator_output_kw",       # Load on genset
    "generator_runtime_hours",   # Hours genset ran today
    "active_generators",         # Number of units staged
    "gen_utilization_pct",       # Load factor (drives SFC non-linearity)
    "gen_energy_proxy",          # generator_output_kw × runtime_hours
    "gen_status_enc",
    # Power system context
    "total_load_kw", "heating_load_kw",
    "solar_generation_kw", "solar_roll7_mean",
    "renewable_share_percent",
    "load_roll7_mean",
    # Battery (drives how much generator must run vs solar)
    "battery_soc_percent", "soc_lag1", "soc_roll7",
    # Fuel state at start of day (NOT today's consumed — that's the target)
    "fuel_stock_lag1",            # Previous day stock
    "days_since_refuel",
    # Population (heating/cooking demand proxy)
    "total_population", "occupancy_percent",
    "per_capita_load",
    # Fuel consumption history (lag and rolling)
    "fuel_consumed_lag1", "fuel_consumed_lag2", "fuel_consumed_lag3",
    "fuel_consumed_lag7",
    "fuel_roll3_mean", "fuel_roll7_mean", "fuel_roll14_mean",
    # CHP context (previous day heat recovery drives next consumption estimate)
    "chp_lag1", "chp_roll7",
    # Risk context
    "power_risk_lag1",
]


def mape(y_true, y_pred):
    mask = y_true > 0.01
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def evaluate(name, y_true, y_pred):
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mp   = mape(y_true, y_pred)
    logger.info("[%s] MAE=%.2f L  RMSE=%.2f L  R²=%.4f  MAPE=%.2f%%", name, mae, rmse, r2, mp)
    return {"mae": round(mae, 3), "rmse": round(rmse, 3), "r2": round(r2, 6), "mape_pct": round(mp, 3)}


def train():
    logger.info("=" * 60)
    logger.info("MODEL 2 — Fuel Consumption Prediction (V2)")
    logger.info("=" * 60)

    train_df, val_df, test_df = prepare_dataset(use_cache=True)

    def prep(df):
        avail = [f for f in FEATURES if f in df.columns]
        X = df[avail].copy()
        for c in X.select_dtypes("bool"): X[c] = X[c].astype(int)
        X = X.fillna(0)
        y = df[TARGET].values
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
        "objective": "regression_l1",  # L1 = MAE — robust to extreme refuel days
        "metric": "mae",
        "num_leaves": 127,
        "learning_rate": 0.04,
        "subsample": 0.8,
        "colsample_bytree": 0.75,
        "min_child_samples": 30,
        "reg_alpha": 0.1,
        "reg_lambda": 0.2,
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
        "verbosity": -1,
    }

    logger.info("Training LightGBM (2000 rounds, early stopping 50) ...")
    ds_train = lgb.Dataset(X_tr_s, label=y_train, feature_name=feat_cols)
    ds_val   = lgb.Dataset(X_va_s, label=y_val,   reference=ds_train)
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

    with open(os.path.join(MODELS_DIR, "lgbm_fuel.pkl"),     "wb") as f: pickle.dump(model, f)
    with open(os.path.join(MODELS_DIR, "scaler_fuel.pkl"),   "wb") as f: pickle.dump(scaler, f)
    with open(os.path.join(MODELS_DIR, "features_fuel.json"),"w") as f: json.dump(feat_cols, f, indent=2)
    with open(os.path.join(RESULTS_DIR,"metrics_fuel.json"), "w") as f: json.dump(metrics, f, indent=2)
    fi.to_csv(os.path.join(RESULTS_DIR, "fi_fuel.csv"), index=False)

    logger.info("Model 2 complete. Test R²=%.4f  RMSE=%.2f L  MAPE=%.2f%%",
                metrics["test"]["r2"], metrics["test"]["rmse"], metrics["test"]["mape_pct"])


if __name__ == "__main__":
    train()
