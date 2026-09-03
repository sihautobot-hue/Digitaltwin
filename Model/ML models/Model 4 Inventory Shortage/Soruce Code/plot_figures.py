# plot_figures.py
# Publication-quality scientific visualization suite for Model 4 Version 3.
# Generates EXACTLY AND ONLY 6 PNG figures (300 DPI):
#   1. fig01_confusion_matrix.png
#   2. fig02_roc_curve.png
#   3. fig03_precision_recall_curve.png
#   4. fig04_shap_feature_importance.png
#   5. fig05_prediction_probability_distribution.png
#   6. fig06_feature_importance_model.png

import os
import json
import logging
import pickle
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, roc_curve, precision_recall_curve,
    roc_auc_score, average_precision_score
)

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("PlotFigures-Model4-V3")

from config import (
    MODELS_DIR,
    RESULTS_DIR,
    FIGURES_DIR,
    TARGET_NAME,
)

# Set global Matplotlib publication styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"],
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 11,
    "axes.labelweight": "bold",
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.titleweight": "bold",
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "axes.spines.top": False,
    "axes.spines.right": False,
})

NAVY_BLUE = "#1B3B6F"
ICE_BLUE  = "#6D9DC5"
CORAL_RED = "#D9534F"
TEAL      = "#2E8B57"
GOLD      = "#D4AF37"


