"""
plot_figures.py
---------------
Publication-quality figure generation for Model 3 V3.
Generates 18 figures in both PNG (300 DPI) and SVG format.
All plots use a consistent, accessible Antarctic Digital Twin aesthetic.

Figures Produced:
  01. Algorithm Benchmark — Validation RMSE comparison
  02. Feature Importance — Top 30 features (Gain)
  03. Actual vs Predicted — Test set scatter plot
  04. Temporal Forecast Trace — Time series of predictions vs actuals
  05. Residual Distribution — KDE + histogram
  06. Residual vs Predicted — Heteroscedasticity check
  07. QQ Plot — Residual normality assessment
  08. Autocorrelation of Residuals — Lag-40 ACF
  09. Regime-Wise Error Decomposition — By fuel runway level
  10. Year-Wise Test Performance — RMSE bar chart by year
  11. Station-Wise Generalization — Maitri vs Bharati comparison
  12. Shipping Season vs Off-Season — Conditional error
  13. Prediction Interval Plot — 90% PI on test set excerpt
  14. Fuel Runway Trajectory — 90-day animated window
  15. Forecast Bias Distribution — Signed error histogram
  16. Rolling 30-Day RMSE — Error drift over time
  17. LOSO Stability — All-5-fold vs deduplicated-3-fold comparison
  18. Feature Correlation with Target — Top features Pearson r
"""

import json
import logging
import os
import warnings
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
import pandas as pd
from matplotlib.ticker import MaxNLocator
from scipy import stats
# statsmodels not required — ACF computed via numpy

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("PlotFigures-Model3-V3")

from config import FIGURES_DIR, RESULTS_DIR, TARGET_NAME, TARGET_CLIP

# ── Aesthetic Constants ────────────────────────────────────────────────────────
PALETTE = {
    "primary":   "#1E6EAF",
    "secondary": "#F05B28",
    "accent":    "#2AAA7E",
    "warn":      "#FFC107",
    "critical":  "#D62728",
    "neutral":   "#7F7F7F",
    "bg":        "#F8F9FA",
    "dark":      "#1A1A2E",
}
DPI = 300
FIGSIZE_STANDARD = (12, 6)
FIGSIZE_WIDE     = (16, 6)
FIGSIZE_TALL     = (10, 10)

plt.rcParams.update({
    "font.family":    "DejaVu Sans",
    "font.size":      11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.facecolor":   "#F8F9FA",
    "figure.facecolor": "#FFFFFF",
    "grid.alpha": 0.3,
    "grid.linestyle": "--",
    "legend.framealpha": 0.9,
    "legend.fontsize":   10,
})

FIG_REGISTRY = []


def _save(fig: plt.Figure, name: str, tight: bool = True) -> None:
    base = os.path.join(FIGURES_DIR, name)
    if tight:
        fig.tight_layout()
    fig.savefig(base + ".png", dpi=DPI, bbox_inches="tight")
    fig.savefig(base + ".svg",          bbox_inches="tight")
    plt.close(fig)
    FIG_REGISTRY.append(name)
    logger.info("Saved figure: %s.{png,svg}", name)


