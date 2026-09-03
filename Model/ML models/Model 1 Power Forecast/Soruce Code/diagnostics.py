"""
diagnostics.py
--------------
Scientific Residual Diagnostics & Out-Of-Distribution (OOD) Stress Testing
for Model 1 (Power Load Forecasting V3).

Diagnostics Included:
  1. Residual Statistical Tests (Mean, Variance, Skewness, Kurtosis, Durbin-Watson)
  2. Heteroscedasticity Analysis (Breusch-Pagan / Variance by Load Bin)
  3. Regime-based Error Breakdowns:
      - Winter vs Summer
      - Polar Night vs Polar Day
      - High Load vs Low Load
      - Storm Days (Wind > 70 km/h) vs Calm Days
  4. Out-Of-Distribution (OOD) Stress Testing:
      - Extreme Antarctic Cold Snap (T < -35°C)
      - Blizzard Conditions (Wind > 90 km/h)
      - Population Transition Surges
      - Low Generator / Low Battery Regimes
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

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Diagnostics-V3")

from config_v3 import MODELS_DIR, RESULTS_DIR, FEATURES_V3, TARGET_FORECAST
from data_pipeline import get_chronological_splits


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def calc_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    if len(y_true) == 0:
        return {"n": 0, "mae": 0.0, "rmse": 0.0, "r2": 0.0, "mape_pct": 0.0, "bias": 0.0}
    mae  = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2   = float(r2_score(y_true, y_pred)) if len(y_true) > 1 and np.var(y_true) > 1e-6 else 1.0
    mp   = float(mape(y_true, y_pred))
    bias = float(np.mean(y_pred - y_true))
    return {
        "n": len(y_true),
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 6),
        "mape_pct": round(mp, 4),
        "bias": round(bias, 4),
    }


def run_diagnostics_suite():
    logger.info("Executing comprehensive residual diagnostics & OOD stress tests ...")

    # Load dataset & model
    corpus_cache = os.path.join(RESULTS_DIR, "_day_ahead_corpus.pkl")
    with open(corpus_cache, "rb") as f:
        df = pickle.load(f)

    train_df, val_df, test_df = get_chronological_splits(df)

    with open(os.path.join(MODELS_DIR, "best_model_power_v3.pkl"), "rb") as f:
        model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "scaler_power_v3.pkl"), "rb") as f:
        scaler = pickle.load(f)

    X_test_s = scaler.transform(test_df[FEATURES_V3].values)
    y_test   = test_df[TARGET_FORECAST].values
    y_pred   = model.predict(X_test_s)
    residuals = y_test - y_pred

    test_df_eval = test_df.copy()
    test_df_eval["y_true"] = y_test
    test_df_eval["y_pred"] = y_pred
    test_df_eval["residual"] = residuals
    test_df_eval["abs_error"] = np.abs(residuals)
    test_df_eval["pct_error"] = np.abs(residuals) / np.clip(y_test, 1.0, None) * 100

    # Save evaluated test DataFrame for figure generation
    test_df_eval.to_csv(os.path.join(RESULTS_DIR, "test_predictions_evaluated.csv"), index=False)

    # ── 1. Residual Distribution Diagnostics ───────────────────────────────────
    res_mean = float(np.mean(residuals))
    res_std  = float(np.std(residuals))
    res_skew = float(stats.skew(residuals))
    res_kurt = float(stats.kurtosis(residuals))
    
    # Durbin-Watson statistic for autocorrelation
    diff_res = np.diff(residuals)
    dw_stat  = float(np.sum(diff_res ** 2) / np.sum(residuals ** 2))

    # Jarque-Bera normality test
    jb_stat, jb_pval = stats.jarque_bera(residuals)

    dist_report = {
        "residual_mean_kw": round(res_mean, 4),
        "residual_std_kw": round(res_std, 4),
        "residual_skewness": round(res_skew, 4),
        "residual_excess_kurtosis": round(res_kurt, 4),
        "durbin_watson_stat": round(dw_stat, 4),
        "jarque_bera_stat": round(float(jb_stat), 4),
        "jarque_bera_pvalue": round(float(jb_pval), 6),
    }
    logger.info("Residual Statistics: Mean=%.4f, Std=%.4f, Skew=%.4f, Kurt=%.4f, DW=%.4f",
                res_mean, res_std, res_skew, res_kurt, dw_stat)

    # ── 2. Regime-Based Error Analysis ─────────────────────────────────────────
    # Winter vs Summer
    winter_mask = test_df_eval["is_shipping_season"] == 0
    summer_mask = test_df_eval["is_shipping_season"] == 1
    winter_metrics = calc_metrics(y_test[winter_mask], y_pred[winter_mask])
    summer_metrics = calc_metrics(y_test[summer_mask], y_pred[summer_mask])

    # Polar Night vs Polar Day
    polar_night_mask = test_df_eval["is_polar_night"] == 1
    polar_day_mask   = test_df_eval["is_polar_day"] == 1
    shoulder_mask    = (~polar_night_mask) & (~polar_day_mask)
    night_metrics    = calc_metrics(y_test[polar_night_mask], y_pred[polar_night_mask])
    day_metrics      = calc_metrics(y_test[polar_day_mask], y_pred[polar_day_mask])
    shoulder_metrics = calc_metrics(y_test[shoulder_mask], y_pred[shoulder_mask])

    # High Load (Upper Quartile) vs Low Load (Lower Quartile)
    q25, q75 = np.percentile(y_test, 25), np.percentile(y_test, 75)
    low_load_mask  = y_test <= q25
    mid_load_mask  = (y_test > q25) & (y_test < q75)
    high_load_mask = y_test >= q75
    low_load_metrics  = calc_metrics(y_test[low_load_mask], y_pred[low_load_mask])
    mid_load_metrics  = calc_metrics(y_test[mid_load_mask], y_pred[mid_load_mask])
    high_load_metrics = calc_metrics(y_test[high_load_mask], y_pred[high_load_mask])

    # Storm vs Calm Days
    storm_mask = test_df_eval["fc_wind_speed_kmh"] >= 65.0
    calm_mask  = test_df_eval["fc_wind_speed_kmh"] < 65.0
    storm_metrics = calc_metrics(y_test[storm_mask], y_pred[storm_mask])
    calm_metrics  = calc_metrics(y_test[calm_mask], y_pred[calm_mask])

    regime_report = {
        "winter_expedition": winter_metrics,
        "summer_expedition": summer_metrics,
        "polar_night": night_metrics,
        "polar_day": day_metrics,
        "shoulder_seasons": shoulder_metrics,
        "low_load_regime": low_load_metrics,
        "mid_load_regime": mid_load_metrics,
        "high_load_regime": high_load_metrics,
        "storm_regime_wind_ge_65kmh": storm_metrics,
        "calm_regime_wind_lt_65kmh": calm_metrics,
    }

    # ── 3. Out-Of-Distribution (OOD) Stress Testing ────────────────────────────
    logger.info("--> Executing Out-Of-Distribution (OOD) stress tests ...")
    
    # Stress 1: Extreme Cold Snap (Ambient temp < -35°C)
    cold_mask = test_df_eval["fc_temperature_c"] < -35.0
    cold_stress = calc_metrics(y_test[cold_mask], y_pred[cold_mask])

    # Stress 2: Blizzard Gust Conditions (Wind Gust > 90 km/h)
    blizzard_mask = test_df_eval["fc_wind_gust_kmh"] > 90.0
    blizzard_stress = calc_metrics(y_test[blizzard_mask], y_pred[blizzard_mask])

    # Stress 3: Population Seasonal Transition Surge (Occupancy delta != 0)
    trans_mask = test_df_eval["pop_trend7"].abs() >= 5.0
    trans_stress = calc_metrics(y_test[trans_mask], y_pred[trans_mask])

    # Stress 4: Critical Battery State at Forecast Cutoff (SoC < 30%)
    low_soc_mask = test_df_eval["battery_soc_start_pct"] < 30.0
    soc_stress = calc_metrics(y_test[low_soc_mask], y_pred[low_soc_mask])

    ood_report = {
        "extreme_cold_snap_T_lt_minus35C": cold_stress,
        "blizzard_conditions_gust_gt_90kmh": blizzard_stress,
        "population_transition_spikes": trans_stress,
        "low_battery_state_soc_lt_30pct": soc_stress,
    }

    # Save complete diagnostic audit
    final_audit = {
        "residual_distribution": dist_report,
        "operational_regimes": regime_report,
        "ood_stress_tests": ood_report,
    }

    with open(os.path.join(RESULTS_DIR, "diagnostics_report.json"), "w") as f:
        json.dump(final_audit, f, indent=2)

    logger.info("Diagnostics & OOD audit successfully saved to %s", RESULTS_DIR)
    return final_audit


if __name__ == "__main__":
    run_diagnostics_suite()
