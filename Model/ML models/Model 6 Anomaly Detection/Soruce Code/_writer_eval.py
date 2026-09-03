src = """
# evaluate.py -- Model 6 V3: Scientific Evaluation, Regime Stress Testing, and Calibration
import os, json, logging, pickle, warnings
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, brier_score_loss,
    confusion_matrix, balanced_accuracy_score, matthews_corrcoef,
    precision_recall_curve
)
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance
import shap

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Evaluate-Model6-V3")

from config import MODELS_DIR, RESULTS_DIR, TARGET_NAME, RANDOM_SEED
from feature_engineering import load_raw_corpus, get_chronological_splits
from train_models import prep_xy, predict_proba_safe


def compute_expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")
    bin_edges = np.linspace(0, 1, n_bins + 1)
    bin_indices = np.digitize(y_prob, bin_edges) - 1
    bin_indices = np.clip(bin_indices, 0, n_bins - 1)
    ece = 0.0
    for i in range(n_bins):
        mask = bin_indices == i
        if np.sum(mask) > 0:
            bin_acc = np.mean(y_true[mask])
            bin_conf = np.mean(y_prob[mask])
            ece += np.abs(bin_acc - bin_conf) * (np.sum(mask) / len(y_true))
    return float(ece)


def find_optimal_threshold(y_val: np.ndarray, p_val: np.ndarray) -> Tuple[float, float]:
    precisions, recalls, thresholds = precision_recall_curve(y_val, p_val)
    f1_scores = np.where((precisions + recalls) > 0, 2 * (precisions * recalls) / (precisions + recalls), 0)
    best_idx = np.argmax(f1_scores)
    best_thresh = thresholds[best_idx] if best_idx < len(thresholds) else 0.5
    best_f1 = f1_scores[best_idx]
    logger.info("Optimal threshold selected on VALIDATION set: %.4f (Val F1: %.4f)", best_thresh, best_f1)
    return float(best_thresh), float(best_f1)


def evaluate_slice(slice_name: str, y_true: np.ndarray, y_proba: np.ndarray, threshold: float = 0.5) -> Dict:
    n = len(y_true)
    if n == 0:
        return {"n": 0, "positive_rate_pct": 0.0, "precision": None, "recall": None, "f1": None, "pr_auc": None}
    y_pred = (y_proba >= threshold).astype(int)
    acc = accuracy_score(y_true, y_pred)
    p   = precision_score(y_true, y_pred, zero_division=0)
    r   = recall_score(y_true, y_pred, zero_division=0)
    f1  = f1_score(y_true, y_pred, zero_division=0)
    try:
        pr_auc = average_precision_score(y_true, y_proba) if len(np.unique(y_true)) > 1 else float(np.mean(y_true))
    except Exception:
        pr_auc = float(np.mean(y_true))
    try:
        roc_auc = roc_auc_score(y_true, y_proba) if len(np.unique(y_true)) > 1 else 0.5
    except Exception:
        roc_auc = 0.5

    logger.info(
        "Slice [%-26s] (N=%4d, Pos=%.1f%%) | Prec=%.4f  Rec=%.4f  F1=%.4f  PR-AUC=%.4f",
        slice_name, n, np.mean(y_true) * 100, p, r, f1, pr_auc
    )
    return {
        "n": int(n),
        "positive_rate_pct": round(float(np.mean(y_true) * 100), 2),
        "precision": round(float(p), 4),
        "recall": round(float(r), 4),
        "f1": round(float(f1), 4),
        "pr_auc": round(float(pr_auc), 4),
        "roc_auc": round(float(roc_auc), 4),
    }


def run_explainability(model, X_sample: np.ndarray, y_sample: np.ndarray, feat_cols: List[str]) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
    logger.info("Computing TreeSHAP values on sample of N=%d ...", len(X_sample))
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
        if isinstance(shap_values, list) and len(shap_values) >= 2:
            shap_arr = shap_values[1]
        else:
            shap_arr = np.array(shap_values)
    except Exception as e:
        logger.warning("TreeExplainer failed (%s), using generic Explainer ...", str(e))
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

    logger.info("Computing Permutation Importance on validation sample ...")
    perm_res = permutation_importance(model, X_sample, y_sample, scoring="average_precision", n_repeats=5, random_state=RANDOM_SEED, n_jobs=-1)
    perm_df = pd.DataFrame({
        "feature": feat_cols,
        "perm_importance_mean": perm_res.importances_mean,
        "perm_importance_std": perm_res.importances_std,
    }).sort_values("perm_importance_mean", ascending=False).reset_index(drop=True)
    pos_sum = np.sum(np.maximum(0, perm_df["perm_importance_mean"]))
    perm_df["perm_importance_pct"] = round(100.0 * np.maximum(0, perm_df["perm_importance_mean"]) / (pos_sum if pos_sum > 0 else 1.0), 2)

    return shap_df, perm_df, shap_arr


def run_evaluation():
    logger.info("=" * 60)
    logger.info("RUNNING SCIENTIFIC EVALUATION, REGIME TESTS & INTERPRETABILITY")
    logger.info("=" * 60)

    with open(os.path.join(MODELS_DIR, "best_model_v3.pkl"), "rb") as f:
        model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "scaler_v3.pkl"), "rb") as f:
        scaler = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "feature_columns_v3.json"), "r") as f:
        feat_cols = json.load(f)

    corpus = load_raw_corpus(deduplicate=False)
    train_df, val_df, test_df = get_chronological_splits(corpus)

    X_va, y_va = prep_xy(val_df, feat_cols)
    X_va_s = scaler.transform(X_va)
    p_va = predict_proba_safe(model, X_va_s)

    # 1. Select optimal threshold on validation set only
    opt_threshold, val_f1_opt = find_optimal_threshold(y_va, p_va)

    # 2. Evaluate on Hold-out Test Set (2022)
    X_te, y_te = prep_xy(test_df, feat_cols)
    X_te_s = scaler.transform(X_te)
    p_te = predict_proba_safe(model, X_te_s)
    y_pred_te = (p_te >= opt_threshold).astype(int)

    acc = accuracy_score(y_te, y_pred_te)
    p   = precision_score(y_te, y_pred_te, zero_division=0)
    r   = recall_score(y_te, y_pred_te, zero_division=0)
    f1  = f1_score(y_te, y_pred_te, zero_division=0)
    bal_acc = balanced_accuracy_score(y_te, y_pred_te)
    mcc = matthews_corrcoef(y_te, y_pred_te)
    try:
        roc_auc = roc_auc_score(y_te, p_te) if len(np.unique(y_te)) > 1 else 0.5
    except Exception:
        roc_auc = 0.5
    try:
        pr_auc = average_precision_score(y_te, p_te) if len(np.unique(y_te)) > 1 else float(np.mean(y_te))
    except Exception:
        pr_auc = float(np.mean(y_te))
    brier = brier_score_loss(y_te, p_te)
    ece = compute_expected_calibration_error(y_te, p_te)
    cm = confusion_matrix(y_te, y_pred_te)
    tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, len(y_te))

    logger.info("=" * 60)
    logger.info("HOLD-OUT TEST PERFORMANCE (2022 Chronological @ Thresh=%.4f)", opt_threshold)
    logger.info("  Accuracy:          %.4f", acc)
    logger.info("  Precision:         %.4f", p)
    logger.info("  Recall:            %.4f", r)
    logger.info("  F1 Score:          %.4f", f1)
    logger.info("  PR-AUC:            %.4f", pr_auc)
    logger.info("  ROC-AUC:           %.4f", roc_auc)
    logger.info("  Balanced Accuracy: %.4f", bal_acc)
    logger.info("  MCC:               %.4f", mcc)
    logger.info("  Brier Score:       %.4f", brier)
    logger.info("  Calibration ECE:   %.4f", ece)
    logger.info("  Confusion Matrix:  TN=%d, FP=%d, FN=%d, TP=%d", tn, fp, fn, tp)
    logger.info("=" * 60)

    # 3. Operational Stress Tests (Regime Analysis)
    slices = {}
    # 1. Polar Winter (season_enc == 1 or polar_night_flag == 1)
    mask_winter = (test_df["season_enc"] == 1) | (test_df["polar_night_flag"] == 1)
    slices["Polar Winter"] = evaluate_slice("Polar Winter", y_te[mask_winter], p_te[mask_winter], opt_threshold)

    # 2. Polar Summer (season_enc == 0 and polar_day_flag == 1)
    mask_summer = (test_df["season_enc"] == 0) & (test_df["polar_day_flag"] == 1)
    slices["Polar Summer"] = evaluate_slice("Polar Summer", y_te[mask_summer], p_te[mask_summer], opt_threshold)

    # 3. High Population (scheduled_population >= 35)
    mask_high_pop = (test_df["scheduled_population"] >= 35)
    slices["High Population"] = evaluate_slice("High Population", y_te[mask_high_pop], p_te[mask_high_pop], opt_threshold)

    # 4. Low Population (scheduled_population < 20)
    mask_low_pop = (test_df["scheduled_population"] < 20)
    slices["Low Population"] = evaluate_slice("Low Population", y_te[mask_low_pop], p_te[mask_low_pop], opt_threshold)

    # 5. Storm Days (storm_flag == 1 or fc_wind_speed > 60)
    mask_storm = (test_df["storm_flag"] == 1) | (test_df["fc_wind_speed"] > 60)
    slices["Storm Days"] = evaluate_slice("Storm Days", y_te[mask_storm], p_te[mask_storm], opt_threshold)

    # 6. Extreme Cold (extreme_cold_flag == 1 or fc_temperature < -30)
    mask_cold = (test_df["extreme_cold_flag"] == 1) | (test_df["fc_temperature"] < -30)
    slices["Extreme Cold"] = evaluate_slice("Extreme Cold", y_te[mask_cold], p_te[mask_cold], opt_threshold)

    # 7. Fuel Critical (fuel_critical_flag == 1 or fuel_days_remaining_lag1 < 10)
    mask_fuel_crit = (test_df["fuel_critical_flag"] == 1) | (test_df["fuel_days_remaining_lag1"] < 10)
    slices["Fuel Critical (<10d)"] = evaluate_slice("Fuel Critical (<10d)", y_te[mask_fuel_crit], p_te[mask_fuel_crit], opt_threshold)

    # 8. Low Battery (battery_soc_low_flag == 1 or battery_soc_lag1 < 20)
    mask_low_bat = (test_df["battery_soc_low_flag"] == 1) | (test_df["battery_soc_lag1"] < 20)
    slices["Low Battery (<20%)"] = evaluate_slice("Low Battery (<20%)", y_te[mask_low_bat], p_te[mask_low_bat], opt_threshold)

    # 9. Inventory Stress (critical_items_lag1 > 5 or inventory_shortage_lag1 == 1)
    mask_inv_stress = (test_df["critical_items_lag1"] > 5) | (test_df["inventory_shortage_lag1"] == 1)
    slices["Inventory Stress"] = evaluate_slice("Inventory Stress", y_te[mask_inv_stress], p_te[mask_inv_stress], opt_threshold)

    # 10. Communication Degradation (communication_outage_lag1 == 1 or signal_quality_lag1 < 50)
    mask_comm_deg = (test_df["communication_outage_lag1"] == 1) | (test_df["signal_quality_lag1"] < 50)
    slices["Communication Degradation"] = evaluate_slice("Communication Degradation", y_te[mask_comm_deg], p_te[mask_comm_deg], opt_threshold)

    # Station Bharati vs Maitri
    mask_bharati = (test_df["station_enc"] == 0)
    mask_maitri  = (test_df["station_enc"] == 1)
    slices["Bharati Station"] = evaluate_slice("Bharati Station", y_te[mask_bharati], p_te[mask_bharati], opt_threshold)
    slices["Maitri Station"]  = evaluate_slice("Maitri Station",  y_te[mask_maitri],  p_te[mask_maitri],  opt_threshold)

    # 4. Model Feature Importance
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

    # 5. TreeSHAP & Permutation Importance
    np.random.seed(RANDOM_SEED)
    sample_idx = np.random.choice(len(X_te_s), size=min(1000, len(X_te_s)), replace=False)
    X_sample = X_te_s[sample_idx]
    y_sample = y_te[sample_idx]
    shap_df, perm_df, shap_arr = run_explainability(model, X_sample, y_sample, feat_cols)

    eval_summary = {
        "optimal_threshold": round(float(opt_threshold), 4),
        "validation_f1_at_optimal_threshold": round(float(val_f1_opt), 4),
        "overall_test": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(p), 4),
            "recall": round(float(r), 4),
            "f1": round(float(f1), 4),
            "pr_auc": round(float(pr_auc), 4),
            "roc_auc": round(float(roc_auc), 4),
            "balanced_accuracy": round(float(bal_acc), 4),
            "mcc": round(float(mcc), 4),
            "brier_score": round(float(brier), 4),
            "expected_calibration_error": round(float(ece), 4),
            "confusion_matrix": {
                "tn": int(tn),
                "fp": int(fp),
                "fn": int(fn),
                "tp": int(tp),
            },
        },
        "regime_stress_tests": slices,
        "top_features_model": fi_df.head(20).to_dict(orient="records"),
        "top_features_shap": shap_df.head(20).to_dict(orient="records"),
        "top_features_permutation": perm_df.head(20).to_dict(orient="records"),
    }
    with open(os.path.join(RESULTS_DIR, "evaluation_v3.json"), "w") as f:
        json.dump(eval_summary, f, indent=2)

    logger.info("Scientific evaluation complete. Saved to %s", RESULTS_DIR)
    return eval_summary, y_te, p_te, y_pred_te, shap_df, fi_df


if __name__ == "__main__":
    run_evaluation()
"""
with open("evaluate.py", "w", encoding="utf-8") as f:
    f.write(src.strip() + "\n")
print("Saved evaluate.py")
