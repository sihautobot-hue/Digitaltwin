"""
train_models.py
---------------
Multi-algorithm benchmark training pipeline for Model 3 Version 3.
Selects the winning algorithm EXCLUSIVELY via Validation RMSE.
Performs Leave-One-Simulation-Out (LOSO) cross-validation on all 5 runs
and also on the 3 deduplicated runs (1, 2, 3).
"""

import json
import logging
import os
import pickle
import warnings
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, ElasticNet
from sklearn.ensemble import (
    RandomForestRegressor,
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
)
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("TrainModels-Model3-V3")

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
    logger.warning("XGBoost not installed — skipping.")

try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:
    HAS_LGB = False
    logger.warning("LightGBM not installed — skipping.")

try:
    from catboost import CatBoostRegressor
    HAS_CAT = True
except ImportError:
    HAS_CAT = False
    logger.warning("CatBoost not installed — skipping.")

from config import FEATURE_COLUMNS, MODEL_CONFIGS, MODELS_DIR, RESULTS_DIR, RANDOM_SEED, TARGET_NAME
from feature_engineering import (
    verify_simulation_hashes,
    load_raw_corpus,
    build_fuel_runway_dataset,
    get_chronological_splits,
    get_loso_splits,
)


def mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true > 0.5
    if mask.sum() == 0:
        return np.nan
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def evaluate_split(name: str, y_true: np.ndarray, y_pred: np.ndarray) -> Dict:
    mae  = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2   = r2_score(y_true, y_pred)
    mp   = mape(y_true, y_pred)
    logger.info("[%s] MAE=%.2fd RMSE=%.2fd R²=%.4f MAPE=%.2f%%", name, mae, rmse, r2, mp)
    return {"mae": round(mae, 4), "rmse": round(rmse, 4), "r2": round(r2, 6), "mape_pct": round(mp, 3)}


def get_safe_features(df: pd.DataFrame) -> List[str]:
    return [f for f in FEATURE_COLUMNS if f in df.columns]


