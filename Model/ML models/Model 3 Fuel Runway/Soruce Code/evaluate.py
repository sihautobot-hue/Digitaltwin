"""
evaluate.py
-----------
Comprehensive evaluation and stress testing module for Model 3 V3.
Includes:
  - Chronological performance analysis
  - Operational regime-wise decomposition
  - Station-wise generalization
  - Residual distribution analysis
  - Prediction interval estimation via quantile residuals
"""

import json
import logging
import os
import pickle
import warnings
from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Evaluate-Model3-V3")

from config import FEATURE_COLUMNS, MODELS_DIR, RESULTS_DIR, TARGET_NAME, TARGET_CLIP


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true > 0.5
    if mask.sum() == 0:
        return np.nan
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mp   = mape(y_true, y_pred)
    bias = float(np.mean(y_pred - y_true))
    p25, p50, p75 = np.percentile(np.abs(y_pred - y_true), [25, 50, 75])
    return {
        "mae":       round(float(mae), 4),
        "rmse":      round(float(rmse), 4),
        "r2":        round(float(r2), 6),
        "mape_pct":  round(float(mp), 3),
        "bias_days": round(float(bias), 4),
        "p25_abs_err": round(float(p25), 4),
        "p50_abs_err": round(float(p50), 4),
        "p75_abs_err": round(float(p75), 4),
    }


def load_model_artifacts():
    with open(os.path.join(MODELS_DIR, "best_model_v3.pkl"), "rb") as f:
        model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "scaler_v3.pkl"), "rb") as f:
        scaler = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "feature_columns_v3.json")) as f:
        feat_cols = json.load(f)
    return model, scaler, feat_cols


def prep_X(df: pd.DataFrame, feat_cols: List[str], scaler: StandardScaler) -> np.ndarray:
    avail = [f for f in feat_cols if f in df.columns]
    X = df[avail].copy().fillna(0.0)
    for c in X.select_dtypes("bool"):
        X[c] = X[c].astype(int)
    return scaler.transform(X.values)


