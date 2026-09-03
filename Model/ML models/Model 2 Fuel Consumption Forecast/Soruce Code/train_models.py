"""
train_models.py
---------------
Production training and algorithm selection pipeline for Model 2 (Version 3).
Trains and benchmarks 8 distinct algorithms:
  1. Linear Regression
  2. ElasticNet
  3. Random Forest
  4. Extra Trees
  5. HistGradientBoosting
  6. XGBoost
  7. LightGBM
  8. CatBoost

Selection Rule:
  Winner chosen strictly by validation RMSE (2020–2021).
  Executes LOSO cross-validation with duplicate run disclosure.
"""

import os
import sys
import json
import time
import pickle
import logging
import warnings
from typing import Dict, Any, List, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, ElasticNet
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostRegressor

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("TrainModels-Model2-V3")

from config import (
    MODELS_DIR,
    RESULTS_DIR,
    FEATURE_COLUMNS,
    TARGET_NAME,
    MODEL_CONFIGS,
    RANDOM_SEED,
)
from feature_engineering import (
    verify_simulation_hashes,
    load_raw_corpus,
    build_day_ahead_fuel_dataset,
    get_chronological_splits,
    get_loso_splits,
)

np.random.seed(RANDOM_SEED)


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def calc_metrics(name: str, y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    mae  = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2   = float(r2_score(y_true, y_pred))
    mp   = float(mape(y_true, y_pred))
    bias = float(np.mean(y_pred - y_true))
    metrics = {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "r2": round(r2, 6),
        "mape_pct": round(mp, 4),
        "bias": round(bias, 4),
    }
    logger.info("  [%s] MAE=%.3f L | RMSE=%.3f L | R²=%.4f | MAPE=%.2f%% | Bias=%.3f L",
                name, mae, rmse, r2, mp, bias)
    return metrics


# ══════════════════════════════════════════════════════════════════════════════
# MODEL TRAINING ROUTINES (8 ARCHITECTURES)
# ══════════════════════════════════════════════════════════════════════════════

def train_linear_regression(X_train: np.ndarray, y_train: np.ndarray) -> LinearRegression:
    m = LinearRegression(**MODEL_CONFIGS["LinearRegression"])
    m.fit(X_train, y_train)
    return m


def train_elastic_net(X_train: np.ndarray, y_train: np.ndarray) -> ElasticNet:
    m = ElasticNet(**MODEL_CONFIGS["ElasticNet"])
    m.fit(X_train, y_train)
    return m


def train_random_forest(X_train: np.ndarray, y_train: np.ndarray) -> RandomForestRegressor:
    m = RandomForestRegressor(**MODEL_CONFIGS["RandomForest"])
    m.fit(X_train, y_train)
    return m


def train_extra_trees(X_train: np.ndarray, y_train: np.ndarray) -> ExtraTreesRegressor:
    m = ExtraTreesRegressor(**MODEL_CONFIGS["ExtraTrees"])
    m.fit(X_train, y_train)
    return m


def train_hist_gb(X_train: np.ndarray, y_train: np.ndarray) -> HistGradientBoostingRegressor:
    m = HistGradientBoostingRegressor(**MODEL_CONFIGS["HistGradientBoosting"])
    m.fit(X_train, y_train)
    return m


def train_xgb(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray) -> xgb.XGBRegressor:
    m = xgb.XGBRegressor(**MODEL_CONFIGS["XGBoost"])
    m.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False,
    )
    return m


def train_lgbm(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray, feature_names: List[str]) -> lgb.Booster:
    ds_train = lgb.Dataset(X_train, label=y_train, feature_name=feature_names)
    ds_val   = lgb.Dataset(X_val, label=y_val, reference=ds_train)
    params = {k: v for k, v in MODEL_CONFIGS["LightGBM"].items() if k != "n_estimators"}
    callbacks = [lgb.early_stopping(50, verbose=False)]
    m = lgb.train(
        params, ds_train,
        num_boost_round=MODEL_CONFIGS["LightGBM"]["n_estimators"],
        valid_sets=[ds_val],
        callbacks=callbacks,
    )
    return m


def train_catboost(X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray) -> CatBoostRegressor:
    m = CatBoostRegressor(**MODEL_CONFIGS["CatBoost"])
    m.fit(
        X_train, y_train,
        eval_set=(X_val, y_val),
        early_stopping_rounds=50,
        verbose=False,
    )
    return m


# ══════════════════════════════════════════════════════════════════════════════
# CHRONOLOGICAL BENCHMARK
# ══════════════════════════════════════════════════════════════════════════════