def _title_tag(title: str) -> str:
    return f"Model 3 V3 — {title}"


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 01: Algorithm Benchmark — Validation RMSE
# ─────────────────────────────────────────────────────────────────────────────
def fig01_algorithm_benchmark(benchmark_data: Dict) -> None:
    val_ranking = benchmark_data.get("benchmark", {}).get("benchmark", {})
    if not val_ranking:
        val_ranking = benchmark_data.get("benchmark", {})

    names, val_rmse, test_rmse = [], [], []
    for alg, m in val_ranking.items():
        names.append(alg)
        val_rmse.append(m.get("val", {}).get("rmse", np.nan))
        test_rmse.append(m.get("test", {}).get("rmse", np.nan))

    if not names:
        logger.warning("No benchmark data for Fig 01. Skipping.")
        return

    fig, ax = plt.subplots(figsize=FIGSIZE_STANDARD)
    x = np.arange(len(names))
    w = 0.35
    bars_val  = ax.bar(x - w/2, val_rmse,  w, label="Validation RMSE", color=PALETTE["primary"], alpha=0.87)
    bars_test = ax.bar(x + w/2, test_rmse, w, label="Test RMSE",       color=PALETTE["secondary"], alpha=0.87)

    winner = benchmark_data.get("benchmark", {}).get("winner", "")
    if winner in names:
        wi = names.index(winner)
        ax.axvline(x=wi, color=PALETTE["accent"], ls="--", lw=1.5, alpha=0.6)
        ax.annotate("Winner ✓", xy=(wi, max(v for v in val_rmse if np.isfinite(v)) * 0.95),
                    color=PALETTE["accent"], fontweight="bold", ha="center", fontsize=10)

    ax.set_xticks(x)
    ax.set_xticklabels(names, rotation=25, ha="right")
    ax.set_ylabel("RMSE (days)")
    ax.set_title(_title_tag("Algorithm Benchmark — Day-Ahead Fuel Runway RMSE"))
    ax.legend()
    ax.grid(axis="y")
    _save(fig, "fig01_algorithm_benchmark")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 02: Feature Importance — Top 30
# ─────────────────────────────────────────────────────────────────────────────
def fig02_feature_importance(fi_df: pd.DataFrame) -> None:
    top = fi_df.head(30).copy()
    fig, ax = plt.subplots(figsize=(12, 9))
    colors = [PALETTE["primary"] if i < 5 else PALETTE["secondary"] if i < 15 else PALETTE["neutral"]
              for i in range(len(top))]
    ax.barh(top["feature"][::-1], top["importance"][::-1], color=colors[::-1], alpha=0.85)
    ax.set_xlabel("Feature Importance (Gain)")
    ax.set_title(_title_tag("Top 30 Features by Gain — Fuel Runway Forecast"))
    ax.grid(axis="x")
    _save(fig, "fig02_feature_importance")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 03: Actual vs Predicted Scatter
# ─────────────────────────────────────────────────────────────────────────────
def fig03_actual_vs_predicted(test_df: pd.DataFrame) -> None:
    y_true = test_df[TARGET_NAME].values
    y_pred = test_df["y_pred"].values
    fig, ax = plt.subplots(figsize=(9, 9))
    sc = ax.scatter(y_true, y_pred, alpha=0.25, s=8, c=PALETTE["primary"])
    lims = [min(y_true.min(), y_pred.min()), max(y_true.max(), y_pred.max())]
    ax.plot(lims, lims, "k--", lw=1.5, label="Perfect forecast")
    # Regression line
    m_coef, b_coef = np.polyfit(y_true, y_pred, 1)
    ax.plot(np.sort(y_true), m_coef * np.sort(y_true) + b_coef,
            color=PALETTE["secondary"], lw=1.5, label=f"Fit: slope={m_coef:.3f}")
    ax.set_xlabel("Actual Fuel Runway (days)")
    ax.set_ylabel("Predicted Fuel Runway (days)")
    ax.set_title(_title_tag("Actual vs Predicted — Test Set"))
    ax.legend()
    ax.grid()
    _save(fig, "fig03_actual_vs_predicted")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 04: Temporal Forecast Trace (first station, 365 days of test set)
# ─────────────────────────────────────────────────────────────────────────────
def fig04_temporal_trace(test_df: pd.DataFrame) -> None:
    df_s = test_df.sort_values("date")
    if "station_id" in df_s.columns:
        df_s = df_s[df_s["station_id"] == df_s["station_id"].unique()[0]]
    df_s = df_s.head(365)
    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    ax.plot(pd.to_datetime(df_s["date"]), df_s[TARGET_NAME], label="Actual", color=PALETTE["primary"], lw=1.5)
    ax.plot(pd.to_datetime(df_s["date"]), df_s["y_pred"],   label="Predicted", color=PALETTE["secondary"], lw=1.5, ls="--")
    ax.fill_between(pd.to_datetime(df_s["date"]),
                    df_s[TARGET_NAME] - df_s["abs_residual"],
                    df_s[TARGET_NAME] + df_s["abs_residual"],
                    alpha=0.15, color=PALETTE["secondary"], label="±Error")
    ax.axhline(30, color=PALETTE["warn"], ls=":", lw=1.5, label="30-day alert threshold")
    ax.axhline(10, color=PALETTE["critical"], ls=":", lw=1.5, label="10-day critical threshold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Fuel Runway (days)")
    ax.set_title(_title_tag("Day-Ahead Fuel Runway Forecast — Temporal Trace"))
    ax.legend(ncol=2, fontsize=9)
    ax.grid()
    _save(fig, "fig04_temporal_trace")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 05: Residual Distribution
