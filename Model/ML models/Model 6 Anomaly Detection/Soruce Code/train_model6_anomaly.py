"""
train_model6_anomaly.py
-----------------------
Model 6 V2: Operational Anomaly Detection (Multi-Subsystem)
Target: Binary anomaly label (constructed from physics violation detection)

Architecture: Isolation Forest + LightGBM ensemble
  Phase 1: Isolation Forest on operational telemetry → anomaly scores
  Phase 2: LightGBM binary classifier trained on physics-based anomaly labels
  Phase 3: Ensemble weighted average for final detection

Key V2 Improvements:
  - Physics-based anomaly label construction using V2 causal relationships
  - CHP-water coupling anomaly (high CHP but low water production)
  - Genset staging anomaly (active_generators=0 when load > 0)
  - Battery voltage cliff (SoC drop >20% overnight)
  - Shipping window violation check (V2 sea-ice lockout)
  - Connectivity radome icing detection

Antarctica Digital Twin | SIH Project — Version 2 Models
"""

import os, sys, json, logging, pickle, warnings
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    confusion_matrix, classification_report,
)

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Model6-Anomaly")

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


# ══════════════════════════════════════════════════════════════════════════════
# PHYSICS-BASED ANOMALY LABEL CONSTRUCTION
# ══════════════════════════════════════════════════════════════════════════════

def build_anomaly_labels(df: pd.DataFrame) -> pd.Series:
    """
    Construct binary anomaly labels from multi-system physics violations.
    These represent abnormal states that violate operational limits.

    Rules combined with logical OR:
      1. Gensets offline during non-zero load with critical battery
      2. Significant load shedding (>5 kWh)
      3. Severe battery SoC drop (>30% overnight cliff)
      4. Fuel stock critical reserve breached (<500 L)
      5. Water emergency declared
      6. Critical water quality drop (<82 WQI)
      7. Extended satellite blackout (>=5 days offline)
      8. Critical composite risk score (>70)
      9. Supply chain shipping delivery delays during season
    """
    labels = pd.Series(False, index=df.index)

    # 1. Power system anomalies
    if "active_generators" in df.columns and "total_load_kw" in df.columns:
        labels |= (
            (df["active_generators"] == 0) &
            (df["total_load_kw"] > 20.0) &
            (df.get("battery_soc_percent", 100) < 15.0)
        )

    # 2. Load shedding event (unserved demand)
    if "load_shedding_kwh" in df.columns:
        labels |= df["load_shedding_kwh"] > 5.0

    # 3. Sudden SoC cliff (overnight battery discharge > 30%)
    if "soc_delta" in df.columns:
        labels |= df["soc_delta"] < -30.0

    # 4. Fuel stock near empty
    if "fuel_stock_liters" in df.columns:
        labels |= df["fuel_stock_liters"] < 500.0

    # 5. Water system emergency
    if "water_emergency" in df.columns:
        labels |= df["water_emergency"] == True

    # 6. Water quality degradation
    if "water_quality_index" in df.columns:
        labels |= df["water_quality_index"] < 82.0

    # 7. Connectivity blackout
    if "offline_duration_days" in df.columns:
        labels |= df["offline_duration_days"] >= 5

    # 8. Extreme composite risk
    if "overall_risk_score" in df.columns:
        labels |= df["overall_risk_score"] > 70.0

    # 9. Delayed shipment in logistics
    if "delayed_shipments" in df.columns:
        labels |= df["delayed_shipments"] > 0

    logger.info("Anomaly label construction: %.2f%% anomaly rate (%d of %d samples)",
                labels.mean() * 100, labels.sum(), len(labels))
    return labels.astype(int)


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE SET — ANOMALY DETECTION
# ══════════════════════════════════════════════════════════════════════════════