def run_chronological_benchmark(df: pd.DataFrame) -> Tuple[Dict[str, Any], Any, StandardScaler, str]:
    logger.info("=" * 78)
    logger.info("  BENCHMARKING 8 ALGORITHMS ON CHRONOLOGICAL SPLIT (MODEL 2)")
    logger.info("=" * 78)

    train_df, val_df, test_df = get_chronological_splits(df)

    X_tr_raw = train_df[FEATURE_COLUMNS].values
    y_train  = train_df[TARGET_NAME].values

    X_va_raw = val_df[FEATURE_COLUMNS].values
    y_val    = val_df[TARGET_NAME].values

    X_te_raw = test_df[FEATURE_COLUMNS].values
    y_test   = test_df[TARGET_NAME].values

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_tr_raw)
    X_val   = scaler.transform(X_va_raw)
    X_test  = scaler.transform(X_te_raw)

    benchmark_results = {}
    trained_models = {}

    # 1. Linear Regression
    logger.info("--> 1. Training Linear Regression ...")
    t0 = time.time()
    m_lr = train_linear_regression(X_train, y_train)
    t_lr = time.time() - t0
    trained_models["LinearRegression"] = m_lr
    benchmark_results["LinearRegression"] = {
        "train": calc_metrics("LR-Train", y_train, m_lr.predict(X_train)),
        "val":   calc_metrics("LR-Val",   y_val,   m_lr.predict(X_val)),
        "test":  calc_metrics("LR-Test",  y_test,  m_lr.predict(X_test)),
        "train_time_s": round(t_lr, 2),
    }

    # 2. ElasticNet
    logger.info("--> 2. Training ElasticNet ...")
    t0 = time.time()
    m_en = train_elastic_net(X_train, y_train)
    t_en = time.time() - t0
    trained_models["ElasticNet"] = m_en
    benchmark_results["ElasticNet"] = {
        "train": calc_metrics("ElasticNet-Train", y_train, m_en.predict(X_train)),
        "val":   calc_metrics("ElasticNet-Val",   y_val,   m_en.predict(X_val)),
        "test":  calc_metrics("ElasticNet-Test",  y_test,  m_en.predict(X_test)),
        "train_time_s": round(t_en, 2),
    }

    # 3. Random Forest
    logger.info("--> 3. Training Random Forest Regressor ...")
    t0 = time.time()
    m_rf = train_random_forest(X_train, y_train)
    t_rf = time.time() - t0
    trained_models["RandomForest"] = m_rf
    benchmark_results["RandomForest"] = {
        "train": calc_metrics("RF-Train", y_train, m_rf.predict(X_train)),
        "val":   calc_metrics("RF-Val",   y_val,   m_rf.predict(X_val)),
        "test":  calc_metrics("RF-Test",  y_test,  m_rf.predict(X_test)),
        "train_time_s": round(t_rf, 2),
    }

    # 4. Extra Trees
    logger.info("--> 4. Training Extra Trees Regressor ...")
    t0 = time.time()
    m_et = train_extra_trees(X_train, y_train)
    t_et = time.time() - t0
    trained_models["ExtraTrees"] = m_et
    benchmark_results["ExtraTrees"] = {
        "train": calc_metrics("ET-Train", y_train, m_et.predict(X_train)),
        "val":   calc_metrics("ET-Val",   y_val,   m_et.predict(X_val)),
        "test":  calc_metrics("ET-Test",  y_test,  m_et.predict(X_test)),
        "train_time_s": round(t_et, 2),
    }

    # 5. HistGradientBoosting
    logger.info("--> 5. Training HistGradientBoosting Regressor ...")
    t0 = time.time()
    m_hgb = train_hist_gb(X_train, y_train)
    t_hgb = time.time() - t0
    trained_models["HistGradientBoosting"] = m_hgb
    benchmark_results["HistGradientBoosting"] = {
        "train": calc_metrics("HGB-Train", y_train, m_hgb.predict(X_train)),
        "val":   calc_metrics("HGB-Val",   y_val,   m_hgb.predict(X_val)),
        "test":  calc_metrics("HGB-Test",  y_test,  m_hgb.predict(X_test)),
        "train_time_s": round(t_hgb, 2),
    }

    # 6. XGBoost
    logger.info("--> 6. Training XGBoost Regressor ...")
    t0 = time.time()
    m_xgb = train_xgb(X_train, y_train, X_val, y_val)
    t_xgb = time.time() - t0
    trained_models["XGBoost"] = m_xgb
    benchmark_results["XGBoost"] = {
        "train": calc_metrics("XGB-Train", y_train, m_xgb.predict(X_train)),
        "val":   calc_metrics("XGB-Val",   y_val,   m_xgb.predict(X_val)),
        "test":  calc_metrics("XGB-Test",  y_test,  m_xgb.predict(X_test)),
        "train_time_s": round(t_xgb, 2),
    }

    # 7. LightGBM
    logger.info("--> 7. Training LightGBM Regressor ...")
    t0 = time.time()
    m_lgbm = train_lgbm(X_train, y_train, X_val, y_val, FEATURE_COLUMNS)
    t_lgbm = time.time() - t0
    trained_models["LightGBM"] = m_lgbm
    benchmark_results["LightGBM"] = {
        "train": calc_metrics("LGBM-Train", y_train, m_lgbm.predict(X_train)),
        "val":   calc_metrics("LGBM-Val",   y_val,   m_lgbm.predict(X_val)),
        "test":  calc_metrics("LGBM-Test",  y_test,  m_lgbm.predict(X_test)),
        "train_time_s": round(t_lgbm, 2),
    }

    # 8. CatBoost
    logger.info("--> 8. Training CatBoost Regressor ...")
    t0 = time.time()
    m_cat = train_catboost(X_train, y_train, X_val, y_val)
    t_cat = time.time() - t0
    trained_models["CatBoost"] = m_cat
    benchmark_results["CatBoost"] = {
        "train": calc_metrics("CatBoost-Train", y_train, m_cat.predict(X_train)),
        "val":   calc_metrics("CatBoost-Val",   y_val,   m_cat.predict(X_val)),
        "test":  calc_metrics("CatBoost-Test",  y_test,  m_cat.predict(X_test)),
        "train_time_s": round(t_cat, 2),
    }

    # Selection: strictly best validation RMSE
    winner_name = min(benchmark_results.keys(), key=lambda k: benchmark_results[k]["val"]["rmse"])
    logger.info("=" * 78)
    logger.info("  SCIENTIFIC WINNER SELECTED: %s (Val RMSE = %.4f L, Test R² = %.4f)",
                winner_name, benchmark_results[winner_name]["val"]["rmse"],
                benchmark_results[winner_name]["test"]["r2"])
    logger.info("=" * 78)

    rows = []
    for name, res in benchmark_results.items():
        rows.append({
            "Algorithm": name,
            "Train R²": res["train"]["r2"],
            "Val R²": res["val"]["r2"],
            "Test R²": res["test"]["r2"],
            "Val RMSE (L)": res["val"]["rmse"],
            "Test RMSE (L)": res["test"]["rmse"],
            "Test MAE (L)": res["test"]["mae"],
            "Test MAPE (%)": res["test"]["mape_pct"],
            "Train Time (s)": res["train_time_s"],
        })
    df_cmp = pd.DataFrame(rows).sort_values("Val RMSE (L)")
    df_cmp.to_csv(os.path.join(RESULTS_DIR, "model_benchmark_comparison.csv"), index=False)
    logger.info("\n%s\n", df_cmp.to_string(index=False))

    return benchmark_results, trained_models[winner_name], scaler, winner_name


