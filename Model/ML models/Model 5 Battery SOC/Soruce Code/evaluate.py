"""
evaluate.py
-----------
Step 7: Comprehensive Scientific Evaluation, Regime Stress Testing,
Residual Drift Analysis, and Uncertainty Interval Calibration.
Model 5 (Version 3): Day-Ahead Battery State of Charge Forecasting
"""

import os
import json
import logging
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

from config import RESULTS_DIR, REGIMES, FEATURE_COLUMNS, TARGET_FORECAST

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Evaluate-M5V3")


def calc_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate MAPE with zero protection."""
    denom = np.maximum(np.abs(y_true), 1.0)
    return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)


def compute_durbin_watson(residuals: np.ndarray) -> float:
    """Compute Durbin-Watson statistic for serial correlation."""
    diff = np.diff(residuals)
    return float(np.sum(diff ** 2) / np.maximum(np.sum(residuals ** 2), 1e-8))


def compute_prediction_intervals(
    train_residuals: np.ndarray,
    test_residuals: np.ndarray
) -> Dict[str, Dict[str, float]]:
    """
    Calibrate and test empirical prediction intervals at 80%, 90%, and 95% confidence levels.
    """
    coverage_results = {}
    for conf in [0.80, 0.90, 0.95]:
        alpha = (1.0 - conf) / 2.0
        lower_q = float(np.percentile(train_residuals, alpha * 100))
        upper_q = float(np.percentile(train_residuals, (1.0 - alpha) * 100))
        width = upper_q - lower_q

        # Test empirical coverage on test residuals
        in_bounds = (test_residuals >= lower_q) & (test_residuals <= upper_q)
        emp_coverage = float(np.mean(in_bounds) * 100.0)

        coverage_results[f"{int(conf * 100)}%"] = {
            "nominal_coverage_pct": conf * 100.0,
            "empirical_coverage_pct": round(emp_coverage, 2),
            "interval_width_pct": round(width, 4),
            "lower_bound_delta": round(lower_q, 4),
            "upper_bound_delta": round(upper_q, 4),
        }
    return coverage_results


def evaluate_stress_regimes(
    test_df: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluate Model 5 performance across 7 distinct operational microgrid regimes.
    """
    regime_metrics = {}
    print("\n" + "=" * 80)
    print("STEP 7: OPERATIONAL REGIME STRESS TESTS (HOLDOUT TEST YEAR 2022)")
    print("=" * 80)

    rows = []
    for regime_name, condition_fn in REGIMES.items():
        mask = condition_fn(test_df).values
        n_samples = int(np.sum(mask))

        if n_samples == 0:
            regime_metrics[regime_name] = {"sample_count": 0, "status": "No occurrences in test set"}
            continue

        y_t = y_true[mask]
        y_p = y_pred[mask]
        res = y_t - y_p

        rmse = float(np.sqrt(mean_squared_error(y_t, y_p)))
        mae = float(mean_absolute_error(y_t, y_p))
        mape = calc_mape(y_t, y_p)
        r2 = float(r2_score(y_t, y_p)) if len(np.unique(y_t)) > 1 else 0.0
        bias = float(np.mean(y_p - y_t))

        regime_metrics[regime_name] = {
            "sample_count": n_samples,
            "rmse_pct": round(rmse, 4),
            "mae_pct": round(mae, 4),
            "mape_pct": round(mape, 3),
            "r2_score": round(r2, 4),
            "mean_bias_pct": round(bias, 4),
        }

        rows.append({
            "Operational Regime": regime_name,
            "Sample Count (N)": n_samples,
            "RMSE (%)": round(rmse, 4),
            "MAE (%)": round(mae, 4),
            "MAPE (%)": round(mape, 3),
            "R2 Score": round(r2, 4),
            "Mean Bias (%)": round(bias, 4),
        })

    rdf = pd.DataFrame(rows)
    print(rdf.to_string(index=False))
    print("=" * 80 + "\n")
    return regime_metrics


def perform_full_evaluation(
    model: Any,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    model_name: str
) -> Tuple[Dict[str, Any], np.ndarray, np.ndarray, np.ndarray]:
    """
    Execute full scientific evaluation and return comprehensive metrics dictionary.
    """
    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET_FORECAST].values
    train_preds = model.predict(X_train)
    train_residuals = y_train - train_preds

    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_FORECAST].values
    test_preds = model.predict(X_test)
    test_residuals = y_test - test_preds

    # Global Metrics
    rmse = float(np.sqrt(mean_squared_error(y_test, test_preds)))
    mae = float(mean_absolute_error(y_test, test_preds))
    mape = calc_mape(y_test, test_preds)
    r2 = float(r2_score(y_test, test_preds))
    bias = float(np.mean(test_preds - y_test))
    residual_std = float(np.std(test_residuals))

    # Serial drift & autocorrelation
    dw = compute_durbin_watson(test_residuals)
    lag1_autocorr = float(pd.Series(test_residuals).autocorr(lag=1))

    # Prediction Interval Calibration
    pi_coverage = compute_prediction_intervals(train_residuals, test_residuals)

    # Regime Stress Tests
    regime_results = evaluate_stress_regimes(test_df, y_test, test_preds)

    metrics_payload = {
        "model_name": model_name,
        "version": "V3",
        "target": "battery_soc_percent (Day t+1 End-of-Day SoC %)",
        "prediction_time": "18:00 on Day t",
        "forecast_horizon": "End of Day t+1 (24-hour lead)",
        "test_year": 2022,
        "test_sample_count": len(test_df),
        "global_metrics": {
            "rmse_pct": round(rmse, 4),
            "mae_pct": round(mae, 4),
            "mape_pct": round(mape, 3),
            "r2_score": round(r2, 6),
            "mean_bias_pct": round(bias, 4),
            "residual_std_pct": round(residual_std, 4),
            "durbin_watson": round(dw, 4),
            "residual_lag1_autocorrelation": round(lag1_autocorr, 4),
        },
        "prediction_interval_coverage": pi_coverage,
        "regime_stress_tests": regime_results,
    }

    print("=" * 80)
    print("GLOBAL TEST METRICS (HOLDOUT YEAR 2022, N=3,600):")
    print(f"  • Root Mean Squared Error (RMSE):        {metrics_payload['global_metrics']['rmse_pct']}%")
    print(f"  • Mean Absolute Error (MAE):             {metrics_payload['global_metrics']['mae_pct']}%")
    print(f"  • Mean Absolute Percentage Error (MAPE): {metrics_payload['global_metrics']['mape_pct']}%")
    print(f"  • Coefficient of Determination (R²):     {metrics_payload['global_metrics']['r2_score']}")
    print(f"  • Mean Error (Bias):                     {metrics_payload['global_metrics']['mean_bias_pct']}%")
    print(f"  • Residual Standard Deviation:           {metrics_payload['global_metrics']['residual_std_pct']}%")
    print(f"  • Durbin-Watson Statistic:               {metrics_payload['global_metrics']['durbin_watson']}")
    print(f"  • Residual Lag-1 Autocorrelation:        {metrics_payload['global_metrics']['residual_lag1_autocorrelation']}")
    print("=" * 80)

    # Save to JSON
    json_path = os.path.join(RESULTS_DIR, "metrics_battery_soc.json")
    with open(json_path, "w") as fp:
        json.dump(metrics_payload, fp, indent=2)
    logger.info("Saved evaluation metrics JSON to %s", json_path)

    return metrics_payload, y_test, test_preds, test_residuals