def prep_xy(df: pd.DataFrame, feat_cols: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    X = df[feat_cols].copy()
    for c in X.select_dtypes("bool"):
        X[c] = X[c].astype(int)
    X = X.fillna(0.0)
    y = df[TARGET_NAME].values
    return X.values, y


def build_algorithm(name: str) -> object:
    cfg = MODEL_CONFIGS.get(name, {})
    if name == "LinearRegression":
        return LinearRegression()
    elif name == "ElasticNet":
        return ElasticNet(**cfg)
    elif name == "RandomForest":
        return RandomForestRegressor(**cfg)
    elif name == "ExtraTrees":
        return ExtraTreesRegressor(**cfg)
    elif name == "HistGradientBoosting":
        return HistGradientBoostingRegressor(**cfg)
    elif name == "XGBoost" and HAS_XGB:
        return xgb.XGBRegressor(**cfg)
    elif name == "LightGBM" and HAS_LGB:
        return lgb.LGBMRegressor(**cfg)
    elif name == "CatBoost" and HAS_CAT:
        return CatBoostRegressor(**cfg)
    else:
        return None


def train_and_benchmark(
    df: pd.DataFrame,
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> Tuple[str, object, StandardScaler, List[str], Dict]:
    """
    Train all 8 algorithms. Select winner by VALIDATION RMSE only.
    Returns (winning_name, fitted_model, scaler, feature_columns, all_metrics).
    """
    feat_cols = get_safe_features(train_df)
    logger.info("Benchmarking %d algorithms over %d features ...", len(MODEL_CONFIGS), len(feat_cols))

    scaler = StandardScaler()
    X_tr, y_tr = prep_xy(train_df, feat_cols)
    X_va, y_va = prep_xy(val_df,   feat_cols)
    X_te, y_te = prep_xy(test_df,  feat_cols)

    X_tr_s = scaler.fit_transform(X_tr)
    X_va_s = scaler.transform(X_va)
    X_te_s = scaler.transform(X_te)

    benchmark_results: Dict[str, Dict] = {}
    val_rmse_map: Dict[str, float] = {}

    candidate_names = [
        "LinearRegression", "ElasticNet", "RandomForest", "ExtraTrees",
        "HistGradientBoosting", "XGBoost", "LightGBM", "CatBoost",
    ]

    for alg_name in candidate_names:
        algo = build_algorithm(alg_name)
        if algo is None:
            logger.info("Skipping %s (not installed or disabled).", alg_name)
            continue

        logger.info("Training %s ...", alg_name)
        try:
            algo.fit(X_tr_s, y_tr)
            m = {
                "train": evaluate_split(f"{alg_name}:TRAIN", y_tr, algo.predict(X_tr_s)),
                "val":   evaluate_split(f"{alg_name}:VAL",   y_va, algo.predict(X_va_s)),
                "test":  evaluate_split(f"{alg_name}:TEST",  y_te, algo.predict(X_te_s)),
            }
            benchmark_results[alg_name] = m
            val_rmse_map[alg_name] = m["val"]["rmse"]
        except Exception as e:
            logger.warning("Algorithm %s failed: %s", alg_name, str(e))

    if not val_rmse_map:
        raise RuntimeError("No algorithms trained successfully.")

    # Winner selected by VALIDATION RMSE only
    winner = min(val_rmse_map, key=val_rmse_map.get)
    logger.info("=" * 60)
    logger.info("BENCHMARK WINNER: %s (Val RMSE=%.4f days)", winner, val_rmse_map[winner])
    logger.info("=" * 60)

    # Retrain winner on Train+Val for final test evaluation
    train_val_df = pd.concat([train_df, val_df], ignore_index=True)
    X_tv, y_tv = prep_xy(train_val_df, feat_cols)
    scaler_final = StandardScaler()
    X_tv_s = scaler_final.fit_transform(X_tv)
    X_te_s_final = scaler_final.transform(X_te)

    final_model = build_algorithm(winner)
    final_model.fit(X_tv_s, y_tv)
    final_test_metrics = evaluate_split("FINAL:TEST", y_te, final_model.predict(X_te_s_final))

    benchmark_summary = {
        "benchmark": benchmark_results,
        "winner": winner,
        "winner_val_rmse": val_rmse_map[winner],
        "final_test": final_test_metrics,
        "num_features": len(feat_cols),
        "val_rmse_ranking": sorted(val_rmse_map.items(), key=lambda x: x[1]),
    }

    logger.info("Final Test: MAE=%.2fd RMSE=%.2fd R²=%.4f MAPE=%.2f%%",
                final_test_metrics["mae"], final_test_metrics["rmse"],
                final_test_metrics["r2"], final_test_metrics["mape_pct"])

    return winner, final_model, scaler_final, feat_cols, benchmark_summary


def loso_cross_validation(df: pd.DataFrame, winner_name: str) -> Dict:
    """
    Leave-One-Simulation-Out cross-validation.
    Reports both all-5-fold and deduplicated (Runs 1, 2, 3) results.
    """
    logger.info("Running LOSO cross-validation with %s ...", winner_name)
    feat_cols = get_safe_features(df)
    splits = get_loso_splits(df)

    all_fold_results = []
    for train_loso, val_loso, fold_id in splits:
        X_tr, y_tr = prep_xy(train_loso, feat_cols)
        X_va, y_va = prep_xy(val_loso,   feat_cols)
        sc = StandardScaler()
        X_tr_s = sc.fit_transform(X_tr)
        X_va_s = sc.transform(X_va)
        m = build_algorithm(winner_name)
        m.fit(X_tr_s, y_tr)
        preds = m.predict(X_va_s)
        metrics = evaluate_split(f"LOSO Fold {fold_id}", y_va, preds)
        metrics["fold_id"] = fold_id
        all_fold_results.append(metrics)

    # All 5 folds
    rmse_all = [r["rmse"] for r in all_fold_results]
    mae_all  = [r["mae"]  for r in all_fold_results]
    r2_all   = [r["r2"]   for r in all_fold_results]

    # Deduplicated: runs 1, 2, 3 only (runs 4 and 5 are bitwise duplicates of run 3)
    dedup_folds = [r for r in all_fold_results if r["fold_id"] in [1, 2, 3]]
    rmse_dd = [r["rmse"] for r in dedup_folds]
    mae_dd  = [r["mae"]  for r in dedup_folds]
    r2_dd   = [r["r2"]   for r in dedup_folds]

    loso_summary = {
        "all_folds_5": {
            "per_fold": all_fold_results,
            "mean_rmse": round(np.mean(rmse_all), 4),
            "std_rmse":  round(np.std(rmse_all), 4),
            "mean_mae":  round(np.mean(mae_all), 4),
            "std_mae":   round(np.std(mae_all), 4),
            "mean_r2":   round(np.mean(r2_all), 6),
            "std_r2":    round(np.std(r2_all), 6),
        },
        "deduplicated_3": {
            "per_fold": dedup_folds,
            "mean_rmse": round(np.mean(rmse_dd), 4),
            "std_rmse":  round(np.std(rmse_dd), 4),
            "mean_mae":  round(np.mean(mae_dd), 4),
            "std_mae":   round(np.std(mae_dd), 4),
            "mean_r2":   round(np.mean(r2_dd), 6),
            "std_r2":    round(np.std(r2_dd), 6),
        },
        "integrity_note": (
            "Runs 4 and 5 are bitwise duplicates of Run 3 (verified via SHA-256). "
            "The 5-fold result is optimistic. The 3-fold deduplicated result is the "
            "scientifically defensible baseline for publication."
        ),
    }

    logger.info("LOSO All-5:   RMSE=%.4f ± %.4f days", loso_summary["all_folds_5"]["mean_rmse"], loso_summary["all_folds_5"]["std_rmse"])
    logger.info("LOSO Dedup-3: RMSE=%.4f ± %.4f days", loso_summary["deduplicated_3"]["mean_rmse"], loso_summary["deduplicated_3"]["std_rmse"])
    return loso_summary


def get_feature_importance(model, feat_cols: List[str], winner_name: str) -> pd.DataFrame:
    """Extract feature importances from the winning model."""
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "coef_"):
        importances = np.abs(model.coef_)
    else:
        importances = np.zeros(len(feat_cols))

    fi = pd.DataFrame({"feature": feat_cols, "importance": importances})
    fi = fi.sort_values("importance", ascending=False).reset_index(drop=True)
    fi["importance_pct"] = (fi["importance"] / fi["importance"].sum() * 100).round(2)
    return fi


def save_artifacts(
    winner: str,
    model,
    scaler: StandardScaler,
    feat_cols: List[str],
    benchmark_summary: Dict,
    loso_summary: Dict,
    fi_df: pd.DataFrame,
) -> None:
    """Persist all training artifacts to disk."""
    # Models
    with open(os.path.join(MODELS_DIR, "best_model_v3.pkl"), "wb") as f:
        pickle.dump(model, f)
    with open(os.path.join(MODELS_DIR, "scaler_v3.pkl"), "wb") as f:
        pickle.dump(scaler, f)
    with open(os.path.join(MODELS_DIR, "feature_columns_v3.json"), "w") as f:
        json.dump(feat_cols, f, indent=2)

    # Results
    full_results = {
        "model_version": "v3",
        "target": TARGET_NAME,
        "winner": winner,
        "benchmark": benchmark_summary,
        "loso": loso_summary,
    }
    with open(os.path.join(RESULTS_DIR, "benchmark_results_v3.json"), "w") as f:
        json.dump(full_results, f, indent=2)

    fi_df.to_csv(os.path.join(RESULTS_DIR, "feature_importance_v3.csv"), index=False)
    logger.info("All artifacts saved to %s and %s", MODELS_DIR, RESULTS_DIR)


def run():
    hash_report = verify_simulation_hashes()
    df_raw = load_raw_corpus()
    df = build_fuel_runway_dataset(df_raw)
    df["year"] = pd.to_datetime(df["date"]).dt.year

    from feature_engineering import get_chronological_splits
    train_df, val_df, test_df = get_chronological_splits(df)

    winner, model, scaler, feat_cols, benchmark_summary = train_and_benchmark(
        df, train_df, val_df, test_df
    )
    loso_summary = loso_cross_validation(df, winner)
    fi_df = get_feature_importance(model, feat_cols, winner)

    logger.info("Top 15 Features:\n%s", fi_df.head(15).to_string(index=False))
    save_artifacts(winner, model, scaler, feat_cols, benchmark_summary, loso_summary, fi_df)
    return winner, model, scaler, feat_cols, benchmark_summary, loso_summary, fi_df, df, train_df, val_df, test_df


if __name__ == "__main__":
    run()