# ══════════════════════════════════════════════════════════════════════════════
# LEAVE-ONE-SIMULATION-OUT (LOSO) VALIDATION
# ══════════════════════════════════════════════════════════════════════════════

def run_loso_cross_validation(df: pd.DataFrame, winner_name: str) -> Dict[str, Any]:
    logger.info("=" * 78)
    logger.info("  LEAVE-ONE-SIMULATION-OUT (LOSO) 5-FOLD CROSS-VALIDATION (MODEL 2)")
    logger.info("=" * 78)

    hashes = verify_simulation_hashes()
    folds = get_loso_splits(df)
    fold_metrics = []

    for train_k, test_k, k in folds:
        logger.info("--> LOSO Fold %d: Training on Runs != %d, Testing on Run == %d ...", k, k, k)

        train_sub = train_k[train_k["year"] <= 2019]
        val_sub   = train_k[train_k["year"] >= 2020]

        X_tr = train_sub[FEATURE_COLUMNS].values
        y_tr = train_sub[TARGET_NAME].values

        X_va = val_sub[FEATURE_COLUMNS].values
        y_va = val_sub[TARGET_NAME].values

        X_te = test_k[FEATURE_COLUMNS].values
        y_te = test_k[TARGET_NAME].values

        scaler_k = StandardScaler()
        X_tr_s = scaler_k.fit_transform(X_tr)
        X_va_s = scaler_k.transform(X_va)
        X_te_s = scaler_k.transform(X_te)

        if winner_name == "CatBoost":
            m_k = train_catboost(X_tr_s, y_tr, X_va_s, y_va)
        elif winner_name == "LightGBM":
            m_k = train_lgbm(X_tr_s, y_tr, X_va_s, y_va, FEATURE_COLUMNS)
        elif winner_name == "XGBoost":
            m_k = train_xgb(X_tr_s, y_tr, X_va_s, y_va)
        elif winner_name == "RandomForest":
            m_k = train_random_forest(X_tr_s, y_tr)
        elif winner_name == "ExtraTrees":
            m_k = train_extra_trees(X_tr_s, y_tr)
        elif winner_name == "HistGradientBoosting":
            m_k = train_hist_gb(X_tr_s, y_tr)
        elif winner_name == "ElasticNet":
            m_k = train_elastic_net(X_tr_s, y_tr)
        else:
            m_k = train_linear_regression(X_tr_s, y_tr)

        y_pred_k = m_k.predict(X_te_s)
        res_k = calc_metrics(f"LOSO-Fold-{k}", y_te, y_pred_k)
        res_k["fold"] = k
        res_k["test_samples"] = len(test_k)
        res_k["sha256"] = hashes[k]["sha256"][:16]
        res_k["is_duplicate_run"] = (k in [4, 5])
        fold_metrics.append(res_k)

    df_loso = pd.DataFrame(fold_metrics)
    df_loso.to_csv(os.path.join(RESULTS_DIR, "loso_cv_metrics.csv"), index=False)

    summary_all = {
        "r2_mean": float(df_loso["r2"].mean()),
        "r2_std": float(df_loso["r2"].std()),
        "rmse_mean": float(df_loso["rmse"].mean()),
        "rmse_std": float(df_loso["rmse"].std()),
        "mae_mean": float(df_loso["mae"].mean()),
        "mae_std": float(df_loso["mae"].std()),
        "mape_mean": float(df_loso["mape_pct"].mean()),
        "mape_std": float(df_loso["mape_pct"].std()),
    }

    df_dedup = df_loso[~df_loso["is_duplicate_run"]]
    summary_dedup = {
        "r2_mean": float(df_dedup["r2"].mean()),
        "r2_std": float(df_dedup["r2"].std()),
        "rmse_mean": float(df_dedup["rmse"].mean()),
        "rmse_std": float(df_dedup["rmse"].std()),
        "mae_mean": float(df_dedup["mae"].mean()),
        "mae_std": float(df_dedup["mae"].std()),
        "mape_mean": float(df_dedup["mape_pct"].mean()),
        "mape_std": float(df_dedup["mape_pct"].std()),
    }

    loso_final = {
        "all_5_folds_summary": summary_all,
        "deduplicated_3_folds_summary": summary_dedup,
        "duplicate_warning": "Runs 3, 4, and 5 share identical SHA-256 hashes (13cff3e1...). Naive 5-fold LOSO is optimistic. Deduplicated 3-fold reflects true independent simulation variation.",
        "folds": fold_metrics,
    }

    logger.info("=" * 78)
    logger.info("  LOSO 5-FOLD ALL SUMMARY:         RMSE = %.3f ± %.3f L | R² = %.4f ± %.4f",
                summary_all["rmse_mean"], summary_all["rmse_std"], summary_all["r2_mean"], summary_all["r2_std"])
    logger.info("  LOSO DEDUPLICATED (RUNS 1–3):    RMSE = %.3f ± %.3f L | R² = %.4f ± %.4f",
                summary_dedup["rmse_mean"], summary_dedup["rmse_std"], summary_dedup["r2_mean"], summary_dedup["r2_std"])
    logger.info("=" * 78)

    with open(os.path.join(RESULTS_DIR, "loso_summary.json"), "w") as f:
        json.dump(loso_final, f, indent=2)

    return loso_final


