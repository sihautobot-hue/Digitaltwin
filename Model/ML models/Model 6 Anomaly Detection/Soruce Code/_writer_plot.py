src = """
# plot_figures.py -- Model 6 V3: Publication-grade Visualization Suite
# Generates EXACTLY AND ONLY 6 PNG figures (300 DPI, No SVG):
#   1. fig01_confusion_matrix.png
#   2. fig02_precision_recall_curve.png
#   3. fig03_roc_curve.png
#   4. fig04_calibration_curve.png
#   5. fig05_shap_feature_importance.png
#   6. fig06_feature_importance_model.png

import os, json, logging, warnings
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, roc_curve, precision_recall_curve, roc_auc_score, average_precision_score
from sklearn.calibration import calibration_curve

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("PlotFigures-Model6-V3")

from config import RESULTS_DIR, FIGURES_DIR

# Styling config
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


def plot_fig01_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, opt_thresh: float):
    logger.info("Generating Figure 1: Confusion Matrix ...")
    cm = confusion_matrix(y_true, y_pred)
    cm_norm = confusion_matrix(y_true, y_pred, normalize="true")

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    annot = np.empty((2, 2), dtype=object)
    for i in range(2):
        for j in range(2):
            annot[i, j] = f"{cm[i, j]:,}\n({cm_norm[i, j]*100:.1f}%)"

    sns.heatmap(
        cm_norm, annot=annot, fmt="", cmap="Blues",
        xticklabels=["Nominal (0)", "Anomaly (1)"],
        yticklabels=["Nominal (0)", "Anomaly (1)"],
        cbar=True, ax=ax, linewidths=1.5, linecolor="white",
        vmin=0.0, vmax=1.0, annot_kws={"size": 12, "weight": "bold"}
    )
    ax.set_title(f"Figure 1: Confusion Matrix (Day-Ahead Operational Anomaly)\nTest Set (2022 Hold-Out @ Thresh={opt_thresh:.2f})", pad=15)
    ax.set_xlabel("Predicted Tomorrow State (Day t+1)")
    ax.set_ylabel("Actual Realized Tomorrow State (Day t+1)")

    out_path = os.path.join(FIGURES_DIR, "fig01_confusion_matrix.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def plot_fig02_precision_recall_curve(y_true: np.ndarray, y_proba: np.ndarray, opt_thresh: float):
    logger.info("Generating Figure 2: Precision-Recall Curve ...")
    prec, rec, thresholds = precision_recall_curve(y_true, y_proba)
    pr_auc = average_precision_score(y_true, y_proba) if len(np.unique(y_true)) > 1 else float(np.mean(y_true))
    baseline = np.mean(y_true)

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.plot(rec, prec, color=TEAL, lw=2.5, label=f"Model 6 V3 (PR-AUC = {pr_auc:.4f})")
    ax.axhline(baseline, color="gray", linestyle="--", lw=1.5, label=f"Prevalence Baseline ({baseline*100:.1f}%)")

    # Mark optimal threshold point
    idx = np.argmin(np.abs(thresholds - opt_thresh)) if len(thresholds) > 0 else 0
    if idx < len(rec) and idx < len(prec):
        ax.scatter([rec[idx]], [prec[idx]], color=CORAL_RED, s=100, zorder=5, label=f"Optimal Thresh ({opt_thresh:.2f})")

    ax.fill_between(rec, prec, color=TEAL, alpha=0.15)
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.05])
    ax.set_xlabel("Recall (Sensitivity)")
    ax.set_ylabel("Precision (Positive Predictive Value)")
    ax.set_title("Figure 2: Precision-Recall Curve\nDay-Ahead Operational Risk Forecast", pad=15)
    ax.legend(loc="lower left", frameon=True, framealpha=0.9)
    ax.grid(True, linestyle=":", alpha=0.6)

    out_path = os.path.join(FIGURES_DIR, "fig02_precision_recall_curve.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def plot_fig03_roc_curve(y_true: np.ndarray, y_proba: np.ndarray):
    logger.info("Generating Figure 3: ROC Curve ...")
    fpr, tpr, _ = roc_curve(y_true, y_proba)
    auc_score = roc_auc_score(y_true, y_proba) if len(np.unique(y_true)) > 1 else 0.5

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.plot(fpr, tpr, color=NAVY_BLUE, lw=2.5, label=f"Model 6 V3 (ROC-AUC = {auc_score:.4f})")
    ax.plot([0, 1], [0, 1], color="gray", lw=1.5, linestyle="--", label="Random Chance (AUC = 0.5000)")

    ax.fill_between(fpr, tpr, color=ICE_BLUE, alpha=0.25)
    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.set_xlabel("False Positive Rate (1 - Specificity)")
    ax.set_ylabel("True Positive Rate (Sensitivity / Recall)")
    ax.set_title("Figure 3: Receiver Operating Characteristic (ROC) Curve\nDay-Ahead Operational Anomaly Forecast", pad=15)
    ax.legend(loc="lower right", frameon=True, framealpha=0.9)
    ax.grid(True, linestyle=":", alpha=0.6)

    out_path = os.path.join(FIGURES_DIR, "fig03_roc_curve.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def plot_fig04_calibration_curve(y_true: np.ndarray, y_proba: np.ndarray):
    logger.info("Generating Figure 4: Calibration Curve ...")
    prob_true, prob_pred = calibration_curve(y_true, y_proba, n_bins=10, strategy="uniform")

    fig, ax = plt.subplots(figsize=(6.5, 5.5))
    ax.plot(prob_pred, prob_true, marker="s", color=NAVY_BLUE, lw=2.0, label="Model 6 V3 Reliability")
    ax.plot([0, 1], [0, 1], color="gray", linestyle="--", lw=1.5, label="Perfect Calibration")

    ax.set_xlim([-0.02, 1.02])
    ax.set_ylim([-0.02, 1.02])
    ax.set_xlabel("Mean Predicted Probability")
    ax.set_ylabel("Fraction of Positives (Observed Frequency)")
    ax.set_title("Figure 4: Probability Calibration Curve (Reliability Diagram)\nDay-Ahead Operational Anomaly Risk", pad=15)
    ax.legend(loc="upper left", frameon=True, framealpha=0.9)
    ax.grid(True, linestyle=":", alpha=0.6)

    out_path = os.path.join(FIGURES_DIR, "fig04_calibration_curve.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def plot_fig05_shap_feature_importance():
    logger.info("Generating Figure 5: SHAP Feature Importance ...")
    eval_json = os.path.join(RESULTS_DIR, "evaluation_v3.json")
    with open(eval_json, "r") as f:
        data = json.load(f)

    top_shap = pd.DataFrame(data["top_features_shap"]).head(15)
    top_shap = top_shap.sort_values("mean_abs_shap", ascending=True)

    fig, ax = plt.subplots(figsize=(8, 6.5))
    bars = ax.barh(top_shap["feature"], top_shap["mean_abs_shap"], color=NAVY_BLUE, alpha=0.85, height=0.65)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.005 * max(top_shap["mean_abs_shap"]), bar.get_y() + bar.get_height()/2,
                f"{w:.3f}", va="center", ha="left", fontsize=9, color="#333333")

    ax.set_xlabel("Mean |SHAP Value| (Impact on Model Log-Odds)")
    ax.set_title("Figure 5: TreeSHAP Feature Attribution (Top 15 Predictors)\nDay-Ahead Operational Risk Attribution", pad=15)
    ax.grid(True, axis="x", linestyle=":", alpha=0.6)

    out_path = os.path.join(FIGURES_DIR, "fig05_shap_feature_importance.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def plot_fig06_feature_importance_model():
    logger.info("Generating Figure 6: Model-based Feature Importance ...")
    eval_json = os.path.join(RESULTS_DIR, "evaluation_v3.json")
    with open(eval_json, "r") as f:
        data = json.load(f)

    fi_df = pd.DataFrame(data["top_features_model"]).head(15)
    fi_df = fi_df.sort_values("importance_pct", ascending=True)

    fig, ax = plt.subplots(figsize=(8, 6.5))
    bars = ax.barh(fi_df["feature"], fi_df["importance_pct"], color=ICE_BLUE, alpha=0.9, edgecolor=NAVY_BLUE, lw=0.8, height=0.65)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.2, bar.get_y() + bar.get_height()/2,
                f"{w:.1f}%", va="center", ha="left", fontsize=9, color="#222222", weight="bold")

    ax.set_xlabel("Relative Importance (% Split Contribution / Gain)")
    ax.set_title("Figure 6: Model-Based Feature Importance (Top 15)\nWinning Tree Ensemble Split Dynamics", pad=15)
    ax.grid(True, axis="x", linestyle=":", alpha=0.6)

    out_path = os.path.join(FIGURES_DIR, "fig06_feature_importance_model.png")
    plt.savefig(out_path)
    plt.close()
    logger.info("Saved: %s", out_path)


def generate_all_figures(y_true: np.ndarray, y_proba: np.ndarray, y_pred: np.ndarray, opt_thresh: float):
    logger.info("=" * 60)
    logger.info("GENERATING ALL 6 REQUIRED PNG FIGURES FOR MODEL 6 V3")
    logger.info("=" * 60)

    plot_fig01_confusion_matrix(y_true, y_pred, opt_thresh)
    plot_fig02_precision_recall_curve(y_true, y_proba, opt_thresh)
    plot_fig03_roc_curve(y_true, y_proba)
    plot_fig04_calibration_curve(y_true, y_proba)
    plot_fig05_shap_feature_importance()
    plot_fig06_feature_importance_model()

    logger.info("All 6 PNG figures successfully generated in %s", FIGURES_DIR)
"""
with open("plot_figures.py", "w", encoding="utf-8") as f:
    f.write(src.strip() + "\n")
print("Saved plot_figures.py")
