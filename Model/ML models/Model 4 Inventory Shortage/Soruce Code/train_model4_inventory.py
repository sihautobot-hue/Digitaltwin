"""
train_model4_inventory.py
--------------------------
Model 4 V2: Inventory Shortage Prediction
Target: inventory_shortage_items > 0 (binary classification)
Also tracks: critical_items, low_items (ordinal)

Architecture: LightGBM Classifier (upgraded from previous)
Key V2 Improvements:
  - FEFO batch expiry tracking → expired_items, expired_quantity
  - Reliability-driven spare parts consumption → critical_items spikes
  - Shipping season awareness → delayed_shipments
  - Multi-run corpus enables rare shortage event coverage (class balance)

Antarctica Digital Twin | SIH Project — Version 2 Models
"""

import os, sys, json, logging, pickle, warnings
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    classification_report, confusion_matrix,
)
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Model4-Inventory")

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

TARGET = "inventory_shortage_items"

# ══════════════════════════════════════════════════════════════════════════════
# LEAKAGE ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
# EXCLUDED (leakage):
#   - critical_items, low_items: sub-components of shortage score, same moment
#   - inventory_health_score: aggregate computed simultaneously
#   - inventory_orders_created_today: triggered by today's shortage detection
# INCLUDED WITH CAUTION:
#   - inv_health_lag1, inv_critical_lag1: yesterday's state → valid leading indicators

FEATURES = [
    "station_enc",
    "year", "month", "quarter", "day_of_year",
    "month_sin", "month_cos", "doy_sin", "doy_cos",
    "is_shipping_season",
    "season_enc", "weather_enc",
    "temperature_c", "wind_speed_kmh", "weather_severity",
    "weather_severity_lag1", "weather_severity_roll7",
    # Inventory state (lagged — yesterday)
    "inv_health_lag1",
    "inv_health_roll7",
    "inv_critical_lag1",
    "shortage_roll7",
    "expired_items",
    "expired_quantity",
    "delayed_shipments",
    "inventory_orders_pending",
    "inventory_eta_days",
    "inventory_batch_count",
    # Reliability-driven spares demand
    "power_risk_lag1", "risk_lag1", "risk_roll7",
    "fuel_risk_lag1", "water_risk_lag1",
    # Population (drives consumption)
    "total_population", "occupancy_percent",
    "scientists", "engineers", "technicians",
    "pop_lag1", "pop_roll14_mean",
    # Season context (higher research intensity in summer)
    "is_polar_night", "is_polar_day",
    # Supply chain logistics
    "fuel_shipments_pending", "fuel_eta_days",
    "days_since_refuel",
    # Power/fuel (failures drive maintenance parts consumption)
    "power_shortage_event",
    "generator_runtime_hours",
    "active_generators",
    "fuel_stock_lag1",
    "fuel_consumed_lag1", "fuel_roll7_mean",
    # Water (membrane filters)
    "water_plant_utilisation_percent",
    "water_quality_lag1",
]


def evaluate_clf(name, y_true, y_pred_proba, threshold=0.5):
    y_pred = (y_pred_proba >= threshold).astype(int)
    p   = precision_score(y_true, y_pred, zero_division=0)
    r   = recall_score(y_true, y_pred, zero_division=0)
    f1  = f1_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, y_pred_proba) if len(np.unique(y_true)) > 1 else 0.0
    logger.info("[%s] Precision=%.3f  Recall=%.3f  F1=%.3f  AUC=%.4f", name, p, r, f1, auc)
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4), "auc": round(auc, 4)}


def train():
    logger.info("=" * 60)
    logger.info("MODEL 4 — Inventory Shortage Prediction (V2)")
    logger.info("=" * 60)

    train_df, val_df, test_df = prepare_dataset(use_cache=True)

    def prep(df):
        avail = [f for f in FEATURES if f in df.columns]
        X = df[avail].copy()
        for c in X.select_dtypes("bool"): X[c] = X[c].astype(int)
        X = X.fillna(0)
        y = (df[TARGET] > 0).astype(int).values
        return X, y, avail

    X_train, y_train, feat_cols = prep(train_df)
    X_val,   y_val,   _         = prep(val_df)
    X_test,  y_test,  _         = prep(test_df)

    # Class balance
    pos_rate = y_train.mean()
    logger.info("Train: %d | Val: %d | Test: %d | Features: %d",
                len(X_train), len(X_val), len(X_test), len(feat_cols))
    logger.info("Positive rate (shortage): %.2f%%", pos_rate * 100)
    scale_pos = (1 - pos_rate) / max(pos_rate, 1e-6)
    logger.info("scale_pos_weight: %.2f", scale_pos)

    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_train)
    X_va_s = scaler.transform(X_val)
    X_te_s = scaler.transform(X_test)

    params = {
        "objective": "binary",
        "metric": "auc",
        "num_leaves": 63,
        "learning_rate": 0.04,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_samples": 20,
        "scale_pos_weight": scale_pos,
        "reg_alpha": 0.1,
        "reg_lambda": 0.2,
        "random_state": RANDOM_SEED,
        "n_jobs": -1,
        "verbosity": -1,
    }

    ds_train = lgb.Dataset(X_tr_s, label=y_train, feature_name=feat_cols)
    ds_val   = lgb.Dataset(X_va_s, label=y_val,   reference=ds_train)
    logger.info("Training LightGBM binary classifier ...")
    model = lgb.train(
        params, ds_train, num_boost_round=2000,
        valid_sets=[ds_val],
        callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(200)],
    )

    val_proba  = model.predict(X_va_s)
    test_proba = model.predict(X_te_s)

    metrics = {
        "train": evaluate_clf("TRAIN", y_train, model.predict(X_tr_s)),
        "val":   evaluate_clf("VAL",   y_val,   val_proba),
        "test":  evaluate_clf("TEST",  y_test,  test_proba),
        "best_iteration": model.best_iteration,
        "positive_rate_train_pct": round(pos_rate * 100, 3),
        "num_features": len(feat_cols),
    }

    # Confusion matrix on test
    cm = confusion_matrix(y_test, (test_proba >= 0.5).astype(int))
    logger.info("Confusion Matrix (Test):\n%s", cm)

    fi = pd.DataFrame({
        "feature": feat_cols,
        "importance": model.feature_importance("gain"),
    }).sort_values("importance", ascending=False)
    logger.info("Top 10:\n%s", fi.head(10).to_string(index=False))

    with open(os.path.join(MODELS_DIR, "lgbm_inventory.pkl"),     "wb") as f: pickle.dump(model, f)
    with open(os.path.join(MODELS_DIR, "scaler_inventory.pkl"),   "wb") as f: pickle.dump(scaler, f)
    with open(os.path.join(MODELS_DIR, "features_inventory.json"),"w") as f: json.dump(feat_cols, f, indent=2)
    with open(os.path.join(RESULTS_DIR,"metrics_inventory.json"), "w") as f: json.dump(metrics, f, indent=2)
    pd.DataFrame(cm).to_csv(os.path.join(RESULTS_DIR, "confusion_inventory.csv"), index=False)
    fi.to_csv(os.path.join(RESULTS_DIR, "fi_inventory.csv"), index=False)

    logger.info("Model 4 complete. Test F1=%.3f  AUC=%.4f",
                metrics["test"]["f1"], metrics["test"]["auc"])


if __name__ == "__main__":
    train()