def main():
    logger.info("Starting Model 2 (Fuel Consumption Forecast V3) training pipeline ...")
    verify_simulation_hashes()
    df_raw = load_raw_corpus()
    df_clean = build_day_ahead_fuel_dataset(df_raw)

    cache_path = os.path.join(RESULTS_DIR, "_day_ahead_corpus.pkl")
    with open(cache_path, "wb") as f:
        pickle.dump(df_clean, f, protocol=4)
    logger.info("Saved cached dataset to: %s", cache_path)

    benchmarks, best_model, scaler, winner_name = run_chronological_benchmark(df_clean)

    # Save best model artifacts
    model_file = os.path.join(MODELS_DIR, "best_model_fuel_v3.pkl")
    scaler_file = os.path.join(MODELS_DIR, "scaler_fuel_v3.pkl")
    feats_file = os.path.join(MODELS_DIR, "features_fuel_v3.json")
    metrics_file = os.path.join(RESULTS_DIR, "chronological_metrics_v3.json")

    with open(model_file, "wb") as f: pickle.dump(best_model, f)
    with open(scaler_file, "wb") as f: pickle.dump(scaler, f)
    with open(feats_file, "w") as f: json.dump(FEATURE_COLUMNS, f, indent=2)
    with open(metrics_file, "w") as f: json.dump(benchmarks, f, indent=2)

    with open(os.path.join(RESULTS_DIR, "winner_name.txt"), "w") as f:
        f.write(winner_name)

    loso_results = run_loso_cross_validation(df_clean, winner_name)
    logger.info("Model 2 V3 training and selection completed successfully.")


if __name__ == "__main__":
    main()