# ─────────────────────────────────────────────────────────────────────────────
def fig05_residual_distribution(test_df: pd.DataFrame) -> None:
    resids = test_df["residual"].values
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)
    ax1.hist(resids, bins=60, color=PALETTE["primary"], alpha=0.8, density=True, edgecolor="white")
    xr = np.linspace(resids.min(), resids.max(), 300)
    ax1.plot(xr, stats.norm.pdf(xr, resids.mean(), resids.std()),
             color=PALETTE["secondary"], lw=2, label="Normal fit")
    ax1.axvline(0, color="black", lw=1.5, ls="--")
    ax1.set_xlabel("Residual (days)")
    ax1.set_ylabel("Density")
    ax1.set_title("Residual Histogram + Normal Fit")
    ax1.legend()

    ax2.hist(test_df["abs_residual"].values, bins=60, color=PALETTE["accent"], alpha=0.8, density=True, edgecolor="white")
    ax2.set_xlabel("Absolute Residual (days)")
    ax2.set_ylabel("Density")
    ax2.set_title("Absolute Error Distribution")
    ax2.grid()

    fig.suptitle(_title_tag("Residual Distribution Analysis"), fontweight="bold")
    _save(fig, "fig05_residual_distribution")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 06: Residual vs Predicted (Heteroscedasticity)
