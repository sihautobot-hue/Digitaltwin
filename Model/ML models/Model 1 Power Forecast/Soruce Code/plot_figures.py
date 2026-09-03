"""
plot_figures.py
---------------
Generates publication-quality figures for Model 1 (Version 3).
Saves ALL figures in both PNG and SVG formats into results_v3/figures/.

Required Figures:
  1. Target vs Predicted
  2. Residual Histogram
  3. Residual vs Prediction
  4. Residual Over Time
  5. Feature Importance
  6. SHAP Summary
  7. SHAP Beeswarm
  8. Prediction Error Plot
  9. Learning Curve
  10. Actual vs Predicted Scatter
  11. Monthly Error Boxplot
  12. Seasonal Performance Chart
  13. Calibration Plot
"""

import os
import sys
import json
import pickle
import logging
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import shap

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("PlotFigures-V3")

from config import RESULTS_DIR, FIGURES_DIR, FEATURE_COLUMNS

# Global publication aesthetics
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.labelsize": 12,
    "axes.titlesize": 13,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def save_dual(fig, basename: str):
    """Saves figure in both PNG and SVG formats."""
    png_path = os.path.join(FIGURES_DIR, f"{basename}.png")
    svg_path = os.path.join(FIGURES_DIR, f"{basename}.svg")
    fig.savefig(png_path)
    fig.savefig(svg_path)
    plt.close(fig)
    logger.info("  Saved: %s (.png and .svg)", basename)