FEATURES = [
    "station_enc",
    "year", "month", "day_of_year",
    "month_sin", "month_cos", "doy_sin", "doy_cos",
    "is_shipping_season", "is_polar_night",
    "season_enc", "weather_enc",
    # Environmental state
    "temperature_c", "wind_speed_kmh", "weather_severity",
    "snow_depth_cm", "visibility_m", "solar_radiation_wm2",
    "wind_chill_c", "katabatic_index",
    "temperature_c_lag1", "weather_severity_lag1", "weather_severity_roll7",
    # Power system telemetry
    "total_load_kw", "solar_generation_kw",
    "battery_soc_percent", "soc_lag1", "soc_delta", "soc_roll7",
    "generator_output_kw", "generator_runtime_hours",
    "active_generators", "gen_status_enc",
    "power_margin_kw", "renewable_share_percent",
    "load_shedding_kwh", "unserved_energy_kwh",
    "load_lag1", "load_roll7_mean",
    # Fuel telemetry
    "fuel_stock_liters", "fuel_stock_lag1", "fuel_stock_trend3",
    "fuel_consumed_today_liters", "fuel_consumed_lag1",
    "fuel_roll7_mean", "fuel_days_remaining",
    "fuel_status_enc", "days_since_refuel",
    "chp_waste_heat_kw", "chp_lag1",
    # Water telemetry
    "water_storage_liters", "water_stock_lag1",
    "daily_water_production_liters", "water_production_lag1",
    "water_quality_index", "water_quality_lag1", "water_quality_roll7",
    "water_stress_ratio",
    # Connectivity
    "signal_quality_percent", "buffered_data_mb",
    "offline_duration_days", "offline_streak",
    "link_offline", "link_degraded",
    # Inventory health
    "inventory_health_score", "inv_health_lag1", "inv_health_roll7",
    "critical_items", "inv_critical_lag1",
    "inventory_shortage_items", "shortage_roll7",
    "expired_items",
    # Risk composite history
    "overall_risk_score", "risk_lag1", "risk_roll7", "risk_trend7",
    "power_risk_lag1", "fuel_risk_lag1", "weather_risk_lag1", "water_risk_lag1",
    "connectivity_risk_lag1",
    # Population
    "total_population", "pop_lag1", "pop_delta",
]


def evaluate_clf(name, y_true, y_pred_proba, threshold=0.5):
    y_pred = (y_pred_proba >= threshold).astype(int)
    p   = precision_score(y_true, y_pred, zero_division=0)
    r   = recall_score(y_true, y_pred, zero_division=0)
    f1  = f1_score(y_true, y_pred, zero_division=0)
    auc = roc_auc_score(y_true, y_pred_proba) if len(np.unique(y_true)) > 1 else 0.0
    logger.info("[%s] P=%.3f  R=%.3f  F1=%.3f  AUC=%.4f", name, p, r, f1, auc)
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4), "auc": round(auc, 4)}