# ─────────────────────────────────────────────────────────────────────────────
def fig06_residual_vs_predicted(test_df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(test_df["y_pred"], test_df["residual"], alpha=0.2, s=8, c=PALETTE["primary"])
    ax.axhline(0, color="black", lw=1.5, ls="--")
    ax.set_xlabel("Predicted Fuel Runway (days)")
    ax.set_ylabel("Residual (days)")
    ax.set_title(_title_tag("Residual vs Predicted — Heteroscedasticity Check"))
    ax.grid()
    _save(fig, "fig06_residual_vs_predicted")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 07: QQ Plot
# ─────────────────────────────────────────────────────────────────────────────
def fig07_qq_plot(test_df: pd.DataFrame) -> None:
    resids = test_df["residual"].values
    fig, ax = plt.subplots(figsize=(8, 8))
    (osm, osr), (slope, intercept, r) = stats.probplot(resids, dist="norm")
    ax.plot(osm, osr, "o", alpha=0.3, ms=3, color=PALETTE["primary"])
    ax.plot(osm, slope * np.array(osm) + intercept, color=PALETTE["secondary"], lw=2)
    ax.set_xlabel("Theoretical Quantiles")
    ax.set_ylabel("Sample Quantiles")
    ax.set_title(_title_tag(f"Q-Q Plot — Residuals (r={r:.4f})"))
    ax.grid()
    _save(fig, "fig07_qq_plot")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 08: Autocorrelation of Residuals
# ─────────────────────────────────────────────────────────────────────────────
def _acf_numpy(x: np.ndarray, nlags: int = 40) -> np.ndarray:
    """Compute normalized autocorrelation up to nlags using numpy."""
    x = x - x.mean()
    n = len(x)
    var = np.dot(x, x)
    result = np.array(
        [np.dot(x[:n - k], x[k:]) / var for k in range(nlags + 1)]
    )
    return result


def fig08_residual_acf(test_df: pd.DataFrame) -> None:
    resids = test_df.sort_values("date")["residual"].values
    nlags = 40
    acf_vals = _acf_numpy(resids, nlags)
    lags = np.arange(nlags + 1)
    ci = 1.96 / np.sqrt(len(resids))  # 95% confidence interval band

    fig, ax = plt.subplots(figsize=FIGSIZE_STANDARD)
    ax.bar(lags, acf_vals, color=PALETTE["primary"], alpha=0.75, width=0.6)
    ax.axhline(0,    color="black",            lw=1.0)
    ax.axhline( ci,  color=PALETTE["secondary"], lw=1.2, ls="--", label=f"95% CI (±{ci:.3f})")
    ax.axhline(-ci,  color=PALETTE["secondary"], lw=1.2, ls="--")
    ax.set_xlabel("Lag (days)")
    ax.set_ylabel("ACF")
    ax.set_title(_title_tag("Residual Autocorrelation Function (Lag 0–40)"))
    ax.legend(fontsize=9)
    ax.grid(axis="y")
    _save(fig, "fig08_residual_acf")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 09: Regime-Wise Error Decomposition
# ─────────────────────────────────────────────────────────────────────────────
def fig09_regime_decomposition(eval_results: Dict) -> None:
    regime_data = eval_results.get("regime_wise", {})
    if not regime_data:
        return
    labels = [k for k, v in regime_data.items() if isinstance(v.get("rmse"), float)]
    rmse_vals = [regime_data[k]["rmse"] for k in labels]
    mae_vals  = [regime_data[k]["mae"]  for k in labels]
    n_vals    = [regime_data[k].get("n", 0) for k in labels]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIGSIZE_WIDE)
    colors = [PALETTE["critical"], PALETTE["warn"], PALETTE["accent"], PALETTE["primary"], PALETTE["neutral"]][:len(labels)]
    ax1.bar(labels, rmse_vals, color=colors, alpha=0.85)
    ax1.set_xticklabels(labels, rotation=20, ha="right")
    ax1.set_ylabel("RMSE (days)")
    ax1.set_title("RMSE by Fuel Runway Regime")
    for i, (r, n) in enumerate(zip(rmse_vals, n_vals)):
        ax1.annotate(f"n={n}", xy=(i, r), ha="center", va="bottom", fontsize=9)

    ax2.bar(labels, mae_vals, color=colors, alpha=0.85)
    ax2.set_xticklabels(labels, rotation=20, ha="right")
    ax2.set_ylabel("MAE (days)")
    ax2.set_title("MAE by Fuel Runway Regime")

    fig.suptitle(_title_tag("Regime-Wise Error Decomposition"), fontweight="bold")
    _save(fig, "fig09_regime_decomposition")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 10: Year-Wise Test Performance
# ─────────────────────────────────────────────────────────────────────────────
def fig10_year_wise_performance(eval_results: Dict) -> None:
    yw = eval_results.get("year_wise", {})
    if not yw:
        return
    years = sorted(yw.keys())
    rmse_vals = [yw[y]["rmse"] for y in years]
    mae_vals  = [yw[y]["mae"]  for y in years]
    r2_vals   = [yw[y]["r2"]   for y in years]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    for ax, vals, lbl, color in zip(
        axes,
        [rmse_vals, mae_vals, r2_vals],
        ["RMSE (days)", "MAE (days)", "R²"],
        [PALETTE["primary"], PALETTE["secondary"], PALETTE["accent"]],
    ):
        ax.bar([str(y) for y in years], vals, color=color, alpha=0.85)
        ax.set_xlabel("Test Year")
        ax.set_ylabel(lbl)
        ax.set_title(f"Year-Wise {lbl}")
        ax.grid(axis="y")

    fig.suptitle(_title_tag("Year-Wise Test Performance"), fontweight="bold")
    _save(fig, "fig10_year_wise_performance")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 11: Station-Wise Generalization
# ─────────────────────────────────────────────────────────────────────────────
def fig11_station_generalization(eval_results: Dict) -> None:
    sw = eval_results.get("station_wise", {})
    if not sw:
        return
    stations = list(sw.keys())
    fig, axes = plt.subplots(1, 3, figsize=(14, 5))
    metrics = ["rmse", "mae", "r2"]
    labels_m = ["RMSE (days)", "MAE (days)", "R²"]
    colors = [PALETTE["primary"], PALETTE["secondary"]]
    for ax, met, lbl in zip(axes, metrics, labels_m):
        vals = [sw[s][met] for s in stations]
        ax.bar(stations, vals, color=colors[:len(stations)], alpha=0.85)
        ax.set_ylabel(lbl)
        ax.set_title(f"Station-Wise {lbl}")
        ax.grid(axis="y")
    fig.suptitle(_title_tag("Station-Wise Generalization"), fontweight="bold")
    _save(fig, "fig11_station_generalization")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 12: Shipping Season vs Off-Season
