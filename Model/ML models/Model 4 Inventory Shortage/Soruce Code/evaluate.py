# evaluate.py
# Comprehensive scientific evaluation, operational stress testing, and SHAP interpretability for Model 4 V3.

import os
import json
import logging
import pickle
import warnings
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, brier_score_loss,
    confusion_matrix, roc_curve, precision_recall_curve
)
import shap

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("Evaluate-Model4-V3")

from config import (
    MODELS_DIR,
    RESULTS_DIR,
    TARGET_NAME,
    RANDOM_SEED,
)
from feature_engineering import (
    load_raw_corpus,
    get_chronological_splits,
)
from train_models import prep_xy, predict_proba_safe


def evaluate_slice(slice_name: str, y_true: np.ndarray, y_proba: np.ndarray, threshold: float = 0.5) -> Dict:
    n = len(y_true)
    if n == 0:
        return {"n": 0, "accuracy": None, "precision": None, "recall": None, "f1": None, "roc_auc": None}
    y_pred = (y_proba >= threshold).astype(int)
    acc = accuracy_score(y_true, y_pred)
    p   = precision_score(y_true, y_pred, zero_division=0)
    r   = recall_score(y_true, y_pred, zero_division=0)
    f1  = f1_score(y_true, y_pred, zero_division=0)
    try:
        auc = roc_auc_score(y_true, y_proba) if len(np.unique(y_true)) > 1 else 0.5
    except Exception:
        auc = 0.5
    try:
        pr_auc = average_precision_score(y_true, y_proba) if len(np.unique(y_true)) > 1 else float(np.mean(y_true))
    except Exception:
        pr_auc = float(np.mean(y_true))

    logger.info(
        "Slice [%-18s] (N=%4d, Pos=%.1f%%) | Acc=%.4f  Prec=%.4f  Rec=%.4f  F1=%.4f  AUC=%.4f",
        slice_name, n, np.mean(y_true) * 100, acc, p, r, f1, auc
    )
    return {
        "n": n,
        "positive_rate_pct": round(float(np.mean(y_true) * 100), 2),
        "accuracy": round(float(acc), 4),
        "precision": round(float(p), 4),
        "recall": round(float(r), 4),
        "f1": round(float(f1), 4),
        "roc_auc": round(float(auc), 4),
        "pr_auc": round(float(pr_auc), 4),
    }


def compute_shap_analysis(model: object, X_sample: np.ndarray, feat_cols: List[str]) -> Tuple[pd.DataFrame, np.ndarray]:
    logger.info("Computing SHAP values on sample of N=%d instances ...", len(X_sample))
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
        if isinstance(shap_values, list) and len(shap_values) >= 2:
            shap_arr = shap_values[1]  # positive class
        else:
            shap_arr = np.array(shap_values)
    except Exception as e:
        logger.warning("TreeExplainer failed (%s), falling back to generic Explainer ...", str(e))
        explainer = shap.Explainer(model.predict, X_sample)
        res = explainer(X_sample)
        shap_arr = res.values

    if shap_arr.ndim == 3:
        shap_arr = shap_arr[:, :, 1]

    mean_abs_shap = np.mean(np.abs(shap_arr), axis=0)
    shap_df = pd.DataFrame({
        "feature": feat_cols,
        "mean_abs_shap": mean_abs_shap,
    }).sort_values("mean_abs_shap", ascending=False).reset_index(drop=True)

    shap_df["importance_pct"] = round(100.0 * shap_df["mean_abs_shap"] / np.sum(shap_df["mean_abs_shap"]), 2)
    logger.info("Top 10 Features by SHAP computed.")
    return shap_df, shap_arr