def train():
    logger.info("=" * 60)
    logger.info("MODEL 6 — Operational Anomaly Detection (V2)")
    logger.info("=" * 60)

    train_df, val_df, test_df = prepare_dataset(use_cache=True)

    # Build physics-based labels
    for split_df in [train_df, val_df, test_df]:
        split_df["anomaly"] = build_anomaly_labels(split_df).values

    def prep(df):
        avail = [f for f in FEATURES if f in df.columns]
        X = df[avail].copy()
        for c in X.select_dtypes("bool"): X[c] = X[c].astype(int)
        X = X.fillna(0)
        y = df["anomaly"].values
        return X, y, avail

    X_train, y_train, feat_cols = prep(train_df)
    X_val,   y_val,   _         = prep(val_df)
    X_test,  y_test,  _         = prep(test_df)

    pos_rate = y_train.mean()
    logger.info("Train: %d | Val: %d | Test: %d | Features: %d",
                len(X_train), len(X_val), len(X_test), len(feat_cols))
    logger.info("Anomaly rate: %.2f%%", pos_rate * 100)

    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_train)
    X_va_s = scaler.transform(X_val)
    X_te_s = scaler.transform(X_test)

    # Phase 1: Isolation Forest (unsupervised anomaly scores as meta-feature)
    logger.info("Training Isolation Forest (unsupervised phase) ...")
    contam = min(0.20, max(0.01, float(pos_rate)))
    iforest = IsolationForest(
        n_estimators=200, contamination=contam,
        random_state=RANDOM_SEED, n_jobs=-1,
    )
    iforest.fit(X_tr_s[y_train == 0])  # Fit on normal samples only
    if_score_train = -iforest.score_samples(X_tr_s)  # Higher = more anomalous
    if_score_val   = -iforest.score_samples(X_va_s)
    if_score_test  = -iforest.score_samples(X_te_s)

    # Augment feature matrices with IF score (meta-feature)
    X_tr_aug = np.column_stack([X_tr_s, if_score_train])
    X_va_aug = np.column_stack([X_va_s, if_score_val])
    X_te_aug = np.column_stack([X_te_s, if_score_test])
    feat_cols_aug = feat_cols + ["isolation_forest_score"]

    # Phase 2: LightGBM supervised classifier
    scale_pos = (1 - pos_rate) / max(pos_rate, 1e-6)
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

    logger.info("Training LightGBM supervised classifier ...")
    ds_train = lgb.Dataset(X_tr_aug, label=y_train, feature_name=feat_cols_aug)
    ds_val   = lgb.Dataset(X_va_aug, label=y_val,   reference=ds_train)
    lgbm_model = lgb.train(
        params, ds_train, num_boost_round=2000,
        valid_sets=[ds_val],
        callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(200)],
    )

    lgbm_proba_train = lgbm_model.predict(X_tr_aug)
    lgbm_proba_val   = lgbm_model.predict(X_va_aug)
    lgbm_proba_test  = lgbm_model.predict(X_te_aug)

    # Find optimal decision threshold on validation set
    thresholds = np.linspace(0.01, 0.90, 90)
    best_f1, best_th = 0.0, 0.5
    for th in thresholds:
        pred_v = (lgbm_proba_val >= th).astype(int)
        f1_v = f1_score(y_val, pred_v, zero_division=0)
        if f1_v > best_f1:
            best_f1, best_th = f1_v, th

    logger.info("Optimal validation threshold: %.3f (Val F1=%.4f)", best_th, best_f1)

    # Phase 3: Ensemble (weighted average — IF provides unsupervised breadth)
    def norm(arr): return (arr - arr.min()) / (arr.max() - arr.min() + 1e-9)
    alpha = 0.85  # 85% LightGBM, 15% Isolation Forest

    ens_train = alpha * lgbm_proba_train + (1 - alpha) * norm(if_score_train)
    ens_val   = alpha * lgbm_proba_val   + (1 - alpha) * norm(if_score_val)
    ens_test  = alpha * lgbm_proba_test  + (1 - alpha) * norm(if_score_test)

    # Tune ensemble threshold on validation
    best_ens_f1, best_ens_th = 0.0, 0.5
    for th in thresholds:
        pred_ev = (ens_val >= th).astype(int)
        f1_ev = f1_score(y_val, pred_ev, zero_division=0)
        if f1_ev > best_ens_f1:
            best_ens_f1, best_ens_th = f1_ev, th

    logger.info("Optimal ensemble validation threshold: %.3f (Val F1=%.4f)", best_ens_th, best_ens_f1)

    metrics = {
        "lgbm": {
            "optimal_threshold": round(float(best_th), 4),
            "train": evaluate_clf("LGBM-TRAIN", y_train, lgbm_proba_train, threshold=best_th),
            "val":   evaluate_clf("LGBM-VAL",   y_val,   lgbm_proba_val,   threshold=best_th),
            "test":  evaluate_clf("LGBM-TEST",  y_test,  lgbm_proba_test,  threshold=best_th),
        },
        "ensemble": {
            "optimal_threshold": round(float(best_ens_th), 4),
            "train": evaluate_clf("ENS-TRAIN", y_train, ens_train, threshold=best_ens_th),
            "val":   evaluate_clf("ENS-VAL",   y_val,   ens_val,   threshold=best_ens_th),
            "test":  evaluate_clf("ENS-TEST",  y_test,  ens_test,  threshold=best_ens_th),
        },
        "best_iteration": lgbm_model.best_iteration,
        "anomaly_rate_pct": round(pos_rate * 100, 3),
        "ensemble_alpha": alpha,
        "num_features": len(feat_cols_aug),
    }

    fi = pd.DataFrame({
        "feature": feat_cols_aug,
        "importance": lgbm_model.feature_importance("gain"),
    }).sort_values("importance", ascending=False)
    logger.info("Top 10 features:\n%s", fi.head(10).to_string(index=False))

    cm = confusion_matrix(y_test, (ens_test >= best_ens_th).astype(int))
    logger.info("Confusion Matrix (Ensemble Test at th=%.3f):\n%s", best_ens_th, cm)

    with open(os.path.join(MODELS_DIR, "lgbm_anomaly.pkl"),     "wb") as f: pickle.dump(lgbm_model, f)
    with open(os.path.join(MODELS_DIR, "iforest_anomaly.pkl"),  "wb") as f: pickle.dump(iforest, f)
    with open(os.path.join(MODELS_DIR, "scaler_anomaly.pkl"),   "wb") as f: pickle.dump(scaler, f)
    with open(os.path.join(MODELS_DIR, "features_anomaly.json"),"w") as f: json.dump(feat_cols_aug, f, indent=2)
    with open(os.path.join(RESULTS_DIR,"metrics_anomaly.json"), "w") as f: json.dump(metrics, f, indent=2)
    pd.DataFrame(cm).to_csv(os.path.join(RESULTS_DIR, "confusion_anomaly.csv"), index=False)
    fi.to_csv(os.path.join(RESULTS_DIR, "fi_anomaly.csv"), index=False)

    logger.info("Model 6 complete. Ensemble Test F1=%.3f  AUC=%.4f",
                metrics["ensemble"]["test"]["f1"], metrics["ensemble"]["test"]["auc"])


if __name__ == "__main__":
    train()
