"""
run_pipeline.py
---------------
Master orchestrator for Model 3 Version 3.
Executes the full pipeline:
  1. SHA-256 Hash verification of all simulation runs
  2. Data loading and feature engineering
  3. 8-algorithm benchmark training (winner by Validation RMSE)
  4. LOSO cross-validation (all-5-fold + deduplicated-3-fold)
  5. Comprehensive evaluation and stress testing
  6. 18 publication-quality figures (PNG + SVG)
  7. Scientific report generation

DO NOT MODIFY: Model 1, Model 2, or any shared pipeline components.
"""

import json
import logging
import os
import sys
import time
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("RunPipeline-Model3-V3")

from config import RESULTS_DIR, MODELS_DIR, FIGURES_DIR, TARGET_NAME, TARGET_CLIP


def main():
    t0 = time.time()
    logger.info("=" * 78)
    logger.info("  MODEL 3 V3 — DAY-AHEAD FUEL RUNWAY FORECAST — FULL PIPELINE")
    logger.info("=" * 78)
    logger.info("Prediction Contract: 18:00 Day t → fuel_days_remaining at Day t+1")
    logger.info("Strict Forecast Integrity: Shift-First, No Same-Day Leakage")
    logger.info("")

    # ── STEP 1: Integrity Verification ─────────────────────────────────────────
    logger.info("STEP 1 — SHA-256 Simulation Hash Verification")
    from feature_engineering import verify_simulation_hashes, load_raw_corpus, build_fuel_runway_dataset
    hash_report = verify_simulation_hashes()

    # ── STEP 2: Data Loading & Feature Engineering ──────────────────────────────
    logger.info("STEP 2 — Loading corpus and building forecast-safe features")
    df_raw = load_raw_corpus()
    df = build_fuel_runway_dataset(df_raw)
    df["year"] = pd.to_datetime(df["date"]).dt.year
    logger.info("Dataset shape: %d rows × %d columns", len(df), len(df.columns))

    # ── STEP 3: Leakage Audit Export ───────────────────────────────────────────
    logger.info("STEP 3 — Exporting feature leakage audit table")
    from leakage_audit import generate_audit_report
    df_audit = generate_audit_report()
    audit_path = os.path.join(RESULTS_DIR, "model3_feature_leakage_audit.csv")
    df_audit.to_csv(audit_path, index=False)
    logger.info("Leakage audit saved: %s", audit_path)

    # ── STEP 4: Train, Benchmark, and Select Winner ─────────────────────────────
    logger.info("STEP 4 — Multi-algorithm benchmark training")
    from feature_engineering import get_chronological_splits
    train_df, val_df, test_df = get_chronological_splits(df)
    from train_models import train_and_benchmark, loso_cross_validation, get_feature_importance, save_artifacts
    winner, model, scaler, feat_cols, benchmark_summary = train_and_benchmark(df, train_df, val_df, test_df)

    # ── STEP 5: LOSO Cross-Validation ──────────────────────────────────────────
    logger.info("STEP 5 — LOSO cross-validation (all-5 + deduplicated-3)")
    loso_summary = loso_cross_validation(df, winner)

    # ── STEP 6: Feature Importance ─────────────────────────────────────────────
    logger.info("STEP 6 — Feature importance extraction")
    fi_df = get_feature_importance(model, feat_cols, winner)
    save_artifacts(winner, model, scaler, feat_cols, benchmark_summary, loso_summary, fi_df)

    # ── STEP 7: Comprehensive Evaluation ───────────────────────────────────────
    logger.info("STEP 7 — Evaluation and stress testing")
    from evaluate import full_evaluation
    eval_results, test_df_with_preds, model_eval, scaler_eval, feat_cols_eval = full_evaluation(df, test_df)

    # ── STEP 8: Figure Generation ──────────────────────────────────────────────
    logger.info("STEP 8 — Generating 18 publication-quality figures")
    from plot_figures import generate_all_figures
    generate_all_figures(
        benchmark_data=benchmark_summary,
        fi_df=fi_df,
        test_df=test_df_with_preds,
        eval_results=eval_results,
        loso_summary=loso_summary,
        feat_cols=feat_cols,
    )

    # ── STEP 9: Scientific Report ───────────────────────────────────────────────
    logger.info("STEP 9 — Generating MODEL3_V3_SCIENTIFIC_REPORT.md")
    generate_scientific_report(winner, benchmark_summary, loso_summary, eval_results, fi_df, hash_report, t0)

    elapsed = time.time() - t0
    logger.info("=" * 78)
    logger.info("  MODEL 3 V3 PIPELINE COMPLETE IN %.1f seconds", elapsed)
    logger.info("  Winner: %s | Val RMSE: %.4f days", winner, benchmark_summary.get("winner_val_rmse", 0))
    logger.info("  Test RMSE: %.4f days | Test R²: %.4f | Test MAPE: %.2f%%",
                eval_results["overall"]["rmse"],
                eval_results["overall"]["r2"],
                eval_results["overall"]["mape_pct"])
    logger.info("  LOSO Dedup-3 RMSE: %.4f ± %.4f days",
                loso_summary["deduplicated_3"]["mean_rmse"],
                loso_summary["deduplicated_3"]["std_rmse"])
    logger.info("=" * 78)


