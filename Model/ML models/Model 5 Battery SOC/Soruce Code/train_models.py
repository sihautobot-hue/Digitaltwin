"""
train_models.py
---------------
Steps 5 & 6: Multi-Algorithm Benchmarking, Model Selection (Validation-only),
Leave-One-Simulation-Out (LOSO) Cross-Validation, and Model Persistence.
Model 5 (Version 3): Day-Ahead Battery State of Charge Forecasting

Algorithms Trained:
  1. XGBoost (xgboost.XGBRegressor)
  2. LightGBM (lightgbm.LGBMRegressor)
  3. Random Forest (sklearn.ensemble.RandomForestRegressor)
  4. CatBoost (catboost.CatBoostRegressor)
"""

import os
import json
import time
import pickle
import logging
from typing import Dict, Any, Tuple, List

import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import RandomForestRegressor
import catboost as cb

from config import (
    MODELS_DIR,
    RESULTS_DIR,
    FEATURE_COLUMNS,
    TARGET_FORECAST,
    MODEL_CONFIGS,
    RANDOM_SEED,
)
from feature_engineering import (
    load_raw_simulation_runs,
    construct_day_ahead_dataset,
    get_chronological_splits,
    get_loso_folds,
    compute_simulation_hashes,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("TrainModels-M5V3")


def calc_mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate Mean Absolute Percentage Error (MAPE) avoiding zero division."""
    denom = np.maximum(np.abs(y_true), 1.0)
    return float(np.mean(np.abs((y_true - y_pred) / denom)) * 100.0)


def instantiate_models() -> Dict[str, Any]:
    """Instantiate the 4 specified algorithm regressors."""
    return {
        "XGBoost": xgb.XGBRegressor(**MODEL_CONFIGS["XGBoost"]),
        "LightGBM": lgb.LGBMRegressor(**MODEL_CONFIGS["LightGBM"]),
        "Random Forest": RandomForestRegressor(**MODEL_CONFIGS["Random Forest"]),
        "CatBoost": cb.CatBoostRegressor(**MODEL_CONFIGS["CatBoost"]),
    }


def benchmark_models(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame
) -> Tuple[pd.DataFrame, str, Any, Dict[str, Any]]:
    """
    Train all 4 models on 2003-2019, evaluate strictly on 2020-2021 validation set.
    Select the single winning model based solely on Validation RMSE.
    """
    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET_FORECAST]

    X_val = val_df[FEATURE_COLUMNS]
    y_val = val_df[TARGET_FORECAST]

    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_FORECAST]

    models = instantiate_models()
    benchmark_records = []
    trained_models = {}

    print("\n" + "=" * 80)
    print("STEP 5: MULTI-ALGORITHM BENCHMARKING (VALIDATION SET SELECTION ONLY)")
    print("=" * 80)

    for name, model in models.items():
        logger.info("Training algorithm: %s ...", name)
        t0 = time.time()
        model.fit(X_train, y_train)
        elapsed = time.time() - t0

        # Predict
        p_train = model.predict(X_train)
        p_val = model.predict(X_val)
        p_test = model.predict(X_test)

        train_r2 = r2_score(y_train, p_train)
        val_r2 = r2_score(y_val, p_val)
        test_r2 = r2_score(y_test, p_test)

        val_rmse = np.sqrt(mean_squared_error(y_val, p_val))
        test_rmse = np.sqrt(mean_squared_error(y_test, p_test))

        val_mae = mean_absolute_error(y_val, p_val)
        test_mae = mean_absolute_error(y_test, p_test)

        val_mape = calc_mape(y_val.values, p_val)
        test_mape = calc_mape(y_test.values, p_test)

        trained_models[name] = model

        record = {
            "Algorithm": name,
            "Train R2": round(train_r2, 4),
            "Val R2 (2020-21)": round(val_r2, 4),
            "Test R2 (2022)": round(test_r2, 4),
            "Val RMSE (%)": round(val_rmse, 4),
            "Test RMSE (%)": round(test_rmse, 4),
            "Val MAE (%)": round(val_mae, 4),
            "Test MAE (%)": round(test_mae, 4),
            "Val MAPE (%)": round(val_mape, 3),
            "Test MAPE (%)": round(test_mape, 3),
            "Train Time (s)": round(elapsed, 2),
        }
        benchmark_records.append(record)
        logger.info(
            "%s -> Val RMSE: %.4f%% | Val R2: %.4f | Val MAE: %.4f%% (%.2fs)",
            name, val_rmse, val_r2, val_mae, elapsed
        )

    bdf = pd.DataFrame(benchmark_records)
    # Sort strictly by Validation RMSE
    bdf = bdf.sort_values("Val RMSE (%)").reset_index(drop=True)
    winner_name = bdf.iloc[0]["Algorithm"]

    print("\nBENCHMARK RESULTS TABLE:")
    print(bdf.to_string(index=False))
    print(f"\n[WINNER SELECTION] Final Selected Model: {winner_name} (Lowest Validation RMSE: {bdf.iloc[0]['Val RMSE (%)']}%)")
    print("=" * 80 + "\n")

    return bdf, winner_name, trained_models[winner_name], trained_models


def perform_loso_validation(df: pd.DataFrame, winner_name: str) -> Dict[str, Any]:
    """
    Perform 5-fold Leave-One-Simulation-Out (LOSO) cross-validation using the winning model.
    Disclose bitwise duplicate simulation runs in the report.
    """
    print("=" * 80)
    print("STEP 6: LEAVE-ONE-SIMULATION-OUT (LOSO) CROSS-VALIDATION")
    print("=" * 80)

    folds = get_loso_folds(df)
    fold_results = []

    for test_run, train_fold, test_fold in folds:
        logger.info("Executing LOSO Fold: Hold-out Simulation Run %d ...", test_run)
        
        # Instantiate fresh winner model
        models = instantiate_models()
        model = models[winner_name]

        X_tr = train_fold[FEATURE_COLUMNS]
        y_tr = train_fold[TARGET_FORECAST]
        X_ts = test_fold[FEATURE_COLUMNS]
        y_ts = test_fold[TARGET_FORECAST]

        model.fit(X_tr, y_tr)
        preds = model.predict(X_ts)

        rmse = np.sqrt(mean_squared_error(y_ts, preds))
        mae = mean_absolute_error(y_ts, preds)
        mape = calc_mape(y_ts.values, preds)
        r2 = r2_score(y_ts, preds)

        fold_res = {
            "Test Run": test_run,
            "RMSE (%)": round(rmse, 4),
            "MAE (%)": round(mae, 4),
            "MAPE (%)": round(mape, 3),
            "R2": round(r2, 4),
            "Is Duplicate": "Bitwise Duplicate of Run 3" if test_run in [4, 5] else "Unique Simulation",
        }
        fold_results.append(fold_res)
        logger.info("  Run %d -> RMSE: %.4f%% | MAE: %.4f%% | R2: %.4f (%s)", test_run, rmse, mae, r2, fold_res["Is Duplicate"])

    fold_df = pd.DataFrame(fold_results)
    print("\nLOSO FOLD RESULTS:")
    print(fold_df.to_string(index=False))

    all_rmse = [f["RMSE (%)"] for f in fold_results]
    all_r2 = [f["R2"] for f in fold_results]

    dedup_results = [f for f in fold_results if f["Test Run"] in [1, 2, 3]]
    dedup_rmse = [f["RMSE (%)"] for f in dedup_results]
    dedup_r2 = [f["R2"] for f in dedup_results]

    summary = {
        "folds": fold_results,
        "all_5_folds": {
            "rmse_mean": round(float(np.mean(all_rmse)), 4),
            "rmse_std": round(float(np.std(all_rmse)), 4),
            "r2_mean": round(float(np.mean(all_r2)), 4),
            "r2_std": round(float(np.std(all_r2)), 4),
        },
        "deduplicated_runs_1_3": {
            "rmse_mean": round(float(np.mean(dedup_rmse)), 4),
            "rmse_std": round(float(np.std(dedup_rmse)), 4),
            "r2_mean": round(float(np.mean(dedup_r2)), 4),
            "r2_std": round(float(np.std(dedup_r2)), 4),
        },
    }

    print("\nLOSO SUMMARY:")
    print(f"  All 5 Folds Mean RMSE: {summary['all_5_folds']['rmse_mean']}% (+/- {summary['all_5_folds']['rmse_std']}%) | R2: {summary['all_5_folds']['r2_mean']}")
    print(f"  Deduplicated (Runs 1-3) Mean RMSE: {summary['deduplicated_runs_1_3']['rmse_mean']}% (+/- {summary['deduplicated_runs_1_3']['rmse_std']}%) | R2: {summary['deduplicated_runs_1_3']['r2_mean']}")
    print("=" * 80 + "\n")
    return summary


def train_and_save_final_model(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    winner_name: str
) -> Tuple[Any, np.ndarray, np.ndarray]:
    """
    Train final model on Train (2003-2019) or Train+Val, evaluate on holdout Test (2022).
    Saves model pickle and feature schema.
    """
    # For holdout evaluation consistency, model trained on Train (2003-2019)
    models = instantiate_models()
    final_model = models[winner_name]

    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df[TARGET_FORECAST]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df[TARGET_FORECAST]

    logger.info("Fitting final %s model on Train split ...", winner_name)
    final_model.fit(X_train, y_train)

    test_preds = final_model.predict(X_test)
    y_test_arr = y_test.values

    # Save model artifact
    model_path = os.path.join(MODELS_DIR, "best_model_battery_soc_v3.pkl")
    with open(model_path, "wb") as fp:
        pickle.dump(final_model, fp)
    logger.info("Saved best model to %s", model_path)

    # Save feature schema
    schema_path = os.path.join(MODELS_DIR, "features_battery_soc_v3.json")
    with open(schema_path, "w") as fp:
        json.dump(FEATURE_COLUMNS, fp, indent=2)
    logger.info("Saved feature schema (%d features) to %s", len(FEATURE_COLUMNS), schema_path)

    return final_model, test_preds, y_test_arr


if __name__ == "__main__":
    compute_simulation_hashes()
    raw = load_raw_simulation_runs()
    ds = construct_day_ahead_dataset(raw)
    train_df, val_df, test_df = get_chronological_splits(ds)

    bdf, winner_name, winner_model, all_trained = benchmark_models(train_df, val_df, test_df)
    loso_summary = perform_loso_validation(ds, winner_name)
    final_model, test_preds, y_test_arr = train_and_save_final_model(train_df, val_df, test_df, winner_name)