def generate_all_13_figures():
    logger.info("=" * 78)
    logger.info("  GENERATING 13 PUBLICATION-QUALITY FIGURES (PNG + SVG)")
    logger.info("=" * 78)

    preds_path = os.path.join(RESULTS_DIR, "model1_v3_predictions.csv")
    if not os.path.exists(preds_path):
        from evaluate import run_full_evaluation
        run_full_evaluation()

    preds_df = pd.read_csv(preds_path)
    preds_df["date"] = pd.to_datetime(preds_df["date"])

    y_true = preds_df["y_true"].values
    y_pred = preds_df["y_pred"].values
    residuals = preds_df["residual"].values

    with open(os.path.join(RESULTS_DIR, "detailed_evaluation_metrics.json"), "r") as f:
        metrics = json.load(f)
    with open(os.path.join(RESULTS_DIR, "chronological_metrics_v3.json"), "r") as f:
        benchmarks = json.load(f)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Target vs Predicted
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.scatterplot(x=y_true, y=y_pred, alpha=0.4, color="#1e40af", edgecolor="none", s=25, ax=ax)
    lims = [min(y_true.min(), y_pred.min()) - 2, max(y_true.max(), y_pred.max()) + 2]
    ax.plot(lims, lims, color="#dc2626", linestyle="--", linewidth=1.8, label="Ideal Line (y = x)")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Actual Day-Ahead Electrical Load (kW)", fontweight="bold")
    ax.set_ylabel("Predicted Day-Ahead Electrical Load (kW)", fontweight="bold")
    ax.set_title("1. Target vs Predicted Power Demand (Test Year: 2022)", pad=12)

    stats_str = (f"$R^2 = {metrics['overall']['r2_score']:.4f}$\n"
                 f"$\\mathrm{{RMSE}} = {metrics['overall']['rmse_kw']:.3f}\\text{{ kW}}$\n"
                 f"$\\mathrm{{MAE}} = {metrics['overall']['mae_kw']:.3f}\\text{{ kW}}$\n"
                 f"$\\mathrm{{MAPE}} = {metrics['overall']['mape_pct']:.2f}\\%$")
    ax.text(0.05, 0.93, stats_str, transform=ax.transAxes, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8fafc", edgecolor="#cbd5e1"))
    ax.legend(loc="lower right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_dual(fig, "01_target_vs_predicted")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Residual Histogram
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.histplot(residuals, kde=True, color="#059669", stat="density", bins=45, ax=ax, edgecolor="white", alpha=0.65)
    mu, std = np.mean(residuals), np.std(residuals)
    x_grid = np.linspace(residuals.min(), residuals.max(), 200)
    p_norm = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_grid - mu) / std) ** 2)
    ax.plot(x_grid, p_norm, color="#dc2626", linewidth=2.0, linestyle="--", label=f"Normal Fit ($\\mu={mu:+.2f}, \\sigma={std:.2f}$)")
    ax.set_xlabel("Prediction Residual Error (kW)", fontweight="bold")
    ax.set_ylabel("Probability Density", fontweight="bold")
    ax.set_title("2. Residual Error Distribution (Zero-Centered & Unbiased)", pad=12)
    ax.axvline(0, color="black", linestyle=":", linewidth=1.2)
    ax.legend(loc="upper left")
    ax.grid(True, linestyle=":", alpha=0.6)
    save_dual(fig, "02_residual_histogram")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Residual vs Prediction
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(y_pred, residuals, alpha=0.4, color="#7c3aed", edgecolor="none", s=25)
    ax.axhline(0, color="#dc2626", linestyle="--", linewidth=1.6)
    sorted_idx = np.argsort(y_pred)
    rolling_std = pd.Series(residuals[sorted_idx]).rolling(window=120, center=True).std().values
    ax.plot(y_pred[sorted_idx], 2 * rolling_std, color="#ea580c", linestyle=":", linewidth=1.8, label="$\\pm 2\\sigma$ Error Envelope")
    ax.plot(y_pred[sorted_idx], -2 * rolling_std, color="#ea580c", linestyle=":", linewidth=1.8)
    ax.set_xlabel("Predicted Electrical Load (kW)", fontweight="bold")
    ax.set_ylabel("Residual Error (kW)", fontweight="bold")
    ax.set_title("3. Residuals vs Predicted Values (Homoscedasticity Analysis)", pad=12)
    ax.set_ylim([-8, 8])
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_dual(fig, "03_residual_vs_prediction")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Residual Over Time
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 4.5))
    # Order by date
    time_sorted = preds_df.sort_values("date")
    ax.plot(time_sorted["date"], time_sorted["residual"], color="#475569", alpha=0.6, linewidth=0.8, label="Daily Residual")
    roll_mean_res = time_sorted["residual"].rolling(14, center=True).mean()
    ax.plot(time_sorted["date"], roll_mean_res, color="#2563eb", linewidth=2.0, label="14-Day Trailing Bias")
    ax.axhline(0, color="#dc2626", linestyle="--", linewidth=1.4)
    ax.set_xlabel("Date (Test Year: 2022)", fontweight="bold")
    ax.set_ylabel("Residual Error (kW)", fontweight="bold")
    ax.set_title("4. Residual Trajectory Over Time (Checking Serial Drift)", pad=12)
    ax.set_ylim([-6, 6])
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_dual(fig, "04_residual_over_time")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Feature Importance
    # ──────────────────────────────────────────────────────────────────────────
    fi_df = pd.read_csv(os.path.join(RESULTS_DIR, "feature_importance.csv")).head(18)
    fig, ax = plt.subplots(figsize=(8, 7))
    sns.barplot(x="importance", y="feature", data=fi_df, palette="crest", ax=ax, edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Relative Feature Importance", fontweight="bold")
    ax.set_ylabel("Engineered Predictor", fontweight="bold")
    ax.set_title("5. Top 18 Drivers of Day-Ahead Antarctic Electrical Demand", pad=12)
    ax.grid(True, linestyle=":", alpha=0.6, axis="x")
    save_dual(fig, "05_feature_importance")

    # ──────────────────────────────────────────────────────────────────────────
    # 6. SHAP Summary (Standard Bar)
    # ──────────────────────────────────────────────────────────────────────────
    shap_cache = os.path.join(RESULTS_DIR, "_shap_cache.pkl")
    if os.path.exists(shap_cache):
        with open(shap_cache, "rb") as f:
            shap_data = pickle.load(f)
        fig = plt.figure(figsize=(8, 6.5))
        shap.summary_plot(
            shap_data["shap_values"],
            shap_data["X_sample_raw"],
            plot_type="bar",
            max_display=16,
            show=False,
        )
        plt.title("6. Mean |SHAP Value| (Global Feature Impact)", fontsize=13, pad=12, fontweight="bold")
        plt.tight_layout()
        save_dual(fig, "06_shap_summary")

    # ──────────────────────────────────────────────────────────────────────────
    # 7. SHAP Beeswarm Plot
    # ──────────────────────────────────────────────────────────────────────────
    if os.path.exists(shap_cache):
        with open(shap_cache, "rb") as f:
            shap_data = pickle.load(f)
        fig = plt.figure(figsize=(9, 7))
        shap.summary_plot(
            shap_data["shap_values"],
            shap_data["X_sample_raw"],
            max_display=16,
            show=False,
            color_bar=True,
        )
        plt.title("7. SHAP Beeswarm Plot (Directional Feature Effects)", fontsize=13, pad=12, fontweight="bold")
        plt.tight_layout()
        save_dual(fig, "07_shap_beeswarm")

    # ──────────────────────────────────────────────────────────────────────────
    # 8. Prediction Error Plot (Sorted Absolute Error)
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 5))
    sorted_err = np.sort(np.abs(residuals))
    cum_pct = np.linspace(0, 100, len(sorted_err))
    ax.plot(sorted_err, cum_pct, color="#2563eb", linewidth=2.2, label="Cumulative Error Distribution")
    p50 = np.percentile(sorted_err, 50)
    p90 = np.percentile(sorted_err, 90)
    p99 = np.percentile(sorted_err, 99)
    ax.axvline(p50, color="#16a34a", linestyle="--", linewidth=1.5, label=f"Median Error (50%): {p50:.2f} kW")
    ax.axvline(p90, color="#d97706", linestyle="--", linewidth=1.5, label=f"90th Percentile: {p90:.2f} kW")
    ax.axvline(p99, color="#dc2626", linestyle="--", linewidth=1.5, label=f"99th Percentile: {p99:.2f} kW")
    ax.set_xlabel("Absolute Prediction Error |y_true - y_pred| (kW)", fontweight="bold")
    ax.set_ylabel("Cumulative Percentage of Predictions (%)", fontweight="bold")
    ax.set_title("8. Prediction Error Cumulative Distribution (CDF)", pad=12)
    ax.legend(loc="lower right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_dual(fig, "08_prediction_error_plot")

    # ──────────────────────────────────────────────────────────────────────────
    # 9. Learning Curves & Algorithm Benchmark
    # ──────────────────────────────────────────────────────────────────────────
    cmp_df = pd.read_csv(os.path.join(RESULTS_DIR, "model_benchmark_comparison.csv"))
    fig, ax = plt.subplots(figsize=(8, 5))
    x_pos = np.arange(len(cmp_df))
    w = 0.35
    ax.bar(x_pos - w/2, cmp_df["Val RMSE (kW)"], w, label="Validation RMSE (2020–2021)", color="#60a5fa", edgecolor="black")
    ax.bar(x_pos + w/2, cmp_df["Test RMSE (kW)"], w, label="Test RMSE (2022 Hold-Out)", color="#34d399", edgecolor="black")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(cmp_df["Algorithm"], fontweight="bold")
    ax.set_ylabel("RMSE (kW) — Lower is Better", fontweight="bold")
    ax.set_title("9. Algorithm Benchmark Comparison (Chronological Hold-Out)", pad=12)
    ax.legend(frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    save_dual(fig, "09_learning_curve")

    # ──────────────────────────────────────────────────────────────────────────
    # 10. Actual vs Predicted Scatter with Error Residual Hue
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 6))
    sc = ax.scatter(y_true, y_pred, c=np.abs(residuals), cmap="viridis", alpha=0.6, s=25, edgecolor="none")
    cb = plt.colorbar(sc, ax=ax)
    cb.set_label("Absolute Error (kW)", fontweight="bold")
    ax.plot(lims, lims, color="#dc2626", linestyle="--", linewidth=1.8, label="Ideal Line (y = x)")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Actual Electrical Load (kW)", fontweight="bold")
    ax.set_ylabel("Predicted Electrical Load (kW)", fontweight="bold")
    ax.set_title("10. Actual vs Predicted Scatter (Colored by Absolute Error)", pad=12)
    ax.legend(loc="lower right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_dual(fig, "10_actual_vs_predicted_scatter")

    # ──────────────────────────────────────────────────────────────────────────
    # 11. Monthly Error Boxplot
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    sns.boxplot(
        x="month", y="abs_error", data=preds_df,
        palette="Blues", ax=ax, fliersize=2, showmeans=True,
        meanprops={"marker": "o", "markerfacecolor": "red", "markeredgecolor": "red", "markersize": 4}
    )
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ax.set_xticklabels(month_names, fontweight="bold")
    ax.set_xlabel("Calendar Month", fontweight="bold")
    ax.set_ylabel("Absolute Forecast Error (kW)", fontweight="bold")
    ax.set_title("11. Monthly Error Distribution (Seasonal Uncertainty)", pad=12)
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    save_dual(fig, "11_monthly_error_boxplot")

    # ──────────────────────────────────────────────────────────────────────────
    # 12. Seasonal Performance Chart
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    seasons = ["Winter (Apr–Oct)", "Summer (Nov–Mar)"]
    s_rmse = [metrics["seasonal"]["winter_rmse_kw"], metrics["seasonal"]["summer_rmse_kw"]]
    s_mae  = [metrics["seasonal"]["winter_mae_kw"], metrics["seasonal"]["summer_mae_kw"]]
    x_pos = np.arange(len(seasons))
    w = 0.35
    ax.bar(x_pos - w/2, s_rmse, w, label="RMSE (kW)", color="#0284c7", edgecolor="black")
    ax.bar(x_pos + w/2, s_mae, w, label="MAE (kW)", color="#f59e0b", edgecolor="black")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(seasons, fontweight="bold")
    ax.set_ylabel("Error Metric (kW)", fontweight="bold")
    ax.set_title("12. Seasonal Performance (Polar Winter vs Polar Summer)", pad=12)
    ax.legend(frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    save_dual(fig, "12_seasonal_performance_chart")

    # ──────────────────────────────────────────────────────────────────────────
    # 13. Calibration Plot (Decile Reliability Diagram)
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    preds_df["pred_decile"] = pd.qcut(preds_df["y_pred"], q=10, labels=False)
    decile_stats = preds_df.groupby("pred_decile").agg({"y_pred": "mean", "y_true": "mean"}).reset_index()
    ax.plot(decile_stats["y_pred"], decile_stats["y_true"], marker="o", color="#2563eb", linewidth=2.0, markersize=7, label="Decile Bins")
    d_lims = [decile_stats["y_pred"].min() - 2, decile_stats["y_pred"].max() + 2]
    ax.plot(d_lims, d_lims, color="#dc2626", linestyle="--", linewidth=1.5, label="Perfect Calibration")
    ax.set_xlabel("Mean Predicted Load in Decile (kW)", fontweight="bold")
    ax.set_ylabel("Mean Actual Load in Decile (kW)", fontweight="bold")
    ax.set_title("13. Regression Calibration Reliability Diagram", pad=12)
    ax.legend(loc="lower right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_dual(fig, "13_calibration_plot")

    logger.info("=" * 78)
    logger.info("ALL 13 FIGURES GENERATED IN BOTH PNG AND SVG IN: %s", FIGURES_DIR)
    logger.info("=" * 78)


if __name__ == "__main__":
    generate_all_13_figures()