def run_evaluation():
    logger.info("=" * 60)
    logger.info("RUNNING SCIENTIFIC EVALUATION & REGIME STRESS TESTS (MODEL 4 V3)")
    logger.info("=" * 60)

    # Load artifacts
    with open(os.path.join(MODELS_DIR, "best_model_v3.pkl"), "rb") as f:
        model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "scaler_v3.pkl"), "rb") as f:
        scaler = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "feature_columns_v3.json"), "r") as f:
        feat_cols = json.load(f)

    corpus = load_raw_corpus(deduplicate=False)
    train_df, val_df, test_df = get_chronological_splits(corpus)

    X_te, y_te = prep_xy(test_df, feat_cols)
    X_te_s = scaler.transform(X_te)
    p_te = predict_proba_safe(model, X_te_s)
    y_pred_te = (p_te >= 0.5).astype(int)

    # 1. Overall Test Metrics
    acc = accuracy_score(y_te, y_pred_te)
    p   = precision_score(y_te, y_pred_te, zero_division=0)
    r   = recall_score(y_te, y_pred_te, zero_division=0)
    f1  = f1_score(y_te, y_pred_te, zero_division=0)
    try:
        auc = roc_auc_score(y_te, p_te) if len(np.unique(y_te)) > 1 else 0.5
    except Exception:
        auc = 0.5
    try:
        pr_auc = average_precision_score(y_te, p_te) if len(np.unique(y_te)) > 1 else float(np.mean(y_te))
    except Exception:
        pr_auc = float(np.mean(y_te))
    brier = brier_score_loss(y_te, p_te)
    cm = confusion_matrix(y_te, y_pred_te)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, len(y_te))

    # Bias analysis
    fp_rate = fp / max(tn + fp, 1)
    fn_rate = fn / max(tp + fn, 1)
    bias_direction = "Bias toward False Positives (conservative safety bias)" if fp > fn else "Bias toward False Negatives" if fn > fp else "Balanced"

    logger.info("=" * 60)
    logger.info("TEST PERFORMANCE (CHRONOLOGICAL 2022)")
    logger.info("  Accuracy:    %.4f", acc)
    logger.info("  Precision:   %.4f", p)
    logger.info("  Recall:      %.4f", r)
    logger.info("  F1 Score:    %.4f", f1)
    logger.info("  ROC-AUC:     %.4f", auc)
    logger.info("  PR-AUC:      %.4f", pr_auc)
    logger.info("  Brier Score: %.4f", brier)
    logger.info("  Confusion Matrix: TN=%d, FP=%d, FN=%d, TP=%d", tn, fp, fn, tp)
    logger.info("  Bias: %s (FPR=%.4f, FNR=%.4f)", bias_direction, fp_rate, fn_rate)
    logger.info("=" * 60)

    # 2. Operational Slice / Regime Stress Testing
    slices = {}
    
    # Low Inventory: inv_health_lag0 < 50 or critical_items_lag0 > 15
    mask_low_inv = (test_df["inv_health_lag0"] < 50) | (test_df["critical_items_lag0"] > 15)
    slices["Low Inventory"] = evaluate_slice("Low Inventory", y_te[mask_low_inv], p_te[mask_low_inv])

    # Winter: season_enc == 1
    mask_winter = (test_df["season_enc"] == 1)
    slices["Winter"] = evaluate_slice("Winter", y_te[mask_winter], p_te[mask_winter])

    # Summer: season_enc == 0
    mask_summer = (test_df["season_enc"] == 0)
    slices["Summer"] = evaluate_slice("Summer", y_te[mask_summer], p_te[mask_summer])

    # High Population: scheduled_population >= 35
    mask_high_pop = (test_df["scheduled_population"] >= 35)
    slices["High Population"] = evaluate_slice("High Population", y_te[mask_high_pop], p_te[mask_high_pop])

    # Normal Operation: inv_health_lag0 >= 50 and scheduled_population < 35
    mask_normal = (test_df["inv_health_lag0"] >= 50) & (test_df["scheduled_population"] < 35)
    slices["Normal Operation"] = evaluate_slice("Normal Operation", y_te[mask_normal], p_te[mask_normal])

    # Station Bharati vs Maitri
    mask_bharati = (test_df["station_enc"] == 0)
    mask_maitri  = (test_df["station_enc"] == 1)
    slices["Bharati Station"] = evaluate_slice("Bharati Station", y_te[mask_bharati], p_te[mask_bharati])
    slices["Maitri Station"]  = evaluate_slice("Maitri Station",  y_te[mask_maitri],  p_te[mask_maitri])

    # 3. Model Feature Importance
    if hasattr(model, "feature_importances_"):
        raw_fi = model.feature_importances_
    elif hasattr(model, "get_feature_importance"):
        raw_fi = model.get_feature_importance()
    else:
        raw_fi = np.ones(len(feat_cols))

    fi_df = pd.DataFrame({
        "feature": feat_cols,
        "importance": raw_fi,
    }).sort_values("importance", ascending=False).reset_index(drop=True)
    fi_df["importance_pct"] = round(100.0 * fi_df["importance"] / np.sum(fi_df["importance"]), 2)
    fi_df.to_csv(os.path.join(RESULTS_DIR, "feature_importance_v3.csv"), index=False)

    # 4. SHAP Interpretability
    np.random.seed(RANDOM_SEED)
    sample_idx = np.random.choice(len(X_te_s), size=min(1000, len(X_te_s)), replace=False)
    X_sample = X_te_s[sample_idx]
    shap_df, shap_arr = compute_shap_analysis(model, X_sample, feat_cols)

    # Save SHAP sample
    shap_out = pd.DataFrame(shap_arr, columns=feat_cols)
    shap_out.to_csv(os.path.join(RESULTS_DIR, "shap_values_sample.csv"), index=False)

    # 5. Save Test Predictions
    preds_df = test_df[["date", "station_id", "season", TARGET_NAME]].copy()
    preds_df["pred_probability"] = p_te
    preds_df["pred_label"] = y_pred_te
    preds_df["is_correct"] = (preds_df[TARGET_NAME] == preds_df["pred_label"]).astype(int)
    preds_df.to_csv(os.path.join(RESULTS_DIR, "test_predictions_v3.csv"), index=False)

    # Save comprehensive evaluation JSON
    eval_summary = {
        "overall_test": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(f1), 4),
            "roc_auc": round(float(auc), 4),
            "pr_auc": round(float(pr_auc), 4),
            "brier_score": round(float(brier), 4),
            "confusion_matrix": {
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
            },
            "bias_analysis": {
                "fp_rate": round(float(fp_rate), 4),
                "fn_rate": round(float(fn_rate), 4),
                "bias_direction": bias_direction,
            },
        },
        "regime_stress_tests": slices,
        "top_features_model": fi_df.head(20).to_dict(orient="records"),
        "top_features_shap": shap_df.head(20).to_dict(orient="records"),
    }
    with open(os.path.join(RESULTS_DIR, "evaluation_v3.json"), "w") as f:
        json.dump(eval_summary, f, indent=2)

    logger.info("Evaluation complete. Results saved in %s", RESULTS_DIR)
    return eval_summary


if __name__ == "__main__":
    run_evaluation()