def full_evaluation(df_full: pd.DataFrame, test_df: pd.DataFrame) -> Dict:
    """Run complete evaluation suite on the final trained model."""
    model, scaler, feat_cols = load_model_artifacts()
    X_te = prep_X(test_df, feat_cols, scaler)
    y_te = test_df[TARGET_NAME].values
    preds = model.predict(X_te)
    test_df = test_df.copy()
    test_df["y_pred"] = preds
    test_df["residual"] = preds - y_te
    test_df["abs_residual"] = np.abs(preds - y_te)

    results: Dict = {}

    # ── Overall Test Metrics ────────────────────────────────────────────────────
    results["overall"] = compute_metrics(y_te, preds)
    logger.info("Overall Test: MAE=%.2fd RMSE=%.2fd R²=%.4f MAPE=%.2f%%",
                results["overall"]["mae"], results["overall"]["rmse"],
                results["overall"]["r2"], results["overall"]["mape_pct"])

    # ── Chronological Year-wise Breakdown ──────────────────────────────────────
    year_metrics = {}
    for yr in sorted(test_df["year"].unique()):
        m = test_df[test_df["year"] == yr]
        if len(m) < 5:
            continue
        X_yr = prep_X(m, feat_cols, scaler)
        y_yr = m[TARGET_NAME].values
        p_yr = model.predict(X_yr)
        year_metrics[int(yr)] = compute_metrics(y_yr, p_yr)
    results["year_wise"] = year_metrics

    # ── Station-wise Performance ───────────────────────────────────────────────
    station_metrics = {}
    for sid in test_df["station_id"].unique():
        m = test_df[test_df["station_id"] == sid]
        if len(m) < 5:
            continue
        X_st = prep_X(m, feat_cols, scaler)
        y_st = m[TARGET_NAME].values
        p_st = model.predict(X_st)
        station_metrics[sid] = compute_metrics(y_st, p_st)
    results["station_wise"] = station_metrics

    # ── Fuel Runway Regime Stress Test ────────────────────────────────────────
    regimes = {
        "critical (<10d)":     (test_df[TARGET_NAME] < 10),
        "low (10–30d)":        (test_df[TARGET_NAME] >= 10)  & (test_df[TARGET_NAME] < 30),
        "moderate (30–90d)":   (test_df[TARGET_NAME] >= 30)  & (test_df[TARGET_NAME] < 90),
        "comfortable (90–180d)":  (test_df[TARGET_NAME] >= 90)  & (test_df[TARGET_NAME] < 180),
        "ample (180–365d)":    (test_df[TARGET_NAME] >= 180) & (test_df[TARGET_NAME] <= TARGET_CLIP),
    }
    regime_metrics = {}
    for lbl, mask in regimes.items():
        m = test_df[mask]
        if len(m) < 5:
            regime_metrics[lbl] = {"n": len(m), "note": "insufficient samples"}
            continue
        X_r = prep_X(m, feat_cols, scaler)
        y_r = m[TARGET_NAME].values
        p_r = model.predict(X_r)
        met = compute_metrics(y_r, p_r)
        met["n"] = len(m)
        regime_metrics[lbl] = met
    results["regime_wise"] = regime_metrics

    # ── Shipping Season vs Off-Season ─────────────────────────────────────────
    season_metrics = {}
    if "is_shipping_season" in test_df.columns:
        for lbl, flag in [("shipping_season", 1), ("off_season", 0)]:
            m = test_df[test_df["is_shipping_season"] == flag]
            if len(m) < 5:
                continue
            X_s = prep_X(m, feat_cols, scaler)
            y_s = m[TARGET_NAME].values
            p_s = model.predict(X_s)
            met = compute_metrics(y_s, p_s)
            met["n"] = len(m)
            season_metrics[lbl] = met
    results["shipping_season"] = season_metrics

    # ── Weather Regime Decomposition ──────────────────────────────────────────
    weather_metrics = {}
    if "fc_weather_severity" in test_df.columns:
        for sev, lbl in [(0, "calm"), (1, "normal"), (2, "windy"), (3, "severe"), (4, "extreme")]:
            m = test_df[test_df["fc_weather_severity"] == sev]
            if len(m) < 5:
                continue
            X_w = prep_X(m, feat_cols, scaler)
            y_w = m[TARGET_NAME].values
            p_w = model.predict(X_w)
            met = compute_metrics(y_w, p_w)
            met["n"] = len(m)
            weather_metrics[lbl] = met
    results["weather_regime"] = weather_metrics

    # ── Residual Statistics ────────────────────────────────────────────────────
    resids = preds - y_te
    results["residuals"] = {
        "mean":  round(float(np.mean(resids)), 4),
        "std":   round(float(np.std(resids)), 4),
        "skewness": round(float(pd.Series(resids).skew()), 4),
        "kurtosis": round(float(pd.Series(resids).kurtosis()), 4),
        "p5":    round(float(np.percentile(resids,  5)), 4),
        "p25":   round(float(np.percentile(resids, 25)), 4),
        "p50":   round(float(np.percentile(resids, 50)), 4),
        "p75":   round(float(np.percentile(resids, 75)), 4),
        "p95":   round(float(np.percentile(resids, 95)), 4),
    }

    # ── Quantile Prediction Intervals (90% coverage) ──────────────────────────
    abs_resids = np.abs(resids)
    q90 = np.percentile(abs_resids, 90)
    coverage = float(np.mean(abs_resids <= q90))
    results["prediction_interval_90pct"] = {
        "half_width_days": round(float(q90), 2),
        "coverage": round(coverage, 4),
    }
    logger.info("90%% Prediction Interval: ± %.2f days | Coverage: %.1f%%", q90, coverage * 100)

    # Save evaluation results
    out_path = os.path.join(RESULTS_DIR, "evaluation_v3.json")
    with open(out_path, "w") as fp:
        json.dump(results, fp, indent=2)
    logger.info("Evaluation saved to %s", out_path)

    # Save predictions for plotting
    test_df.to_csv(os.path.join(RESULTS_DIR, "test_predictions_v3.csv"), index=False)

    return results, test_df, model, scaler, feat_cols


if __name__ == "__main__":
    from feature_engineering import load_raw_corpus, build_fuel_runway_dataset, get_chronological_splits
    df_raw = load_raw_corpus()
    df = build_fuel_runway_dataset(df_raw)
    df["year"] = pd.to_datetime(df["date"]).dt.year
    _, _, test_df = get_chronological_splits(df)
    full_evaluation(df, test_df)
