"""
evaluate.py
-----------
Comprehensive scientific evaluation, stress testing, and explainability for Model 2 (Version 3).
Calculates:
  1. Performance Metrics: MAE, RMSE, MAPE, R², Residual Mean, Residual Std, Bias, Prediction Interval Coverage
  2. Scientific Stress Tests:
      - Summer vs Winter
      - High Population vs Low Population
      - Storm Days (Wind >= 65 km/h) vs Normal Days
      - Fuel Shortage (Stock < 2,000 L)
      - Generator Outages / Stress
      - Extreme Cold Snap (T < -35°C)
  3. Interpretability:
      - TreeSHAP values
      - Permutation Feature Importance
      - Native Feature Importance
"""

import os
import sys
import json
import pickle
import logging
import warnings
from typing import Dict, Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.inspection import permutation_importance
from sklearn.base import BaseEstimator, RegressorMixin
import shap

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Evaluate-Model2-V3")

from config import (
    MODELS_DIR,
    RESULTS_DIR,
    FEATURE_COLUMNS,
    TARGET_NAME,
    RANDOM_SEED,
)
from feature_engineering import get_chronological_splits


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true > 0.01
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def calc_subset(y_t: np.ndarray, y_p: np.ndarray) -> Dict[str, Any]:
    if len(y_t) == 0:
        return {"n": 0, "rmse": 0.0, "mae": 0.0, "mape_pct": 0.0, "r2": 0.0, "bias": 0.0}
    r2_val = float(r2_score(y_t, y_p)) if len(y_t) > 1 and np.var(y_t) > 1e-6 else 1.0
    return {
        "n": int(len(y_t)),
        "rmse": round(float(np.sqrt(mean_squared_error(y_t, y_p))), 4),
        "mae": round(float(mean_absolute_error(y_t, y_p)), 4),
        "mape_pct": round(float(mape(y_t, y_p)), 4),
        "r2": round(r2_val, 6),
        "bias": round(float(np.mean(y_p - y_t)), 4),
    }