# ─────────────────────────────────────────────────────────────────────────────
def fig12_shipping_season(eval_results: Dict) -> None:
    ss = eval_results.get("shipping_season", {})
    if not ss:
        return
    categories = list(ss.keys())
    rmse_v = [ss[k]["rmse"] for k in categories]
    mae_v  = [ss[k]["mae"]  for k in categories]
    n_v    = [ss[k].get("n", 0) for k in categories]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=FIGSIZE_STANDARD)
    colors = [PALETTE["accent"], PALETTE["warn"]][:len(categories)]
    ax1.bar(categories, rmse_v, color=colors, alpha=0.85)
    ax1.set_ylabel("RMSE (days)")
    ax1.set_title("Shipping Season vs Off-Season RMSE")
    for i, (r, n) in enumerate(zip(rmse_v, n_v)):
        ax1.annotate(f"n={n}", xy=(i, r), ha="center", va="bottom", fontsize=9)
    ax2.bar(categories, mae_v, color=colors, alpha=0.85)
    ax2.set_ylabel("MAE (days)")
    ax2.set_title("Shipping Season vs Off-Season MAE")
    fig.suptitle(_title_tag("Shipping Season Conditional Performance"), fontweight="bold")
    _save(fig, "fig12_shipping_season")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 13: 90% Prediction Interval Plot
# ─────────────────────────────────────────────────────────────────────────────
def fig13_prediction_interval(test_df: pd.DataFrame, eval_results: Dict) -> None:
    pi = eval_results.get("prediction_interval_90pct", {})
    half_width = pi.get("half_width_days", 10.0)
    df_s = test_df.sort_values("date").head(180)
    dates = pd.to_datetime(df_s["date"])
    y_pred = df_s["y_pred"].values
    y_true = df_s[TARGET_NAME].values

    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    ax.fill_between(dates, y_pred - half_width, y_pred + half_width,
                    alpha=0.25, color=PALETTE["primary"], label=f"90% PI (±{half_width:.1f}d)")
    ax.plot(dates, y_true,  label="Actual", color=PALETTE["primary"], lw=1.5)
    ax.plot(dates, y_pred,  label="Predicted", color=PALETTE["secondary"], lw=1.5, ls="--")
    ax.axhline(30, color=PALETTE["warn"],     ls=":", lw=1.2, label="30-day alert")
    ax.axhline(10, color=PALETTE["critical"], ls=":", lw=1.2, label="10-day critical")
    ax.set_xlabel("Date")
    ax.set_ylabel("Fuel Runway (days)")
    ax.set_title(_title_tag("90% Prediction Interval — 180-Day Test Window"))
    ax.legend(ncol=2, fontsize=9)
    ax.grid()
    _save(fig, "fig13_prediction_interval")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 14: Fuel Runway Trajectory (90-day zoomed window)
# ─────────────────────────────────────────────────────────────────────────────
def fig14_fuel_trajectory(test_df: pd.DataFrame) -> None:
    df_s = test_df.sort_values("date")
    # Find a window with interesting dynamics (near-critical or refuel event)
    df_low = df_s[df_s[TARGET_NAME] < 60].head(1)
    if len(df_low):
        center_date = pd.to_datetime(df_low["date"].iloc[0])
        start_date = center_date - pd.Timedelta(days=30)
        df_w = df_s[(pd.to_datetime(df_s["date"]) >= start_date) &
                    (pd.to_datetime(df_s["date"]) <= start_date + pd.Timedelta(days=90))]
    else:
        df_w = df_s.head(90)

    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    ax.plot(pd.to_datetime(df_w["date"]), df_w[TARGET_NAME], label="Actual", color=PALETTE["primary"], lw=2)
    ax.plot(pd.to_datetime(df_w["date"]), df_w["y_pred"],   label="Predicted", color=PALETTE["secondary"], lw=2, ls="--")
    ax.axhspan(0, 10,  alpha=0.08, color=PALETTE["critical"], label="Critical Zone (<10d)")
    ax.axhspan(10, 30, alpha=0.08, color=PALETTE["warn"],     label="Alert Zone (10–30d)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Fuel Runway (days)")
    ax.set_title(_title_tag("Fuel Runway Trajectory — 90-Day Operational Window"))
    ax.legend()
    ax.grid()
    _save(fig, "fig14_fuel_trajectory")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 15: Forecast Bias Distribution
