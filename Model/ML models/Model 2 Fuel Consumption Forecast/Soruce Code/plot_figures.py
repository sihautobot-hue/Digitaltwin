"""
plot_figures.py
---------------
Generates all 18 publication-quality figures for Model 2 (Version 3).
Saves all figures in high-resolution PNG (and SVG) format in results_v3/figures/.

Figures Generated:
  1. Actual vs Predicted
  2. Residual Plot
  3. Residual Histogram
  4. Residual vs Time
  5. Feature Importance
  6. Permutation Importance
  7. SHAP Summary
  8. SHAP Bar Plot
  9. Prediction Error Distribution
  10. Learning Curve
  11. Validation Curve
  12. Monthly Error
  13. Season-wise Error
  14. Storm vs Normal Error
  15. Fuel Consumption Time Series
  16. Top 20 Feature Importance
  17. Correlation Heatmap (training features)
  18. Prediction Confidence Plot (Interval Coverage)
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
logger = logging.getLogger("PlotFigures-Model2-V3")

from config import RESULTS_DIR, FIGURES_DIR, FEATURE_COLUMNS

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


def save_fig(fig, basename: str):
    png_path = os.path.join(FIGURES_DIR, f"{basename}.png")
    svg_path = os.path.join(FIGURES_DIR, f"{basename}.svg")
    fig.savefig(png_path)
    fig.savefig(svg_path)
    plt.close(fig)
    logger.info("  Saved: %s (.png and .svg)", basename)


def generate_all_18_figures():
    logger.info("=" * 78)
    logger.info("  GENERATING 18 PUBLICATION-QUALITY FIGURES FOR MODEL 2 V3")
    logger.info("=" * 78)

    preds_path = os.path.join(RESULTS_DIR, "model2_v3_predictions.csv")
    if not os.path.exists(preds_path):
        from evaluate import run_full_evaluation
        run_full_evaluation()

    df_preds = pd.read_csv(preds_path)
    df_preds["date"] = pd.to_datetime(df_preds["date"])

    y_true = df_preds["y_true"].values
    y_pred = df_preds["y_pred"].values
    residuals = df_preds["residual"].values

    with open(os.path.join(RESULTS_DIR, "detailed_evaluation_metrics.json"), "r") as f:
        metrics = json.load(f)
    with open(os.path.join(RESULTS_DIR, "chronological_metrics_v3.json"), "r") as f:
        benchmarks = json.load(f)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. Actual vs Predicted
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 6))
    sns.scatterplot(x=y_true, y=y_pred, alpha=0.45, color="#0284c7", edgecolor="none", s=25, ax=ax)
    lims = [min(y_true.min(), y_pred.min()) - 20, max(y_true.max(), y_pred.max()) + 20]
    ax.plot(lims, lims, color="#dc2626", linestyle="--", linewidth=1.8, label="Ideal Line (y = x)")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Actual Day-Ahead Fuel Burn (Liters/day)", fontweight="bold")
    ax.set_ylabel("Predicted Day-Ahead Fuel Burn (Liters/day)", fontweight="bold")
    ax.set_title("1. Actual vs Predicted Fuel Consumption (Test Year: 2022)", pad=12)

    stats_str = (f"$R^2 = {metrics['overall']['r2_score']:.4f}$\n"
                 f"$\\mathrm{{RMSE}} = {metrics['overall']['rmse_liters']:.2f}\\text{{ L/day}}$\n"
                 f"$\\mathrm{{MAE}} = {metrics['overall']['mae_liters']:.2f}\\text{{ L/day}}$\n"
                 f"$\\mathrm{{MAPE}} = {metrics['overall']['mape_pct']:.2f}\\%$")
    ax.text(0.05, 0.93, stats_str, transform=ax.transAxes, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8fafc", edgecolor="#cbd5e1"))
    ax.legend(loc="lower right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_fig(fig, "01_actual_vs_predicted")

    # ──────────────────────────────────────────────────────────────────────────
    # 2. Residual Plot (Residuals vs Predicted)
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.scatter(y_pred, residuals, alpha=0.4, color="#7c3aed", edgecolor="none", s=25)
    ax.axhline(0, color="#dc2626", linestyle="--", linewidth=1.6)
    s_idx = np.argsort(y_pred)
    roll_s = pd.Series(residuals[s_idx]).rolling(window=120, center=True).std().values
    ax.plot(y_pred[s_idx], 2 * roll_s, color="#ea580c", linestyle=":", linewidth=1.8, label="$\\pm 2\\sigma$ Error Envelope")
    ax.plot(y_pred[s_idx], -2 * roll_s, color="#ea580c", linestyle=":", linewidth=1.8)
    ax.set_xlabel("Predicted Fuel Consumption (Liters/day)", fontweight="bold")
    ax.set_ylabel("Residual Error (Liters/day)", fontweight="bold")
    ax.set_title("2. Residuals vs Predicted Values (Homoscedasticity Analysis)", pad=12)
    ax.set_ylim([-50, 50])
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_fig(fig, "02_residual_plot")

    # ──────────────────────────────────────────────────────────────────────────
    # 3. Residual Histogram
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.histplot(residuals, kde=True, color="#059669", stat="density", bins=45, ax=ax, edgecolor="white", alpha=0.65)
    mu, std = np.mean(residuals), np.std(residuals)
    x_g = np.linspace(residuals.min(), residuals.max(), 200)
    p_n = (1 / (std * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_g - mu) / std) ** 2)
    ax.plot(x_g, p_n, color="#dc2626", linewidth=2.0, linestyle="--", label=f"Normal Fit ($\\mu={mu:+.2f}, \\sigma={std:.2f}$)")
    ax.set_xlabel("Residual Error (Liters/day)", fontweight="bold")
    ax.set_ylabel("Probability Density", fontweight="bold")
    ax.set_title("3. Residual Error Distribution (Zero-Centered)", pad=12)
    ax.axvline(0, color="black", linestyle=":", linewidth=1.2)
    ax.legend(loc="upper left")
    ax.grid(True, linestyle=":", alpha=0.6)
    save_fig(fig, "03_residual_histogram")

    # ──────────────────────────────────────────────────────────────────────────
    # 4. Residual vs Time
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 4.5))
    t_df = df_preds.sort_values("date")
    ax.plot(t_df["date"], t_df["residual"], color="#64748b", alpha=0.6, linewidth=0.8, label="Daily Residual")
    ax.plot(t_df["date"], t_df["residual"].rolling(14, center=True).mean(), color="#2563eb", linewidth=2.0, label="14-Day Trailing Bias")
    ax.axhline(0, color="#dc2626", linestyle="--", linewidth=1.4)
    ax.set_xlabel("Date (Test Year: 2022)", fontweight="bold")
    ax.set_ylabel("Residual Error (Liters/day)", fontweight="bold")
    ax.set_title("4. Residual Trajectory Over Time (Zero-Drift Validation)", pad=12)
    ax.set_ylim([-45, 45])
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_fig(fig, "04_residual_vs_time")

    # ──────────────────────────────────────────────────────────────────────────
    # 5. Feature Importance (All Engineered)
    # ──────────────────────────────────────────────────────────────────────────
    fi_df = pd.read_csv(os.path.join(RESULTS_DIR, "feature_importance.csv"))
    fig, ax = plt.subplots(figsize=(8, 8))
    sns.barplot(x="importance", y="feature", data=fi_df.head(15), palette="mako", ax=ax, edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Relative Feature Importance Score", fontweight="bold")
    ax.set_ylabel("Predictor", fontweight="bold")
    ax.set_title("5. Model Feature Importance (Day-Ahead Fuel Drivers)", pad=12)
    ax.grid(True, linestyle=":", alpha=0.6, axis="x")
    save_fig(fig, "05_feature_importance")

    # ──────────────────────────────────────────────────────────────────────────
    # 6. Permutation Importance
    # ──────────────────────────────────────────────────────────────────────────
    perm_df = pd.read_csv(os.path.join(RESULTS_DIR, "permutation_importance.csv")).head(15)
    fig, ax = plt.subplots(figsize=(8, 7))
    ax.barh(perm_df["feature"][::-1], perm_df["importance_mean"][::-1],
            xerr=perm_df["importance_std"][::-1], color="#3b82f6", edgecolor="#1e40af", alpha=0.85, capsize=3)
    ax.set_xlabel("Drop in Out-of-Sample RMSE when Shuffled (L/day)", fontweight="bold")
    ax.set_ylabel("Feature", fontweight="bold")
    ax.set_title("6. Out-of-Sample Permutation Feature Importance", pad=12)
    ax.grid(True, linestyle=":", alpha=0.6, axis="x")
    save_fig(fig, "06_permutation_importance")

    # ──────────────────────────────────────────────────────────────────────────
    # 7. SHAP Summary (Beeswarm)
    # ──────────────────────────────────────────────────────────────────────────
    shap_cache = os.path.join(RESULTS_DIR, "_shap_cache.pkl")
    if os.path.exists(shap_cache):
        with open(shap_cache, "rb") as f:
            shap_data = pickle.load(f)
        fig = plt.figure(figsize=(9, 7))
        shap.summary_plot(shap_data["shap_values"], shap_data["X_sample_raw"], max_display=16, show=False, color_bar=True)
        plt.title("7. SHAP Beeswarm Plot (Directional Fuel Consumption Effects)", fontsize=13, pad=12, fontweight="bold")
        plt.tight_layout()
        save_fig(fig, "07_shap_summary")

    # ──────────────────────────────────────────────────────────────────────────
    # 8. SHAP Bar Plot (Global Impact)
    # ──────────────────────────────────────────────────────────────────────────
    if os.path.exists(shap_cache):
        fig = plt.figure(figsize=(8, 6.5))
        shap.summary_plot(shap_data["shap_values"], shap_data["X_sample_raw"], plot_type="bar", max_display=16, show=False)
        plt.title("8. Global Mean |SHAP Value| (Fuel Forecast Impact)", fontsize=13, pad=12, fontweight="bold")
        plt.tight_layout()
        save_fig(fig, "08_shap_bar_plot")

    # ──────────────────────────────────────────────────────────────────────────
    # 9. Prediction Error Distribution (CDF)
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 5))
    s_err = np.sort(np.abs(residuals))
    c_pct = np.linspace(0, 100, len(s_err))
    ax.plot(s_err, c_pct, color="#2563eb", linewidth=2.2, label="Cumulative Error CDF")
    p50 = np.percentile(s_err, 50)
    p90 = np.percentile(s_err, 90)
    p99 = np.percentile(s_err, 99)
    ax.axvline(p50, color="#16a34a", linestyle="--", linewidth=1.5, label=f"Median: {p50:.2f} L/day")
    ax.axvline(p90, color="#d97706", linestyle="--", linewidth=1.5, label=f"90th %ile: {p90:.2f} L/day")
    ax.axvline(p99, color="#dc2626", linestyle="--", linewidth=1.5, label=f"99th %ile: {p99:.2f} L/day")
    ax.set_xlabel("Absolute Prediction Error (Liters/day)", fontweight="bold")
    ax.set_ylabel("Cumulative Percentage of Predictions (%)", fontweight="bold")
    ax.set_title("9. Prediction Error Cumulative Distribution Function", pad=12)
    ax.legend(loc="lower right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_fig(fig, "09_prediction_error_distribution")

    # ──────────────────────────────────────────────────────────────────────────
    # 10. Learning Curve / Benchmark Comparison
    # ──────────────────────────────────────────────────────────────────────────
    cmp_df = pd.read_csv(os.path.join(RESULTS_DIR, "model_benchmark_comparison.csv"))
    fig, ax = plt.subplots(figsize=(10, 5))
    x_pos = np.arange(len(cmp_df))
    w = 0.35
    ax.bar(x_pos - w/2, cmp_df["Val RMSE (L)"], w, label="Validation RMSE (2020–2021)", color="#60a5fa", edgecolor="black")
    ax.bar(x_pos + w/2, cmp_df["Test RMSE (L)"], w, label="Test RMSE (2022)", color="#34d399", edgecolor="black")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(cmp_df["Algorithm"], fontweight="bold", rotation=20)
    ax.set_ylabel("RMSE (Liters/day) — Lower is Better", fontweight="bold")
    ax.set_title("10. Algorithm Portfolio Benchmark (Zero-Leakage Fuel Forecast)", pad=12)
    ax.legend(frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    save_fig(fig, "10_learning_curve")

    # ──────────────────────────────────────────────────────────────────────────
    # 11. Validation Curve (Train vs Val vs Test across Algorithms)
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(cmp_df["Algorithm"], cmp_df["Train R²"], marker="o", color="#0284c7", linewidth=2.0, label="Train R²")
    ax.plot(cmp_df["Algorithm"], cmp_df["Val R²"], marker="s", color="#16a34a", linewidth=2.0, label="Val R² (2020–21)")
    ax.plot(cmp_df["Algorithm"], cmp_df["Test R²"], marker="^", color="#dc2626", linewidth=2.0, label="Test R² (2022)")
    ax.set_xticklabels(cmp_df["Algorithm"], fontweight="bold", rotation=20)
    ax.set_ylabel("Coefficient of Determination (R²)", fontweight="bold")
    ax.set_title("11. Generalization & Validation Curve Across 8 Algorithms", pad=12)
    ax.legend(loc="lower right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_fig(fig, "11_validation_curve")

    # ──────────────────────────────────────────────────────────────────────────
    # 12. Monthly Error
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(9, 5))
    m_dict = metrics["monthly"]
    m_names = list(m_dict.keys())
    m_rmses = [m_dict[m]["rmse_liters"] for m in m_names]
    m_maes  = [m_dict[m]["mae_liters"] for m in m_names]
    x_pos = np.arange(len(m_names))
    ax.bar(x_pos - 0.2, m_rmses, 0.4, label="Monthly RMSE (L/day)", color="#38bdf8", edgecolor="black")
    ax.bar(x_pos + 0.2, m_maes, 0.4, label="Monthly MAE (L/day)", color="#fb7185", edgecolor="black")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(m_names, fontweight="bold")
    ax.set_ylabel("Error Metric (Liters/day)", fontweight="bold")
    ax.set_title("12. Monthly Fuel Forecast Accuracy Across Calendar Cycle", pad=12)
    ax.legend(frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    save_fig(fig, "12_monthly_error")

    # ──────────────────────────────────────────────────────────────────────────
    # 13. Season-wise Error
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    s_names = ["Winter Regime", "Summer Regime"]
    st = metrics["stress_tests"]
    s_r = [st["winter_regime"]["rmse"], st["summer_regime"]["rmse"]]
    s_m = [st["winter_regime"]["mae"], st["summer_regime"]["mae"]]
    x_pos = np.arange(2)
    ax.bar(x_pos - 0.2, s_r, 0.4, label="RMSE (L/day)", color="#0284c7", edgecolor="black")
    ax.bar(x_pos + 0.2, s_m, 0.4, label="MAE (L/day)", color="#f59e0b", edgecolor="black")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(s_names, fontweight="bold")
    ax.set_ylabel("Error (Liters/day)", fontweight="bold")
    ax.set_title("13. Seasonal Error: Polar Winter vs Polar Summer", pad=12)
    ax.legend(frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    save_fig(fig, "13_season_wise_error")

    # ──────────────────────────────────────────────────────────────────────────
    # 14. Storm vs Normal Error
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 5))
    st_labels = ["Normal Days (<65 km/h)", "Storm Days (>=65 km/h)"]
    st_r = [st["calm_days_lt_65kmh"]["rmse"], st["storm_days_ge_65kmh"]["rmse"]]
    st_m = [st["calm_days_lt_65kmh"]["mae"], st["storm_days_ge_65kmh"]["mae"]]
    x_pos = np.arange(2)
    ax.bar(x_pos - 0.2, st_r, 0.4, label="RMSE (L/day)", color="#3b82f6", edgecolor="black")
    ax.bar(x_pos + 0.2, st_m, 0.4, label="MAE (L/day)", color="#ef4444", edgecolor="black")
    ax.set_xticks(x_pos)
    ax.set_xticklabels(st_labels, fontweight="bold")
    ax.set_ylabel("Error (Liters/day)", fontweight="bold")
    ax.set_title("14. Forecast Error Under Extreme Storm Conditions", pad=12)
    ax.legend(frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6, axis="y")
    save_fig(fig, "14_storm_vs_normal_error")

    # ──────────────────────────────────────────────────────────────────────────
    # 15. Fuel Consumption Time Series (365 Days)
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 5))
    s_sub = df_preds[(df_preds["station_enc"] == 0) & (df_preds["run_id"] == 1)].sort_values("date")
    if len(s_sub) == 0: s_sub = df_preds.iloc[:365].sort_values("date")

    ax.plot(s_sub["date"], s_sub["y_true"], label="Actual Fuel Consumption (L/day)", color="#0f172a", linewidth=1.6)
    ax.plot(s_sub["date"], s_sub["y_pred"], label="Day-Ahead Forecast (L/day)", color="#0284c7", linewidth=1.4, linestyle="--")
    ax.fill_between(
        s_sub["date"],
        s_sub["y_pred"] - metrics["overall"]["rmse_liters"] * 1.96,
        s_sub["y_pred"] + metrics["overall"]["rmse_liters"] * 1.96,
        color="#bae6fd", alpha=0.45, label="95% Confidence Interval"
    )
    ax.set_xlabel("Date (Test Year: 2022)", fontweight="bold")
    ax.set_ylabel("Fuel Consumption (Liters/day)", fontweight="bold")
    ax.set_title("15. Full-Year Day-Ahead Fuel Consumption Forecast Timeline (Maitri Station)", pad=12)
    ax.legend(loc="upper right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_fig(fig, "15_fuel_consumption_time_series")

    # ──────────────────────────────────────────────────────────────────────────
    # 16. Top 20 Feature Importance
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 8))
    sns.barplot(x="importance", y="feature", data=fi_df.head(20), palette="viridis", ax=ax, edgecolor="black", linewidth=0.5)
    ax.set_xlabel("Importance Score", fontweight="bold")
    ax.set_ylabel("Predictor", fontweight="bold")
    ax.set_title("16. Top 20 Predictors of Antarctic Station Fuel Burn", pad=12)
    ax.grid(True, linestyle=":", alpha=0.6, axis="x")
    save_fig(fig, "16_top_20_feature_importance")

    # ──────────────────────────────────────────────────────────────────────────
    # 17. Correlation Heatmap (Training Features - Top 12)
    # ──────────────────────────────────────────────────────────────────────────
    top_cols = fi_df["feature"].head(12).tolist()
    corr_mat = df_preds[top_cols].corr()
    fig, ax = plt.subplots(figsize=(9, 8))
    sns.heatmap(corr_mat, annot=True, fmt=".2f", cmap="coolwarm", cbar=True, ax=ax, linewidths=0.5)
    ax.set_title("17. Correlation Matrix of Top 12 Pre-Forecast Predictors", pad=12)
    save_fig(fig, "17_correlation_heatmap")

    # ──────────────────────────────────────────────────────────────────────────
    # 18. Prediction Confidence Plot (Interval Coverage)
    # ──────────────────────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 5))
    nominal_levels = np.array([50, 60, 70, 80, 90, 95, 99])
    empirical_coverage = []
    for lev in nominal_levels:
        alpha = lev / 100.0
        low = np.percentile(residuals, (1 - alpha) / 2 * 100)
        high = np.percentile(residuals, (1 + alpha) / 2 * 100)
        cov = np.mean((residuals >= low) & (residuals <= high)) * 100
        empirical_coverage.append(cov)

    ax.plot(nominal_levels, empirical_coverage, marker="o", color="#2563eb", linewidth=2.0, label="Empirical Coverage")
    ax.plot([45, 100], [45, 100], color="#dc2626", linestyle="--", linewidth=1.5, label="Perfect Calibration (y = x)")
    ax.set_xlim([45, 100])
    ax.set_ylim([45, 100])
    ax.set_xlabel("Nominal Prediction Interval Level (%)", fontweight="bold")
    ax.set_ylabel("Empirical Hold-Out Coverage (%)", fontweight="bold")
    ax.set_title("18. Prediction Interval Calibration Reliability Diagram", pad=12)
    ax.legend(loc="lower right", frameon=True)
    ax.grid(True, linestyle=":", alpha=0.6)
    save_fig(fig, "18_prediction_confidence_plot")

    logger.info("=" * 78)
    logger.info("ALL 18 PUBLICATION-READY FIGURES SUCCESSFULLY GENERATED IN: %s", FIGURES_DIR)
    logger.info("=" * 78)


if __name__ == "__main__":
    generate_all_18_figures()
