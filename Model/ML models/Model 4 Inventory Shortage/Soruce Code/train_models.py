# train_models.py
# Multi-algorithm benchmark training pipeline for Model 4 Version 3.
# Selects winning model EXCLUSIVELY via Validation ROC-AUC & F1 Score.
# Performs Leave-One-Simulation-Out (LOSO) cross-validation on all 5 runs and 3 deduplicated runs.

import os
import json
import logging
import pickle
import warnings
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, brier_score_loss,
    confusion_matrix
)
from sklearn.ensemble import RandomForestClassifier

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("TrainModels-Model4-V3")

import xgboost as xgb
import lightgbm as lgb
from catboost import CatBoostClassifier

from config import (
    FEATURE_COLUMNS,
    MODEL_CONFIGS,
    MODELS_DIR,
    RESULTS_DIR,
    RANDOM_SEED,
    TARGET_NAME,
)
from feature_engineering import (
    verify_simulation_hashes,
    load_raw_corpus,
    get_chronological_splits,
    get_loso_splits,
)


def evaluate_clf(name: str, y_true: np.ndarray, y_pred_proba: np.ndarray, threshold: float = 0.5) -> Dict:
    y_pred = (y_pred_proba >= threshold).astype(int)
    acc = accuracy_score(y_true, y_pred)
    p   = precision_score(y_true, y_pred, zero_division=0)
    r   = recall_score(y_true, y_pred, zero_division=0)
    f1  = f1_score(y_true, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_pred_proba) if len(np.unique(y_true)) > 1 else 0.5
    except Exception:
        auc = 0.5
    try:
        pr_auc = average_precision_score(y_true, y_pred_proba) if len(np.unique(y_true)) > 1 else float(np.mean(y_true))
    except Exception:
        pr_auc = float(np.mean(y_true))
    brier = brier_score_loss(y_true, y_pred_proba)

    logger.info(
        "[%s] Acc=%.4f  Prec=%.4f  Rec=%.4f  F1=%.4f  ROC-AUC=%.4f  PR-AUC=%.4f  Brier=%.4f",
        name, acc, p, r, f1, auc, pr_auc, brier
    )
    return {
        "accuracy": round(acc, 4),
        "precision": round(p, 4),
        "recall": round(r, 4),
        "f1": round(f1, 4),
        "roc_auc": round(auc, 4),
        "pr_auc": round(pr_auc, 4),
        "brier_score": round(brier, 4),
    }


def get_safe_features(df: pd.DataFrame) -> List[str]:
    return [f for f in FEATURE_COLUMNS if f in df.columns]


def prep_xy(df: pd.DataFrame, feat_cols: List[str]) -> Tuple[np.ndarray, np.ndarray]:
    X = df[feat_cols].copy()
    for c in X.select_dtypes("bool"):
        X[c] = X[c].astype(int)
    X = X.fillna(0.0)
    y = df[TARGET_NAME].values.astype(int)
    return X.values, y


def build_algorithm(name: str) -> object:
    cfg = MODEL_CONFIGS.get(name, {})
    if name == "XGBoost":
        return xgb.XGBClassifier(**cfg)
    elif name == "LightGBM":
        return lgb.LGBMClassifier(**cfg)
    elif name == "RandomForest":
        return RandomForestClassifier(**cfg)
    elif name == "CatBoost":
        return CatBoostClassifier(**cfg)
    else:
        raise ValueError(f"Unknown algorithm: {name}")


def fit_model(algo_name: str, model: object, X_tr: np.ndarray, y_tr: np.ndarray,
              X_va: np.ndarray, y_va: np.ndarray) -> object:
    if algo_name == "XGBoost":
        model.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], verbose=False)
    elif algo_name == "LightGBM":
        model.fit(X_tr, y_tr, eval_set=[(X_va, y_va)],
                  callbacks=[lgb.early_stopping(stopping_rounds=50, verbose=False)])
    elif algo_name == "CatBoost":
        model.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], early_stopping_rounds=50, verbose=False)
    elif algo_name == "RandomForest":
        model.fit(X_tr, y_tr)
    return model


def predict_proba_safe(model: object, X: np.ndarray) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        probs = model.predict_proba(X)
        if probs.ndim == 2 and probs.shape[1] >= 2:
            return probs[:, 1]
        elif probs.ndim == 2:
            return probs[:, 0]
        return probs.ravel()
    elif hasattr(model, "decision_function"):
        df = model.decision_function(X)
        return 1.0 / (1.0 + np.exp(-df))
    else:
        preds = model.predict(X)
        return np.clip(preds.astype(float), 0.0, 1.0)