def run_full_evaluation():
    logger.info("=" * 78)
    logger.info("  STARTING SCIENTIFIC EVALUATION & STRESS TESTING (MODEL 2 V3)")
    logger.info("=" * 78)

    cache_path = os.path.join(RESULTS_DIR, "_day_ahead_corpus.pkl")
    with open(cache_path, "rb") as f:
        df = pickle.load(f)

    train_df, val_df, test_df = get_chronological_splits(df)

    with open(os.path.join(MODELS_DIR, "best_model_fuel_v3.pkl"), "rb") as f:
        model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "scaler_fuel_v3.pkl"), "rb") as f:
        scaler = pickle.load(f)

    X_te_raw = test_df[FEATURE_COLUMNS].values
    X_test_s = scaler.transform(X_te_raw)
    y_test   = test_df[TARGET_NAME].values
    y_pred   = model.predict(X_test_s)
    residuals = y_test - y_pred

    eval_df = test_df.copy()
    eval_df["y_true"]    = y_test
    eval_df["y_pred"]    = y_pred
    eval_df["residual"]  = residuals
    eval_df["abs_error"] = np.abs(residuals)
    eval_df["pct_error"] = np.abs(residuals) / np.clip(y_test, 1.0, None) * 100

    preds_csv_path = os.path.join(RESULTS_DIR, "model2_v3_predictions.csv")
    eval_df.to_csv(preds_csv_path, index=False)
    logger.info("Saved full test prediction records to: %s", preds_csv_path)

    # ── 1. Overall Performance Metrics ─────────────────────────────────────────
    rmse_val = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae_val  = float(mean_absolute_error(y_test, y_pred))
    mape_val = float(mape(y_test, y_pred))
    r2_val   = float(r2_score(y_test, y_pred))
    res_mean = float(np.mean(residuals))
    res_std  = float(np.std(residuals))
    bias_val = float(np.mean(y_pred - y_test))

    # Prediction Interval Coverage Probability (PICP)
    # Using residual quantile intervals: 80%, 90%, 95%
    def calc_picp(alpha):
        low_q = np.percentile(residuals, (1 - alpha) / 2 * 100)
        high_q = np.percentile(residuals, (1 + alpha) / 2 * 100)
        covered = (residuals >= low_q) & (residuals <= high_q)
        return float(np.mean(covered) * 100), float(high_q - low_q)

    cov_80, w_80 = calc_picp(0.80)
    cov_90, w_90 = calc_picp(0.90)
    cov_95, w_95 = calc_picp(0.95)

    diff_res = np.diff(residuals)
    dw_stat  = float(np.sum(diff_res ** 2) / np.sum(residuals ** 2))

    overall_metrics = {
        "rmse_liters": round(rmse_val, 4),
        "mae_liters": round(mae_val, 4),
        "mape_pct": round(mape_val, 4),
        "r2_score": round(r2_val, 6),
        "residual_mean_liters": round(res_mean, 4),
        "residual_std_liters": round(res_std, 4),
        "bias_liters": round(bias_val, 4),
        "durbin_watson": round(dw_stat, 4),
        "interval_coverage_80pct": round(cov_80, 2),
        "interval_width_80pct_liters": round(w_80, 3),
        "interval_coverage_90pct": round(cov_90, 2),
        "interval_width_90pct_liters": round(w_90, 3),
        "interval_coverage_95pct": round(cov_95, 2),
        "interval_width_95pct_liters": round(w_95, 3),
        "test_samples": int(len(y_test)),
    }

    # ── 2. Scientific Stress Tests ─────────────────────────────────────────────
    logger.info("--> Running Scientific Stress Tests across operational regimes ...")

    # A. Seasonal: Summer vs Winter
    winter_mask = eval_df["is_shipping_season"] == 0
    summer_mask = eval_df["is_shipping_season"] == 1
    winter_perf = calc_subset(y_test[winter_mask], y_pred[winter_mask])
    summer_perf = calc_subset(y_test[summer_mask], y_pred[summer_mask])

    # B. Population: High (Top 25%) vs Low (Bottom 25%)
    q_pop25 = eval_df["scheduled_population"].quantile(0.25)
    q_pop75 = eval_df["scheduled_population"].quantile(0.75)
    high_pop_mask = eval_df["scheduled_population"] >= q_pop75
    low_pop_mask  = eval_df["scheduled_population"] <= q_pop25
    high_pop_perf = calc_subset(y_test[high_pop_mask], y_pred[high_pop_mask])
    low_pop_perf  = calc_subset(y_test[low_pop_mask], y_pred[low_pop_mask])

    # C. Storm Days (Wind >= 65 km/h) vs Normal Days
    storm_mask = eval_df["fc_wind_speed_kmh"] >= 65.0
    calm_mask  = eval_df["fc_wind_speed_kmh"] < 65.0
    storm_perf = calc_subset(y_test[storm_mask], y_pred[storm_mask])
    calm_perf  = calc_subset(y_test[calm_mask], y_pred[calm_mask])

    # D. Fuel Shortage (Tank Reserves < 2,000 L)
    shortage_mask = eval_df["fuel_stock_start_liters"] < 2000.0
    normal_fuel_mask = eval_df["fuel_stock_start_liters"] >= 2000.0
    shortage_perf = calc_subset(y_test[shortage_mask], y_pred[shortage_mask])
    normal_fuel_perf = calc_subset(y_test[normal_fuel_mask], y_pred[normal_fuel_mask])

    # E. Extreme Cold Snap (Forecast Temperature < -35°C)
    extreme_cold_mask = eval_df["fc_temperature_c"] < -35.0
    moderate_temp_mask = eval_df["fc_temperature_c"] >= -35.0
    cold_perf = calc_subset(y_test[extreme_cold_mask], y_pred[extreme_cold_mask])
    moderate_perf = calc_subset(y_test[moderate_temp_mask], y_pred[moderate_temp_mask])

    # F. Generator Outage / Stress (power risk score elevated)
    gen_stress_mask = eval_df["power_risk_lag1"] > 25.0
    gen_normal_mask = eval_df["power_risk_lag1"] <= 25.0
    gen_stress_perf = calc_subset(y_test[gen_stress_mask], y_pred[gen_stress_mask])
    gen_normal_perf = calc_subset(y_test[gen_normal_mask], y_pred[gen_normal_mask])

    stress_tests = {
        "winter_regime": winter_perf,
        "summer_regime": summer_perf,
        "high_population_regime": high_pop_perf,
        "low_population_regime": low_pop_perf,
        "storm_days_ge_65kmh": storm_perf,
        "calm_days_lt_65kmh": calm_perf,
        "fuel_shortage_stock_lt_2000L": shortage_perf,
        "normal_fuel_stock_ge_2000L": normal_fuel_perf,
        "extreme_cold_T_lt_minus35C": cold_perf,
        "moderate_temperature_ge_minus35C": moderate_perf,
        "generator_stress_risk_gt_25": gen_stress_perf,
        "generator_normal_risk_le_25": gen_normal_perf,
    }

    # ── 3. Monthly Metrics ─────────────────────────────────────────────────────
    monthly_metrics = {}
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for m in range(1, 13):
        m_mask = eval_df["month"] == m
        m_perf = calc_subset(y_test[m_mask], y_pred[m_mask])
        monthly_metrics[month_names[m - 1]] = {
            "month_num": m,
            "rmse_liters": m_perf["rmse"],
            "mae_liters": m_perf["mae"],
            "mape_pct": m_perf["mape_pct"],
            "samples": m_perf["n"],
        }

    full_evaluation = {
        "overall": overall_metrics,
        "stress_tests": stress_tests,
        "monthly": monthly_metrics,
    }

    with open(os.path.join(RESULTS_DIR, "detailed_evaluation_metrics.json"), "w") as f:
        json.dump(full_evaluation, f, indent=2)

    # ── 4. Feature Importance (Native) ─────────────────────────────────────────
    logger.info("Extracting native tree feature importance ...")
    if hasattr(model, "get_feature_importance"):
        fi_scores = model.get_feature_importance()
    elif hasattr(model, "feature_importances_"):
        fi_scores = model.feature_importances_
    elif hasattr(model, "feature_importance"):
        fi_scores = model.feature_importance(importance_type="gain")
    else:
        fi_scores = np.zeros(len(FEATURE_COLUMNS))

    fi_df = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "importance": fi_scores,
    }).sort_values("importance", ascending=False)
    fi_df.to_csv(os.path.join(RESULTS_DIR, "feature_importance.csv"), index=False)

    # ── 5. Permutation Feature Importance ──────────────────────────────────────
    logger.info("Computing Out-of-Sample Permutation Feature Importance ...")
    class ScaledWrapper(BaseEstimator, RegressorMixin):
        def __init__(self, m, sc):
            self.m = m
            self.sc = sc
            self._estimator_type = "regressor"
        def predict(self, X_raw):
            return self.m.predict(self.sc.transform(X_raw))
        def fit(self, X, y):
            return self

    wrapper = ScaledWrapper(model, scaler)
    n_sample = min(1500, len(X_te_raw))
    sub_idx = np.random.RandomState(RANDOM_SEED).choice(len(X_te_raw), n_sample, replace=False)
    perm = permutation_importance(
        wrapper, X_te_raw[sub_idx], y_test[sub_idx],
        scoring="neg_root_mean_squared_error",
        n_repeats=5,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )
    perm_df = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "importance_mean": perm.importances_mean,
        "importance_std": perm.importances_std,
    }).sort_values("importance_mean", ascending=False)
    perm_df.to_csv(os.path.join(RESULTS_DIR, "permutation_importance.csv"), index=False)

    # ── 6. TreeSHAP Values ─────────────────────────────────────────────────────
    logger.info("Computing TreeSHAP values on test sample ...")
    sample_size = min(1000, len(X_test_s))
    shap_idx = np.random.RandomState(RANDOM_SEED).choice(len(X_test_s), sample_size, replace=False)
    X_shap_s = X_test_s[shap_idx]
    X_shap_raw = eval_df[FEATURE_COLUMNS].iloc[shap_idx].copy()

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_shap_s)
    except Exception as exc:
        logger.warning("TreeExplainer fallback: %s", exc)
        X_tr_s = scaler.transform(train_df[FEATURE_COLUMNS].values)
        explainer = shap.Explainer(model.predict, X_tr_s[:200])
        shap_obj = explainer(X_shap_s)
        shap_values = shap_obj.values

    shap_df = pd.DataFrame(shap_values, columns=FEATURE_COLUMNS)
    shap_df.to_csv(os.path.join(RESULTS_DIR, "shap_values_sample.csv"), index=False)

    with open(os.path.join(RESULTS_DIR, "_shap_cache.pkl"), "wb") as f:
        pickle.dump({
            "shap_values": shap_values,
            "X_sample_raw": X_shap_raw,
            "feature_names": FEATURE_COLUMNS,
        }, f, protocol=4)

    logger.info("=" * 78)
    logger.info("MODEL 2 SCIENTIFIC EVALUATION COMPLETE:")
    logger.info("  Hold-Out Test RMSE:  %.3f Liters/day", overall_metrics["rmse_liters"])
    logger.info("  Hold-Out Test MAE:   %.3f Liters/day", overall_metrics["mae_liters"])
    logger.info("  Hold-Out Test MAPE:  %.2f%%", overall_metrics["mape_pct"])
    logger.info("  Hold-Out Test R²:    %.4f", overall_metrics["r2_score"])
    logger.info("  Mean Error (Bias):   %+.4f Liters/day", overall_metrics["bias_liters"])
    logger.info("  Winter RMSE:         %.3f Liters/day", winter_perf["rmse"])
    logger.info("  Summer RMSE:         %.3f Liters/day", summer_perf["rmse"])
    logger.info("  Storm Regime RMSE:   %.3f Liters/day", storm_perf["rmse"])
    logger.info("  Extreme Cold RMSE:   %.3f Liters/day", cold_perf["rmse"])
    logger.info("=" * 78)

    return full_evaluation


if __name__ == "__main__":
    run_full_evaluation()
