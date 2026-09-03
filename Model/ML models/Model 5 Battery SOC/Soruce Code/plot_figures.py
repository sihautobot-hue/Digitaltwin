"""
plot_figures.py
---------------
Step 9: Publication-Grade PNG Visualizations.
Model 5 (Version 3): Day-Ahead Battery State of Charge Forecasting

Generates ONLY the 6 required figures in PNG format:
  1. Actual vs Predicted SoC
  2. Residual Plot
  3. Residual Histogram
  4. SHAP Feature Importance
  5. Battery SoC Time Series (Actual vs Predicted)
  6. Model Feature Importance
"""

import os
import logging
from typing import Dict, Any

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl

from config import FIGURES_DIR, RESULTS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("PlotFigures-M5V3")

# Matplotlib formatting defaults for publication
mpl.rcParams.update({
    "font.sans-serif": "DejaVu Sans",
    "font.family": "sans-serif",
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "axes.labelsize": 11,
    "axes.titlesize": 13,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.titlesize": 14,
    "lines.linewidth": 1.5,
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})


def plot_01_actual_vs_predicted(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metrics: Dict[str, Any]
) -> str:
    """Figure 1: Actual vs Predicted SoC Parity Plot."""
    fig, ax = plt.subplots(figsize=(8, 7))
    
    r2 = metrics["global_metrics"]["r2_score"]
    rmse = metrics["global_metrics"]["rmse_pct"]
    mae = metrics["global_metrics"]["mae_pct"]

    # Hexbin / Scatter
    hb = ax.hexbin(y_true, y_pred, gridsize=45, cmap="Blues", mincnt=1, alpha=0.85)
    cb = fig.colorbar(hb, ax=ax, shrink=0.8)
    cb.set_label("Sample Density (Days)", fontsize=10)

    # 1:1 Parity Line
    lims = [min(np.min(y_true), np.min(y_pred)) - 2, max(np.max(y_true), np.max(y_pred)) + 2]
    ax.plot(lims, lims, color="#d9534f", linestyle="--", linewidth=2.0, label="Ideal Parity ($y = x$)")

    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Actual Battery SoC (%) [Day t+1 Ground Truth]", fontweight="bold")
    ax.set_ylabel("Predicted Battery SoC (%) [Day t 18:00 Forecast]", fontweight="bold")
    ax.set_title("Figure 1: Actual vs Predicted Battery State of Charge (SoC)\nHoldout Test Year 2022 (Bharati & Maitri Stations)", fontweight="bold")

    # Annotation box
    textstr = "\n".join([
        f"$R^2 = {r2:.4f}$",
        f"$\\mathrm{{RMSE}} = {rmse:.3f}\\%$",
        f"$\\mathrm{{MAE}} = {mae:.3f}\\%$",
        f"$N = {len(y_true):,}$ days",
    ])
    props = dict(boxstyle="round,pad=0.6", facecolor="white", edgecolor="#0275d8", alpha=0.9)
    ax.text(0.05, 0.93, textstr, transform=ax.transAxes, fontsize=10, verticalalignment="top", bbox=props)

    ax.legend(loc="lower right", framealpha=0.9)
    plt.tight_layout()

    out_path = os.path.join(FIGURES_DIR, "01_actual_vs_predicted_soc.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    logger.info("Generated Figure 1: %s", out_path)
    return out_path


def plot_02_residual_plot(
    y_pred: np.ndarray,
    residuals: np.ndarray
) -> str:
    """Figure 2: Residuals vs Fitted Values Plot."""
    fig, ax = plt.subplots(figsize=(9, 6))

    mean_res = np.mean(residuals)
    std_res = np.std(residuals)

    ax.scatter(y_pred, residuals, alpha=0.45, color="#0275d8", edgecolor="none", s=24, label="Daily Residuals ($y - \\hat{y}$)")
    ax.axhline(0, color="#d9534f", linestyle="-", linewidth=1.8, label="Zero Error Line")
    ax.axhline(mean_res + 2 * std_res, color="#f0ad4e", linestyle="--", linewidth=1.4, label=f"$+2\\sigma$ Envelope (+{2*std_res:.2f}%)")
    ax.axhline(mean_res - 2 * std_res, color="#f0ad4e", linestyle="--", linewidth=1.4, label=f"$-2\\sigma$ Envelope (-{2*std_res:.2f}%)")

    ax.fill_between([np.min(y_pred), np.max(y_pred)], mean_res - 2 * std_res, mean_res + 2 * std_res, color="#f0ad4e", alpha=0.08)

    ax.set_xlabel("Fitted Battery SoC (%)", fontweight="bold")
    ax.set_ylabel("Residual ($y - \\hat{y}$) [%]", fontweight="bold")
    ax.set_title("Figure 2: Residual Plot (Error vs Fitted State of Charge)\nHoldout Test Year 2022", fontweight="bold")
    ax.legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()

    out_path = os.path.join(FIGURES_DIR, "02_residual_plot.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    logger.info("Generated Figure 2: %s", out_path)
    return out_path


def plot_03_residual_histogram(
    residuals: np.ndarray,
    metrics: Dict[str, Any]
) -> str:
    """Figure 3: Residual Error Distribution Histogram and KDE."""
    fig, ax = plt.subplots(figsize=(9, 6))

    mu = metrics["global_metrics"]["mean_bias_pct"]
    sigma = metrics["global_metrics"]["residual_std_pct"]

    # Histogram
    n, bins, patches = ax.hist(residuals, bins=50, density=True, alpha=0.65, color="#5bc0de", edgecolor="#0275d8", label="Empirical Residual Density")

    # Fitted Normal Curve
    x_norm = np.linspace(np.min(residuals), np.max(residuals), 300)
    y_norm = (1.0 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_norm - mu) / sigma) ** 2)
    ax.plot(x_norm, y_norm, color="#d9534f", linewidth=2.2, label=f"Normal Fit ($\\mu={mu:.3f}\\%$, $\\sigma={sigma:.3f}\\%$)")

    ax.axvline(0, color="black", linestyle="--", linewidth=1.2, label="Zero Bias")
    ax.axvline(mu, color="#5cb85c", linestyle="-", linewidth=1.5, label=f"Mean Bias ({mu:+.3f}%)")

    ax.set_xlabel("Residual Error ($y - \\hat{y}$) [%]", fontweight="bold")
    ax.set_ylabel("Probability Density", fontweight="bold")
    ax.set_title("Figure 3: Residual Histogram and Error Distribution\nHoldout Test Year 2022", fontweight="bold")
    ax.legend(loc="upper right", framealpha=0.9)
    plt.tight_layout()

    out_path = os.path.join(FIGURES_DIR, "03_residual_histogram.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    logger.info("Generated Figure 3: %s", out_path)
    return out_path


def plot_04_shap_feature_importance(
    shap_df: pd.DataFrame,
    top_n: int = 15
) -> str:
    """Figure 4: SHAP Feature Importance Bar Chart."""
    fig, ax = plt.subplots(figsize=(10, 6.5))

    top_shap = shap_df.head(top_n).sort_values("Mean_Abs_SHAP", ascending=True)

    colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(top_shap)))
    bars = ax.barh(top_shap["Feature"], top_shap["Mean_Abs_SHAP"], color=colors, edgecolor="#292b2c", height=0.65)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.03 * np.max(top_shap["Mean_Abs_SHAP"]), bar.get_y() + bar.get_height() / 2,
                f"{w:.3f}", va="center", ha="left", fontsize=8.5, fontweight="bold")

    ax.set_xlabel("Mean Absolute SHAP Value ($E[|\\mathrm{SHAP}|]$) [SoC % Impact]", fontweight="bold")
    ax.set_ylabel("Engineered Feature", fontweight="bold")
    ax.set_title(f"Figure 4: TreeSHAP Global Feature Importance (Top {top_n} Predictors)\nDay-Ahead Battery State of Charge Forecast", fontweight="bold")
    ax.set_xlim(0, np.max(top_shap["Mean_Abs_SHAP"]) * 1.15)
    plt.tight_layout()

    out_path = os.path.join(FIGURES_DIR, "04_shap_feature_importance.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    logger.info("Generated Figure 4: %s", out_path)
    return out_path


def plot_05_battery_soc_time_series(
    test_df: pd.DataFrame,
    y_true: np.ndarray,
    y_pred: np.ndarray,
    train_residuals: np.ndarray
) -> str:
    """Figure 5: Battery SoC Time Series (Actual vs Predicted with 95% interval)."""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Pick single station or representative slice for clean time-series visualization (e.g. Bharati Station 2022)
    mask = (test_df["station_id"] == "BHARATI") if "station_id" in test_df else slice(None)
    if not np.any(mask):
        mask = slice(None)

    dates = test_df.loc[mask, "date"].values if "date" in test_df else np.arange(len(y_true[mask]))
    yt = y_true[mask]
    yp = y_pred[mask]

    # Empirical 95% interval from train residuals
    q025 = np.percentile(train_residuals, 2.5)
    q975 = np.percentile(train_residuals, 97.5)
    lower_bound = np.clip(yp + q025, 0.0, 100.0)
    upper_bound = np.clip(yp + q975, 0.0, 100.0)

    ax.plot(dates, yt, color="#292b2c", linewidth=1.8, label="Actual Battery SoC Ground Truth", alpha=0.9)
    ax.plot(dates, yp, color="#0275d8", linewidth=1.5, linestyle="--", label="Day-Ahead Forecast (Model 5 V3)")
    ax.fill_between(dates, lower_bound, upper_bound, color="#0275d8", alpha=0.18, label="95% Empirical Prediction Interval")

    ax.set_ylabel("Battery State of Charge (%)", fontweight="bold")
    ax.set_xlabel("Date (Year 2022)", fontweight="bold")
    ax.set_title("Figure 5: Battery SoC Time Series Tracking (Actual vs Day-Ahead Forecast)\nBharati Research Station — Year 2022 Holdout", fontweight="bold")
    ax.set_ylim(0, 100)
    ax.legend(loc="lower left", framealpha=0.9)
    plt.tight_layout()

    out_path = os.path.join(FIGURES_DIR, "05_battery_soc_time_series.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    logger.info("Generated Figure 5: %s", out_path)
    return out_path


def plot_06_model_feature_importance(
    fi_df: pd.DataFrame,
    top_n: int = 15
) -> str:
    """Figure 6: Native Model Feature Importance Bar Chart."""
    fig, ax = plt.subplots(figsize=(10, 6.5))

    top_fi = fi_df.head(top_n).sort_values("Importance_Pct", ascending=True)

    colors = plt.cm.magma(np.linspace(0.35, 0.85, len(top_fi)))
    bars = ax.barh(top_fi["Feature"], top_fi["Importance_Pct"], color=colors, edgecolor="#292b2c", height=0.65)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 0.03 * np.max(top_fi["Importance_Pct"]), bar.get_y() + bar.get_height() / 2,
                f"{w:.2f}%", va="center", ha="left", fontsize=8.5, fontweight="bold")

    ax.set_xlabel("Relative Feature Importance (Tree Split Gain / MDI) [%]", fontweight="bold")
    ax.set_ylabel("Engineered Feature", fontweight="bold")
    ax.set_title(f"Figure 6: Native Model Feature Importance (Top {top_n} Predictors)\nDay-Ahead Battery State of Charge Forecast", fontweight="bold")
    ax.set_xlim(0, np.max(top_fi["Importance_Pct"]) * 1.15)
    plt.tight_layout()

    out_path = os.path.join(FIGURES_DIR, "06_model_feature_importance.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    logger.info("Generated Figure 6: %s", out_path)
    return out_path


def generate_all_six_figures(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    residuals: np.ndarray,
    train_residuals: np.ndarray,
    test_df: pd.DataFrame,
    metrics: Dict[str, Any],
    shap_df: pd.DataFrame,
    fi_df: pd.DataFrame
) -> Dict[str, str]:
    """Generate and save the 6 required PNG figures."""
    fig_paths = {}
    fig_paths["01_actual_vs_predicted"] = plot_01_actual_vs_predicted(y_true, y_pred, metrics)
    fig_paths["02_residual_plot"] = plot_02_residual_plot(y_pred, residuals)
    fig_paths["03_residual_histogram"] = plot_03_residual_histogram(residuals, metrics)
    fig_paths["04_shap_feature_importance"] = plot_04_shap_feature_importance(shap_df)
    fig_paths["05_battery_soc_time_series"] = plot_05_battery_soc_time_series(test_df, y_true, y_pred, train_residuals)
    fig_paths["06_model_feature_importance"] = plot_06_model_feature_importance(fi_df)
    return fig_paths