# ─────────────────────────────────────────────────────────────────────────────
def fig15_bias_distribution(test_df: pd.DataFrame) -> None:
    resids = test_df["residual"].values
    fig, ax = plt.subplots(figsize=(10, 6))
    over_pct  = (resids > 0).mean() * 100
    under_pct = (resids < 0).mean() * 100
    pos_resids = resids[resids > 0]
    neg_resids = resids[resids < 0]
    ax.hist(pos_resids, bins=40, color=PALETTE["secondary"], alpha=0.75, label=f"Over-forecast ({over_pct:.1f}%)")
    ax.hist(neg_resids, bins=40, color=PALETTE["primary"],   alpha=0.75, label=f"Under-forecast ({under_pct:.1f}%)")
    ax.axvline(0, color="black", lw=2, ls="--")
    ax.axvline(resids.mean(), color=PALETTE["critical"], lw=1.5, ls=":", label=f"Mean bias={resids.mean():.2f}d")
    ax.set_xlabel("Residual (days)")
    ax.set_ylabel("Count")
    ax.set_title(_title_tag("Forecast Bias Distribution — Over vs Under Prediction"))
    ax.legend()
    ax.grid()
    _save(fig, "fig15_bias_distribution")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 16: Rolling 30-Day RMSE Drift
# ─────────────────────────────────────────────────────────────────────────────
def fig16_rolling_rmse(test_df: pd.DataFrame) -> None:
    df_s = test_df.sort_values("date").copy()
    df_s["squared_err"] = df_s["residual"] ** 2
    df_s["rolling_rmse"] = np.sqrt(df_s["squared_err"].rolling(30, min_periods=5).mean())

    fig, ax = plt.subplots(figsize=FIGSIZE_WIDE)
    ax.plot(pd.to_datetime(df_s["date"]), df_s["rolling_rmse"],
            color=PALETTE["primary"], lw=2, label="30-Day Rolling RMSE")
    overall_rmse = np.sqrt(df_s["squared_err"].mean())
    ax.axhline(overall_rmse, color=PALETTE["secondary"], ls="--", lw=1.5, label=f"Overall RMSE={overall_rmse:.2f}d")
    ax.set_xlabel("Date")
    ax.set_ylabel("RMSE (days)")
    ax.set_title(_title_tag("Rolling 30-Day RMSE — Error Stability Over Time"))
    ax.legend()
    ax.grid()
    _save(fig, "fig16_rolling_rmse")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 17: LOSO Stability