def plot_fig01_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray):
    logger.info("Generating Figure 1: Confusion Matrix ...")
    cm = confusion_matrix(y_true, y_pred)
    cm_norm = confusion_matrix(y_true, y_pred, normalize="true")

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    
    annot = np.empty((2, 2), dtype=object)
    for i in range(2):
        for j in range(2):
            count = cm[i, j]
            pct = cm_norm[i, j] * 100
            annot[i, j] = str(count) + "\n(" + f"{pct:.1f}%" + ")"

    sns.heatmap(
        cm_norm, annot=annot, fmt="", cmap="Blues",
        xticklabels=["No Shortage (0)", "Shortage (1)"],
        yticklabels=["No Shortage (0)", "Shortage (1)"],
        cbar=True, ax=ax, linewidths=1.5, linecolor="white",
        vmin=0.0, vmax=1.0, annot_kws={"size": 12, "weight": "bold"}
    )

    ax.set_title("Figure 1: Confusion Matrix (Day-Ahead Inventory Shortage)\nTest Set (2022 Chronological)", pad=15)
    ax.set_xlabel("Predicted Tomorrow State (Day t+1)")
    ax.set_ylabel("Actual Realized Tomorrow State (Day t+1)")

    out_path = os.path.join(FIGURES_DIR, "fig01_confusion_matrix.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def plot_fig02_roc_curve(y_true: np.ndarray, y_proba: np.ndarray):
    logger.info("Generating Figure 2: ROC Curve ...")
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    auc_score = roc_auc_score(y_true, y_proba) if len(np.unique(y_true)) > 1 else 0.5

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.plot(fpr, tpr, color=NAVY_BLUE, lw=2.5, label=f"Model 4 V3 (ROC-AUC = {auc_score:.4f})")
    ax.plot([0, 1], [0, 1], color="gray", lw=1.5, linestyle="--", label="Random Chance (AUC = 0.5000)")
    
    ax.fill_between(fpr, tpr, color=ICE_BLUE, alpha=0.25)
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.set_xlabel("False Positive Rate (1 - Specificity)")
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)")
    ax.set_title("Figure 2: Receiver Operating Characteristic (ROC) Curve\nDay-Ahead Inventory Shortage Forecast", pad=15)
    ax.legend(loc="lower right", frameon=True, framealpha=0.9)
    ax.grid(True, linestyle=":", alpha=0.6)

    out_path = os.path.join(FIGURES_DIR, "fig02_roc_curve.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def plot_fig03_precision_recall_curve(y_true: np.ndarray, y_proba: np.ndarray):
    logger.info("Generating Figure 3: Precision-Recall Curve ...")
    precision, recall, _ = precision_recall_curve(y_true, y_proba)
    pr_auc = average_precision_score(y_true, y_proba) if len(np.unique(y_true)) > 1 else float(np.mean(y_true))
    baseline = np.mean(y_true)

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.plot(recall, precision, color=TEAL, lw=2.5, label=f"Model 4 V3 (PR-AUC / AP = {pr_auc:.4f})")
    ax.axhline(baseline, color="gray", linestyle="--", lw=1.5, label=f"Prevalence Baseline ({baseline*100:.1f}%)")

    ax.fill_between(recall, precision, color=TEAL, alpha=0.15)
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.05])
    ax.set_xlabel("Recall (True Positive Rate)")
    ax.set_ylabel("Precision (Positive Predictive Value)")
    ax.set_title("Figure 3: Precision-Recall Curve\nDay-Ahead Inventory Shortage Forecast", pad=15)
    ax.legend(loc="lower left", frameon=True, framealpha=0.9)
    ax.grid(True, linestyle=":", alpha=0.6)

    out_path = os.path.join(FIGURES_DIR, "fig03_precision_recall_curve.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def plot_fig04_shap_feature_importance():
    logger.info("Generating Figure 4: SHAP Feature Importance ...")
    eval_json = os.path.join(RESULTS_DIR, "evaluation_v3.json")
    with open(eval_json, "r") as f:
        data = json.load(f)
    
    top_shap = pd.DataFrame(data["top_features_shap"]).head(15)
    top_shap = top_shap.sort_values("mean_abs_shap", ascending=True)

    fig, ax = plt.subplots(figsize=(8, 6.5))
    bars = ax.barh(top_shap["feature"], top_shap["mean_abs_shap"], color=NAVY_BLUE, alpha=0.85, edgecolor="none", height=0.65)
    
    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.005 * max(top_shap["mean_abs_shap"]), bar.get_y() + bar.get_height()/2,
                f"{w:.3f}", va="center", ha="left", fontsize=9, color="#333333")

    ax.set_xlabel("Mean |SHAP Value| (Impact on Model Log-Odds)")
    ax.set_title("Figure 4: SHAP Feature Importance (Top 15 Predictors)\nDay-Ahead Inventory Shortage Attribution", pad=15)
    ax.grid(True, axis="x", linestyle=":", alpha=0.6)

    out_path = os.path.join(FIGURES_DIR, "fig04_shap_feature_importance.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def plot_fig05_prediction_probability_distribution(preds_df: pd.DataFrame):
    logger.info("Generating Figure 5: Actual vs Predicted Probability Distribution ...")
    fig, ax = plt.subplots(figsize=(7.5, 5.5))

    p_no_shortage = preds_df[preds_df[TARGET_NAME] == 0]["pred_probability"]
    p_shortage    = preds_df[preds_df[TARGET_NAME] == 1]["pred_probability"]

    sns.kdeplot(p_no_shortage, ax=ax, color=TEAL, fill=True, alpha=0.35, lw=2.0, label="Actual: No Shortage (y=0)", warn_singular=False)
    sns.kdeplot(p_shortage, ax=ax, color=CORAL_RED, fill=True, alpha=0.35, lw=2.0, label="Actual: Shortage (y=1)", warn_singular=False)

    ax.axvline(0.5, color="black", linestyle="--", lw=1.5, label="Decision Threshold (0.50)")
    ax.set_xlim([-0.05, 1.05])
    ax.set_xlabel("Predicted Probability of Shortage Tomorrow P(Shortage | Day t)")
    ax.set_ylabel("Probability Density")
    ax.set_title("Figure 5: Prediction Probability Distribution\nClass Separation Analysis on Test Set", pad=15)
    ax.legend(loc="upper center", frameon=True, framealpha=0.9)
    ax.grid(True, linestyle=":", alpha=0.6)

    out_path = os.path.join(FIGURES_DIR, "fig05_prediction_probability_distribution.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def plot_fig06_feature_importance_model():
    logger.info("Generating Figure 6: Model-based Feature Importance ...")
    fi_csv = os.path.join(RESULTS_DIR, "feature_importance_v3.csv")
    fi_df = pd.read_csv(fi_csv).head(15)
    fi_df = fi_df.sort_values("importance", ascending=True)

    fig, ax = plt.subplots(figsize=(8, 6.5))
    bars = ax.barh(fi_df["feature"], fi_df["importance_pct"], color=ICE_BLUE, alpha=0.9, edgecolor=NAVY_BLUE, lw=0.8, height=0.65)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.2, bar.get_y() + bar.get_height()/2,
                f"{w:.1f}%", va="center", ha="left", fontsize=9, color="#222222", weight="bold")

    ax.set_xlabel("Relative Importance (% Contribution to Tree Splits / Gain)")
    ax.set_title("Figure 6: Model-Based Feature Importance (Top 15)\nWinning Tree Ensemble Split Dynamics", pad=15)
    ax.grid(True, axis="x", linestyle=":", alpha=0.6)

    out_path = os.path.join(FIGURES_DIR, "fig06_feature_importance_model.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def generate_all_figures():
    logger.info("=" * 60)
    logger.info("GENERATING ALL 6 REQUIRED PNG FIGURES FOR MODEL 4 V3")
    logger.info("=" * 60)

    preds_path = os.path.join(RESULTS_DIR, "test_predictions_v3.csv")
    if not os.path.exists(preds_path):
        raise FileNotFoundError(f"Missing predictions file: {preds_path}")
    preds_df = pd.read_csv(preds_path)

    y_true  = preds_df[TARGET_NAME].values.astype(int)
    y_proba = preds_df["pred_probability"].values
    y_pred  = preds_df["pred_label"].values.astype(int)

    plot_fig01_confusion_matrix(y_true, y_pred)
    plot_fig02_roc_curve(y_true, y_proba)
    plot_fig03_precision_recall_curve(y_true, y_proba)
    plot_fig04_shap_feature_importance()
    plot_fig05_prediction_probability_distribution(preds_df)
    plot_fig06_feature_importance_model()

    logger.info("All 6 PNG figures successfully generated in %s", FIGURES_DIR)


if __name__ == "__main__":
    generate_all_figures()