def run_loso_cross_validation(df: pd.DataFrame, winning_algo: str, feat_cols: List[str]) -> Dict:
    logger.info("=" * 60)
    logger.info("RUNNING LEAVE-ONE-SIMULATION-OUT (LOSO) CROSS-VALIDATION (%s)", winning_algo)
    logger.info("=" * 60)

    # 1. 5-Fold LOSO
    splits_5 = get_loso_splits(df, runs=[1, 2, 3, 4, 5])
    results_5 = []
    for tr, ho, run_id in splits_5:
        X_tr, y_tr = prep_xy(tr, feat_cols)
        X_ho, y_ho = prep_xy(ho, feat_cols)
        scaler = StandardScaler()
        X_tr_s = scaler.fit_transform(X_tr)
        X_ho_s = scaler.transform(X_ho)

        mdl = build_algorithm(winning_algo)
        fit_model(winning_algo, mdl, X_tr_s, y_tr, X_ho_s, y_ho)
        p_ho = predict_proba_safe(mdl, X_ho_s)
        metrics = evaluate_clf(f"LOSO Run-{run_id}", y_ho, p_ho)
        metrics["held_out_run"] = run_id
        results_5.append(metrics)

    # 2. 3-Fold Deduplicated LOSO (Runs 1, 2, 3 only)
    dedup_df = df[df["sim_run_id"].isin([1, 2, 3])].copy()
    splits_3 = get_loso_splits(dedup_df, runs=[1, 2, 3])
    results_3 = []
    for tr, ho, run_id in splits_3:
        X_tr, y_tr = prep_xy(tr, feat_cols)
        X_ho, y_ho = prep_xy(ho, feat_cols)
        scaler = StandardScaler()
        X_tr_s = scaler.fit_transform(X_tr)
        X_ho_s = scaler.transform(X_ho)

        mdl = build_algorithm(winning_algo)
        fit_model(winning_algo, mdl, X_tr_s, y_tr, X_ho_s, y_ho)
        p_ho = predict_proba_safe(mdl, X_ho_s)
        metrics = evaluate_clf(f"LOSO Dedup Run-{run_id}", y_ho, p_ho)
        metrics["held_out_run"] = run_id
        results_3.append(metrics)

    summary = {
        "loso_5fold": {
            "folds": results_5,
            "mean_roc_auc": round(float(np.mean([r["roc_auc"] for r in results_5])), 4),
            "std_roc_auc":  round(float(np.std([r["roc_auc"] for r in results_5])), 4),
            "mean_f1":      round(float(np.mean([r["f1"] for r in results_5])), 4),
            "mean_accuracy":round(float(np.mean([r["accuracy"] for r in results_5])), 4),
        },
        "loso_3fold_deduplicated": {
            "folds": results_3,
            "mean_roc_auc": round(float(np.mean([r["roc_auc"] for r in results_3])), 4),
            "std_roc_auc":  round(float(np.std([r["roc_auc"] for r in results_3])), 4),
            "mean_f1":      round(float(np.mean([r["f1"] for r in results_3])), 4),
            "mean_accuracy":round(float(np.mean([r["accuracy"] for r in results_3])), 4),
        },
    }
    return summary


def run_benchmark():
    logger.info("=" * 60)
    logger.info("MODEL 4 V3: 4-ALGORITHM BENCHMARK (XGBoost, LightGBM, RF, CatBoost)")
    logger.info("=" * 60)

    hashes = verify_simulation_hashes()
    corpus = load_raw_corpus(deduplicate=False)
    feat_cols = get_safe_features(corpus)
    logger.info("Safe Forecast Feature Count: %d", len(feat_cols))

    train_df, val_df, test_df = get_chronological_splits(corpus)
    X_tr, y_tr = prep_xy(train_df, feat_cols)
    X_va, y_va = prep_xy(val_df, feat_cols)
    X_te, y_te = prep_xy(test_df, feat_cols)

    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_va_s = scaler.transform(X_va)
    X_te_s = scaler.transform(X_te)

    algorithms = ["XGBoost", "LightGBM", "RandomForest", "CatBoost"]
    benchmark_results = {}
    trained_models = {}

    for algo in algorithms:
        logger.info("-" * 40)
        logger.info("Training algorithm: %s ...", algo)
        model = build_algorithm(algo)
        model = fit_model(algo, model, X_tr_s, y_tr, X_va_s, y_va)

        p_tr = predict_proba_safe(model, X_tr_s)
        p_va = predict_proba_safe(model, X_va_s)
        p_te = predict_proba_safe(model, X_te_s)

        res_tr = evaluate_clf(f"{algo} [TRAIN]", y_tr, p_tr)
        res_va = evaluate_clf(f"{algo} [VAL]",   y_va, p_va)
        res_te = evaluate_clf(f"{algo} [TEST]",  y_te, p_te)

        benchmark_results[algo] = {
            "train": res_tr,
            "validation": res_va,
            "test": res_te,
        }
        trained_models[algo] = model

    # Select winning model STRICTLY based on Validation performance (Val ROC-AUC, then Val F1)
    def val_score(algo_name):
        v = benchmark_results[algo_name]["validation"]
        return (v["roc_auc"], v["f1"], v["accuracy"])

    sorted_algos = sorted(algorithms, key=val_score, reverse=True)
    winner_name = sorted_algos[0]
    best_model  = trained_models[winner_name]

    logger.info("=" * 60)
    logger.info("ALGORITHM BENCHMARK WINNER (by Validation ROC-AUC & F1): %s", winner_name)
    logger.info("=" * 60)

    # Perform LOSO validation on full corpus
    loso_results = run_loso_cross_validation(corpus, winner_name, feat_cols)

    # Save artifacts
    with open(os.path.join(MODELS_DIR, "best_model_v3.pkl"), "wb") as f:
        pickle.dump(best_model, f)
    with open(os.path.join(MODELS_DIR, "scaler_v3.pkl"), "wb") as f:
        pickle.dump(scaler, f)
    with open(os.path.join(MODELS_DIR, "feature_columns_v3.json"), "w") as f:
        json.dump(feat_cols, f, indent=2)

    benchmark_summary = {
        "benchmark": benchmark_results,
        "ranking": sorted_algos,
        "winner": winner_name,
        "loso": loso_results,
        "simulation_hashes": hashes,
    }
    with open(os.path.join(RESULTS_DIR, "benchmark_results_v3.json"), "w") as f:
        json.dump(benchmark_summary, f, indent=2)

    logger.info("Benchmark complete. Artifacts saved in %s and %s", MODELS_DIR, RESULTS_DIR)
    return winner_name, benchmark_summary


if __name__ == "__main__":
    run_benchmark()