# ─────────────────────────────────────────────────────────────────────────────
def fig17_loso_stability(loso_summary: Dict) -> None:
    all5 = loso_summary.get("all_folds_5", {})
    ded3 = loso_summary.get("deduplicated_3", {})

    fold_ids_all = [r["fold_id"] for r in all5.get("per_fold", [])]
    rmse_all     = [r["rmse"]    for r in all5.get("per_fold", [])]
    fold_ids_ded = [r["fold_id"] for r in ded3.get("per_fold", [])]
    rmse_ded     = [r["rmse"]    for r in ded3.get("per_fold", [])]

    if not fold_ids_all:
        return

    fig, ax = plt.subplots(figsize=FIGSIZE_STANDARD)
    ax.bar([f"Run {f}" for f in fold_ids_all], rmse_all, color=PALETTE["primary"], alpha=0.75, label="All 5 Folds")
    for i, f in enumerate(fold_ids_ded):
        ax.bar(f"Run {f}", rmse_ded[i], color=PALETTE["accent"], alpha=0.9)

    ax.axhline(all5.get("mean_rmse", 0), color=PALETTE["primary"], ls="--", lw=1.5,
               label=f"5-fold Mean={all5.get('mean_rmse', 0):.3f}d")
    ax.axhline(ded3.get("mean_rmse", 0), color=PALETTE["accent"], ls="--", lw=1.5,
               label=f"Dedup-3 Mean={ded3.get('mean_rmse', 0):.3f}d")
    ax.set_xlabel("Held-Out Simulation Run")
    ax.set_ylabel("RMSE (days)")
    ax.set_title(_title_tag("LOSO Stability — All-5-Fold vs Deduplicated-3-Fold"))
    ax.legend()
    ax.grid(axis="y")

    import matplotlib.patches as mpatches
    dup_patch = mpatches.Patch(color=PALETTE["warn"], alpha=0.4, label="⚠ Runs 4&5 = bitwise dup of Run 3")
    ax.add_artist(ax.legend(handles=[dup_patch], loc="lower right", fontsize=9, framealpha=0.7))
    ax.legend(loc="upper right")
    _save(fig, "fig17_loso_stability")


# ─────────────────────────────────────────────────────────────────────────────
# FIGURE 18: Feature Correlation with Target
# ─────────────────────────────────────────────────────────────────────────────
def fig18_feature_correlation(test_df: pd.DataFrame, feat_cols: List[str]) -> None:
    corr_pairs = []
    avail_feats = [f for f in feat_cols if f in test_df.columns]
    y = test_df[TARGET_NAME].values
    for feat in avail_feats:
        vals = test_df[feat].fillna(0).values
        if vals.std() > 0:
            r_val = np.corrcoef(vals, y)[0, 1]
        else:
            r_val = 0.0
        corr_pairs.append((feat, r_val))

    corr_df = pd.DataFrame(corr_pairs, columns=["feature", "pearson_r"])
    corr_df["abs_r"] = corr_df["pearson_r"].abs()
    corr_df = corr_df.sort_values("abs_r", ascending=False).head(30)

    fig, ax = plt.subplots(figsize=(12, 9))
    colors = [PALETTE["secondary"] if r > 0 else PALETTE["primary"] for r in corr_df["pearson_r"]]
    ax.barh(corr_df["feature"][::-1], corr_df["pearson_r"][::-1], color=colors[::-1], alpha=0.82)
    ax.axvline(0, color="black", lw=1.5)
    ax.set_xlabel("Pearson Correlation with fuel_runway_lead1")
    ax.set_title(_title_tag("Top 30 Feature Correlations with Fuel Runway"))
    ax.grid(axis="x")
    _save(fig, "fig18_feature_correlation")


# ─────────────────────────────────────────────────────────────────────────────
# MASTER PLOT RUNNER
# ─────────────────────────────────────────────────────────────────────────────
def generate_all_figures(
    benchmark_data: Dict,
    fi_df: pd.DataFrame,
    test_df: pd.DataFrame,
    eval_results: Dict,
    loso_summary: Dict,
    feat_cols: List[str],
) -> None:
    logger.info("Generating 18 publication-quality figures for Model 3 V3 ...")
    fig01_algorithm_benchmark(benchmark_data)
    fig02_feature_importance(fi_df)
    fig03_actual_vs_predicted(test_df)
    fig04_temporal_trace(test_df)
    fig05_residual_distribution(test_df)
    fig06_residual_vs_predicted(test_df)
    fig07_qq_plot(test_df)
    fig08_residual_acf(test_df)
    fig09_regime_decomposition(eval_results)
    fig10_year_wise_performance(eval_results)
    fig11_station_generalization(eval_results)
    fig12_shipping_season(eval_results)
    fig13_prediction_interval(test_df, eval_results)
    fig14_fuel_trajectory(test_df)
    fig15_bias_distribution(test_df)
    fig16_rolling_rmse(test_df)
    fig17_loso_stability(loso_summary)
    fig18_feature_correlation(test_df, feat_cols)

    logger.info("All 18 figures saved to: %s", FIGURES_DIR)
    logger.info("Figures generated: %s", ", ".join(FIG_REGISTRY))
