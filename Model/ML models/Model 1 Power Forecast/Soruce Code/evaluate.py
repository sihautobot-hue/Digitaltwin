"""
evaluate.py
-----------
Comprehensive scientific evaluation and explainability suite for Model 1 (Version 3).
Calculates:
  1. Overall Performance: RMSE, MAE, MAPE, R², Bias, Residual Mean & Std
  2. Regime Performance:
      - Seasonal RMSE (Winter vs Summer)
      - Monthly RMSE (January through December)
      - Storm RMSE (Wind Speed >= 65 km/h)
      - Population Transition RMSE (|pop_trend7| >= 5)
  3. Feature Importance (Native tree gain & SHAP values)
  4. Exports test predictions CSV with residuals and all metadata
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
import shap

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Evaluate-V3")

from config import (
    MODELS_DIR,
    RESULTS_DIR,
    FEATURE_COLUMNS,
    TARGET_NAME,
    RANDOM_SEED,
)
from feature_engineering import get_chronological_splits


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def calc_subset_rmse(y_t: np.ndarray, y_p: np.ndarray) -> Dict[str, Any]:
    if len(y_t) == 0:
        return {"n": 0, "rmse": 0.0, "mae": 0.0, "mape_pct": 0.0}
    return {
        "n": int(len(y_t)),
        "rmse": round(float(np.sqrt(mean_squared_error(y_t, y_p))), 4),
        "mae": round(float(mean_absolute_error(y_t, y_p)), 4),
        "mape_pct": round(float(mape(y_t, y_p)), 4),
    }


def run_full_evaluation():
    logger.info("=" * 78)
    logger.info("  STARTING RIGOROUS SCIENTIFIC EVALUATION FOR MODEL 1 V3")
    logger.info("=" * 78)

    # 1. Load cached dataset & best model
    cache_path = os.path.join(RESULTS_DIR, "_day_ahead_corpus.pkl")
    with open(cache_path, "rb") as f:
        df = pickle.load(f)

    train_df, val_df, test_df = get_chronological_splits(df)

    with open(os.path.join(MODELS_DIR, "best_model_power_v3.pkl"), "rb") as f:
        model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "scaler_power_v3.pkl"), "rb") as f:
        scaler = pickle.load(f)

    X_test_s = scaler.transform(test_df[FEATURE_COLUMNS].values)
    y_test   = test_df[TARGET_NAME].values
    y_pred   = model.predict(X_test_s)
    residuals = y_test - y_pred

    # Attach predictions and residual metadata
    eval_df = test_df.copy()
    eval_df["y_true"]    = y_test
    eval_df["y_pred"]    = y_pred
    eval_df["residual"]  = residuals
    eval_df["abs_error"] = np.abs(residuals)
    eval_df["pct_error"] = np.abs(residuals) / np.clip(y_test, 1.0, None) * 100

    # Save detailed predictions CSV
    preds_csv_path = os.path.join(RESULTS_DIR, "model1_v3_predictions.csv")
    eval_df.to_csv(preds_csv_path, index=False)
    logger.info("Saved full prediction records to: %s", preds_csv_path)

    # ── 1. Overall Metrics ─────────────────────────────────────────────────────
    rmse_val = float(np.sqrt(mean_squared_error(y_test, y_pred)))
    mae_val  = float(mean_absolute_error(y_test, y_pred))
    mape_val = float(mape(y_test, y_pred))
    r2_val   = float(r2_score(y_test, y_pred))
    res_mean = float(np.mean(residuals))
    res_std  = float(np.std(residuals))
    bias_val = float(np.mean(y_pred - y_test))

    # Durbin-Watson statistic for residual autocorrelation
    diff_res = np.diff(residuals)
    dw_stat  = float(np.sum(diff_res ** 2) / np.sum(residuals ** 2))

    overall_metrics = {
        "rmse_kw": round(rmse_val, 4),
        "mae_kw": round(mae_val, 4),
        "mape_pct": round(mape_val, 4),
        "r2_score": round(r2_val, 6),
        "residual_mean_kw": round(res_mean, 4),
        "residual_std_kw": round(res_std, 4),
        "bias_kw": round(bias_val, 4),
        "durbin_watson": round(dw_stat, 4),
        "test_samples": int(len(y_test)),
    }

    # ── 2. Seasonal Metrics (Winter vs Summer) ─────────────────────────────────
    winter_mask = eval_df["is_shipping_season"] == 0
    summer_mask = eval_df["is_shipping_season"] == 1
    winter_perf = calc_subset_rmse(y_test[winter_mask], y_pred[winter_mask])
    summer_perf = calc_subset_rmse(y_test[summer_mask], y_pred[summer_mask])

    seasonal_metrics = {
        "winter_rmse_kw": winter_perf["rmse"],
        "winter_mae_kw": winter_perf["mae"],
        "winter_mape_pct": winter_perf["mape_pct"],
        "winter_samples": winter_perf["n"],
        "summer_rmse_kw": summer_perf["rmse"],
        "summer_mae_kw": summer_perf["mae"],
        "summer_mape_pct": summer_perf["mape_pct"],
        "summer_samples": summer_perf["n"],
    }

    # ── 3. Monthly Metrics (Jan through Dec) ───────────────────────────────────
    monthly_metrics = {}
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    for m in range(1, 13):
        m_mask = eval_df["month"] == m
        m_perf = calc_subset_rmse(y_test[m_mask], y_pred[m_mask])
        monthly_metrics[month_names[m - 1]] = {
            "month_num": m,
            "rmse_kw": m_perf["rmse"],
            "mae_kw": m_perf["mae"],
            "mape_pct": m_perf["mape_pct"],
            "samples": m_perf["n"],
        }

    # ── 4. Operational Regime Metrics (Storms & Population Transitions) ────────
    storm_mask = eval_df["fc_wind_speed_kmh"] >= 65.0
    calm_mask  = eval_df["fc_wind_speed_kmh"] < 65.0
    storm_perf = calc_subset_rmse(y_test[storm_mask], y_pred[storm_mask])
    calm_perf  = calc_subset_rmse(y_test[calm_mask], y_pred[calm_mask])

    pop_trans_mask = eval_df["pop_trend7"].abs() >= 5.0
    pop_stable_mask= eval_df["pop_trend7"].abs() < 5.0
    pop_trans_perf = calc_subset_rmse(y_test[pop_trans_mask], y_pred[pop_trans_mask])
    pop_stable_perf= calc_subset_rmse(y_test[pop_stable_mask], y_pred[pop_stable_mask])

    regime_metrics = {
        "storm_rmse_kw": storm_perf["rmse"],
        "storm_mae_kw": storm_perf["mae"],
        "storm_samples": storm_perf["n"],
        "calm_rmse_kw": calm_perf["rmse"],
        "calm_mae_kw": calm_perf["mae"],
        "calm_samples": calm_perf["n"],
        "pop_transition_rmse_kw": pop_trans_perf["rmse"],
        "pop_transition_mae_kw": pop_trans_perf["mae"],
        "pop_transition_samples": pop_trans_perf["n"],
        "pop_stable_rmse_kw": pop_stable_perf["rmse"],
        "pop_stable_mae_kw": pop_stable_perf["mae"],
        "pop_stable_samples": pop_stable_perf["n"],
    }

    # Combine all evaluation records
    full_evaluation = {
        "overall": overall_metrics,
        "seasonal": seasonal_metrics,
        "monthly": monthly_metrics,
        "regimes": regime_metrics,
    }

    eval_json_path = os.path.join(RESULTS_DIR, "detailed_evaluation_metrics.json")
    with open(eval_json_path, "w") as f:
        json.dump(full_evaluation, f, indent=2)
    logger.info("Saved comprehensive metrics JSON to: %s", eval_json_path)

    # ── 5. Feature Importance Extraction ───────────────────────────────────────
    logger.info("Extracting feature importance scores ...")
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
    fi_csv_path = os.path.join(RESULTS_DIR, "feature_importance.csv")
    fi_df.to_csv(fi_csv_path, index=False)
    logger.info("Saved feature importance to: %s", fi_csv_path)

    # ── 6. SHAP Values Computation ─────────────────────────────────────────────
    logger.info("Computing SHAP values on representative hold-out sample ...")
    sample_size = min(1000, len(X_test_s))
    rng = np.random.RandomState(RANDOM_SEED)
    sample_idx = rng.choice(len(X_test_s), sample_size, replace=False)
    X_sample_s = X_test_s[sample_idx]
    X_sample_raw = eval_df[FEATURE_COLUMNS].iloc[sample_idx].copy()

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample_s)
    except Exception as exc:
        logger.warning("TreeExplainer fallback: %s", exc)
        X_tr_s = scaler.transform(train_df[FEATURE_COLUMNS].values)
        explainer = shap.Explainer(model.predict, X_tr_s[:200])
        shap_obj = explainer(X_sample_s)
        shap_values = shap_obj.values

    shap_df = pd.DataFrame(shap_values, columns=FEATURE_COLUMNS)
    shap_csv_path = os.path.join(RESULTS_DIR, "shap_values_sample.csv")
    shap_df.to_csv(shap_csv_path, index=False)
    logger.info("Saved SHAP values table to: %s", shap_csv_path)

    # Cache SHAP bundle for plotting
    with open(os.path.join(RESULTS_DIR, "_shap_cache.pkl"), "wb") as f:
        pickle.dump({
            "shap_values": shap_values,
            "X_sample_raw": X_sample_raw,
            "feature_names": FEATURE_COLUMNS,
        }, f, protocol=4)

    # Print summary
    logger.info("=" * 78)
    logger.info("SCIENTIFIC EVALUATION SUMMARY:")
    logger.info("  Hold-Out Test RMSE:  %.3f kW", overall_metrics["rmse_kw"])
    logger.info("  Hold-Out Test MAE:   %.3f kW", overall_metrics["mae_kw"])
    logger.info("  Hold-Out Test MAPE:  %.2f%%", overall_metrics["mape_pct"])
    logger.info("  Hold-Out Test R²:    %.4f", overall_metrics["r2_score"])
    logger.info("  Hold-Out Mean Bias:  %+.4f kW", overall_metrics["bias_kw"])
    logger.info("  Winter RMSE:         %.3f kW", seasonal_metrics["winter_rmse_kw"])
    logger.info("  Summer RMSE:         %.3f kW", seasonal_metrics["summer_rmse_kw"])
    logger.info("  Storm Regime RMSE:   %.3f kW", regime_metrics["storm_rmse_kw"])
    logger.info("  Pop Transition RMSE: %.3f kW", regime_metrics["pop_transition_rmse_kw"])
    logger.info("=" * 78)

    return full_evaluation


if __name__ == "__main__":
    run_full_evaluation()