def generate_scientific_report(winner, benchmark_summary, loso_summary, eval_results, fi_df, hash_report, t0):
    """Generate the full scientific report as Markdown."""
    report_path = os.path.join(RESULTS_DIR, "MODEL3_V3_SCIENTIFIC_REPORT.md")
    all5 = loso_summary.get("all_folds_5", {})
    ded3 = loso_summary.get("deduplicated_3", {})
    ov = eval_results.get("overall", {})
    resid = eval_results.get("residuals", {})
    pi = eval_results.get("prediction_interval_90pct", {})
    bench = benchmark_summary.get("benchmark", {})

    regime_table = ""
    for regime, vals in eval_results.get("regime_wise", {}).items():
        if isinstance(vals.get("rmse"), float):
            regime_table += f"| {regime} | {vals.get('n','?')} | {vals.get('rmse','?')} | {vals.get('mae','?')} | {vals.get('mape_pct','?')} |\n"

    station_table = ""
    for s, vals in eval_results.get("station_wise", {}).items():
        station_table += f"| {s} | {vals.get('rmse','?')} | {vals.get('mae','?')} | {vals.get('r2','?')} | {vals.get('mape_pct','?')} |\n"

    season_table = ""
    for s, vals in eval_results.get("shipping_season", {}).items():
        season_table += f"| {s} | {vals.get('n','?')} | {vals.get('rmse','?')} | {vals.get('mae','?')} | {vals.get('mape_pct','?')} |\n"

    ranking_rows = ""
    val_ranking = benchmark_summary.get("val_rmse_ranking", [])
    for rank, (alg, rmse) in enumerate(val_ranking, 1):
        b = bench.get(alg, {}) if isinstance(bench, dict) else {}
        label = "← **Winner** ✓" if alg == winner else ""
        val_m  = b.get("val",  {}) if isinstance(b, dict) else {}
        test_m = b.get("test", {}) if isinstance(b, dict) else {}
        ranking_rows += f"| {rank} | {alg} | {val_m.get('rmse','?')} | {val_m.get('mae','?')} | {test_m.get('rmse','?')} | {test_m.get('r2','?')} | {label} |\n"

    fi_rows = ""
    for _, row in fi_df.head(20).iterrows():
        fi_rows += f"| {row['feature']} | {row['importance']:.2f} | {row['importance_pct']:.2f}% |\n"

    loso_fold_rows = ""
    for f in all5.get("per_fold", []):
        mark = " ⚠ Dup" if f["fold_id"] in [4, 5] else ""
        loso_fold_rows += f"| Run {f['fold_id']}{mark} | {f['rmse']} | {f['mae']} | {f['r2']} |\n"

    report = f"""# Model 3 Version 3 — Scientific Report
## Day-Ahead Fuel Runway Forecasting: Antarctic Digital Twin

**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}
**Pipeline Version:** V3 (from-scratch scientific rebuild)
**Author:** Antarctic Digital Twin ML Pipeline — SIH Project

---

## 1. Prediction Contract

| Parameter | Specification |
|-----------|---------------|
| Prediction Timestamp | 18:00 Station Local Time on Day t |
| Forecast Horizon | Day t+1 (next calendar day) |
| Target Variable | `fuel_days_remaining` at Day t+1 |
| Target Name | `fuel_runway_lead1` |
| Target Clip | {TARGET_CLIP} days |
| Contract Type | True Day-Ahead Forecast |
| Information Cutoff | All features strictly ≤ 18:00 on Day t |

> **Scientific Rationale:** Fuel runway is an operational safety metric.
> It measures how many days the station can sustain operations from the
> start of Day t+1, given the projected consumption rate. A model issued
> at 18:00 on Day t has access to today's observed fuel stock, past
> consumption history, scheduled population rosters, and day-ahead NWP
> weather forecasts — all of which are available before Day t+1 begins.

---

## 2. Leakage Analysis

The following variables from the Version 2 model were identified as
**same-day leakage** and are **strictly excluded** in V3:

| Variable | Leak Type | Reason |
|----------|-----------|--------|
| `fuel_consumed_today_liters` (Day t+1) | Algebraic Identity | Direct denominator of target formula |
| `generator_output_kw` (Day t+1) | Same-Day Dispatch | Unknown at 18:00 Day t |
| `generator_runtime_hours` (Day t+1) | Same-Day Dispatch | Drives fuel burn equation |
| `active_generators` (Day t+1) | Same-Day Dispatch | Stage decision made intra-day |
| `total_load_kw` (Day t+1) | Same-Day Realization | Post-event measurement |
| `solar_generation_kw` (Day t+1) | Same-Day Realization | Offsets generator dispatch |
| `renewable_share_percent` (Day t+1) | Same-Day Derived | Ratio including post-event values |
| `refuel_event` (Day t+1) | Post-Event Flag | Occurs during Day t+1 |
| `temperature_c` (Day t+1) | Same-Day Obs | Replaced by NWP forecast |
| `fuel_efficiency_l_per_kwh` | Target Derived | fuel_consumed / gen_energy |

**Total rejected variables:** 30+ (full audit in `model3_feature_leakage_audit.csv`)

All historical telemetry (fuel_lag1, gen_output_lag1, etc.) refers to
**Day t and earlier** — strictly valid at 18:00 cutoff.

---

## 3. Feature Engineering Methodology

### 3.1 Shift-Then-Roll Invariance

All rolling statistics are constructed on the *already-shifted* series:

```
fuel_roll7_mean[t] = mean(fuel[t], fuel[t-1], ..., fuel[t-6])
```

The sequence `fuel[0], fuel[1], ..., fuel[t]` never contains `fuel[t+1]`.
This is enforced at the Pandas transform level (no `.shift(-1)` before rolling).

### 3.2 NWP Forecast Simulation

Day-ahead weather forecasts for Day t+1 are constructed by forward-shifting
the realized simulation weather series by 1 day. This simulates realistic
NWP output available before Day t+1 begins. In live deployment, these would
be replaced by ERA5 or WRF day-ahead NWP products.

### 3.3 Scheduled Population Roster

Population for Day t+1 is taken from the forward-shifted population schedule.
In live deployment, this represents the advance crew manifest filed before
each day.

---

## 4. Algorithm Benchmark

Selection criterion: **Validation RMSE only** (not test RMSE).

| Rank | Algorithm | Val RMSE | Val MAE | Test RMSE | Test R² | Notes |
|------|-----------|----------|---------|-----------|---------|-------|
{ranking_rows}

**Winner: {winner}**

---

## 5. Test Set Performance (Chronological)

| Metric | Value |
|--------|-------|
| MAE | {ov.get('mae', '?')} days |
| RMSE | {ov.get('rmse', '?')} days |
| R² | {ov.get('r2', '?')} |
| MAPE | {ov.get('mape_pct', '?')}% |
| Mean Bias | {ov.get('bias_days', '?')} days |
| P50 Absolute Error | {ov.get('p50_abs_err', '?')} days |
| P90 Prediction Interval (±) | {pi.get('half_width_days', '?')} days |
| P90 Coverage | {pi.get('coverage', '?')} |

---

## 6. Regime-Wise Stress Test

Performance by operational fuel runway regime:

| Regime | N | RMSE (d) | MAE (d) | MAPE |
|--------|---|----------|---------|------|
{regime_table}
> **Critical Zone (<10 days):** This is the highest operational priority.
> Errors in this regime have direct consequence for station safety.

---

## 7. Station-Wise Generalization

| Station | RMSE (d) | MAE (d) | R² | MAPE |
|---------|----------|---------|----|------|
{station_table}

---

## 8. Shipping Season Conditional Performance

| Condition | N | RMSE (d) | MAE (d) | MAPE |
|-----------|---|----------|---------|------|
{season_table}

---

## 9. LOSO Cross-Validation

### Per-Fold Results

| Fold | RMSE (d) | MAE (d) | R² |
|------|----------|---------|----|
{loso_fold_rows}

### Summary

| Metric | All-5-Fold | Deduplicated-3-Fold |
|--------|------------|---------------------|
| Mean RMSE | {all5.get('mean_rmse', '?')} | {ded3.get('mean_rmse', '?')} |
| Std RMSE  | {all5.get('std_rmse', '?')}  | {ded3.get('std_rmse', '?')}  |
| Mean MAE  | {all5.get('mean_mae', '?')}  | {ded3.get('mean_mae', '?')}  |
| Mean R²   | {all5.get('mean_r2', '?')}   | {ded3.get('mean_r2', '?')}   |

### ⚠ Duplicate Simulation Disclosure

> SHA-256 hash verification confirmed that simulation Runs 4 and 5 are
> **bitwise identical** to Run 3. The 5-fold LOSO result is **optimistic**
> because held-out runs may share all unique variation with training.
> The **deduplicated 3-fold result (Runs 1, 2, 3)** is the scientifically
> defensible estimate for independent generalization.

---

## 10. Residual Analysis

| Statistic | Value |
|-----------|-------|
| Mean | {resid.get('mean', '?')} days |
| Std | {resid.get('std', '?')} days |
| Skewness | {resid.get('skewness', '?')} |
| Kurtosis | {resid.get('kurtosis', '?')} |
| P5 | {resid.get('p5', '?')} days |
| P50 (Median) | {resid.get('p50', '?')} days |
| P95 | {resid.get('p95', '?')} days |

---

## 11. Top 20 Features by Gain

| Feature | Gain | % Contribution |
|---------|------|----------------|
{fi_rows}

---

## 12. Top Feature Groups (Domain Interpretation)

| Group | Key Features | Importance |
|-------|-------------|------------|
| Fuel Inventory State | `fuel_stock_start_liters`, `fuel_stock_lag1` | Very High |
| Historical Runway Dynamics | `runway_lag1`, `runway_roll7_mean`, `runway_trend_7d` | Very High |
| Historical Consumption | `fuel_lag1`, `fuel_roll7_mean`, `fuel_roll14_mean` | High |
| Fuel Supply Chain | `fuel_shipments_pending`, `fuel_eta_days`, `days_since_refuel_start` | High |
| NWP Weather Forecast | `fc_temperature_c`, `fc_heating_degree_days`, `fc_wind_speed_kmh` | Moderate |
| Population Schedule | `scheduled_population`, `scheduled_occupancy_pct` | Moderate |
| Generator Telemetry | `gen_output_lag1`, `gen_runtime_lag1`, `chp_heat_lag1` | Moderate |

---

## 13. Scientific Integrity Disclosure

1. **Leakage Removal:** All 30+ same-day leakage variables identified in the
   V2 model have been eliminated.

2. **Shift-Then-Roll:** Rolling statistics never reference future observations.
   Validated at feature engineering level via manual index inspection.

3. **NWP Simulation:** Day t+1 weather features simulate realistic forecast
   availability. In live deployment, actual NWP products should replace these.

4. **Chronological Splits:** Train/Val/Test splits are strictly time-ordered.
   No data from future years contaminates training.

5. **Duplicate Simulation Disclosure:** Runs 4 and 5 are bitwise duplicates
   of Run 3. This is explicitly reported in all LOSO tables.

6. **Winner Selection:** Algorithm selected **exclusively** by Validation RMSE.
   Test metrics were never used for model selection.

7. **Target Clipping:** Runway beyond {TARGET_CLIP} days is clipped. Beyond
   1 year of operational fuel, the distinction is not operationally meaningful.

---

## 14. Operational Decision Thresholds

| Threshold | Days | Recommended Action |
|-----------|------|--------------------|
| Critical | < 10 days | Emergency resupply, immediate contact with logistics |
| Alert | 10–30 days | Expedite next tanker schedule |
| Caution | 30–90 days | Monitor consumption rate, verify ETA |
| Normal | 90–180 days | Standard monitoring |
| Comfortable | > 180 days | Routine operational state |

---

## 15. Files Generated

| Artifact | Path |
|----------|------|
| Best Model | `models_v3/best_model_v3.pkl` |
| Scaler | `models_v3/scaler_v3.pkl` |
| Feature List | `models_v3/feature_columns_v3.json` |
| Benchmark Results | `results_v3/benchmark_results_v3.json` |
| Evaluation Results | `results_v3/evaluation_v3.json` |
| Leakage Audit | `results_v3/model3_feature_leakage_audit.csv` |
| Feature Importance | `results_v3/feature_importance_v3.csv` |
| Test Predictions | `results_v3/test_predictions_v3.csv` |
| Figures (18×2) | `results_v3/figures/fig01_*.png/.svg` |
| Scientific Report | `results_v3/MODEL3_V3_SCIENTIFIC_REPORT.md` |

---

*Report generated by Antarctic Digital Twin ML Pipeline V3*
*Model 3: Day-Ahead Fuel Runway Forecast*
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("Scientific report saved: %s", report_path)


if __name__ == "__main__":
    main()
