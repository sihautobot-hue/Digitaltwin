"""
run_pipeline.py
---------------
Master End-to-End Orchestrator for Model 5 (Version 3)
Day-Ahead Battery State of Charge (SoC) Forecasting

Executes all 11 scientific steps:
  1. Forecast Contract Specification
  2. Leakage Audit
  3. Feature Engineering (Shift-Then-Roll)
  4. Chronological Splitting & SHA-256 Duplicate Check
  5. Multi-Algorithm Benchmarking (XGBoost, LightGBM, Random Forest, CatBoost)
  6. Leave-One-Simulation-Out (LOSO) Cross-Validation
  7. Model Evaluation & Stress Testing (7 Regimes)
  8. Interpretability via TreeSHAP
  9. PNG Figure Generation (Exact 6 Figures)
  10. Artifact Persistence (Model, Schema, Metrics JSON)
  11. Scientific Report Compilation
"""

import os
import sys
import time
import json
import logging
import numpy as np
import pandas as pd

from config import (
    BASE_DIR,
    MODELS_DIR,
    RESULTS_DIR,
    FIGURES_DIR,
    FEATURE_COLUMNS,
    TARGET_FORECAST,
)
from leakage_audit import run_leakage_audit
from feature_engineering import (
    compute_simulation_hashes,
    load_raw_simulation_runs,
    construct_day_ahead_dataset,
    get_chronological_splits,
)
from train_models import (
    benchmark_models,
    perform_loso_validation,
    train_and_save_final_model,
)
from evaluate import perform_full_evaluation
from explainability import compute_shap_and_feature_importance
from plot_figures import generate_all_six_figures

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Pipeline-M5V3")


def run_full_pipeline():
    logger.info("Starting Model 5 (Version 3) Full Scientific Pipeline ...")
    start_time = time.time()

    # ── Step 1 & 2: Leakage Audit ─────────────────────────────────────────────
    audit_df = run_leakage_audit()

    # ── Step 6: SHA-256 Cryptographic Hash Check ──────────────────────────────
    hashes = compute_simulation_hashes()

    # ── Steps 3 & 4: Data Loading & Shift-Then-Roll Engineering ───────────────
    raw_df = load_raw_simulation_runs()
    dataset = construct_day_ahead_dataset(raw_df)
    train_df, val_df, test_df = get_chronological_splits(dataset)

    # ── Step 5: Multi-Algorithm Benchmarking (Validation-only Selection) ──────
    bdf, winner_name, winner_model, all_trained = benchmark_models(train_df, val_df, test_df)

    # ── Step 6: Leave-One-Simulation-Out (LOSO) Validation ─────────────────────
    loso_summary = perform_loso_validation(dataset, winner_name)

    # ── Step 10: Final Model Persistence ──────────────────────────────────────
    final_model, test_preds, y_test_arr = train_and_save_final_model(train_df, val_df, test_df, winner_name)

    # Compute training residuals for interval calibration
    train_preds = final_model.predict(train_df[FEATURE_COLUMNS])
    train_residuals = train_df[TARGET_FORECAST].values - train_preds

    # ── Step 7: Comprehensive Scientific Evaluation & Stress Tests ────────────
    metrics_payload, y_test, test_preds, test_residuals = perform_full_evaluation(
        final_model, train_df, test_df, winner_name
    )

    # ── Step 8: Explainability (TreeSHAP & Native Feature Importance) ──────────
    shap_df, fi_df, shap_matrix, X_sample = compute_shap_and_feature_importance(final_model, test_df, sample_size=600)

    # ── Step 9: PNG Figures Generation ────────────────────────────────────────
    fig_paths = generate_all_six_figures(
        y_test, test_preds, test_residuals, train_residuals, test_df, metrics_payload, shap_df, fi_df
    )

    elapsed = time.time() - start_time
    logger.info("Pipeline completed successfully in %.2f seconds.", elapsed)
    print("\n" + "=" * 80)
    print(f"MODEL 5 (V3) PIPELINE COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS")
    print("=" * 80)
    print(f"• Model Saved: {os.path.join(MODELS_DIR, 'best_model_battery_soc_v3.pkl')}")
    print(f"• Feature Schema: {os.path.join(MODELS_DIR, 'features_battery_soc_v3.json')}")
    print(f"• Metrics JSON: {os.path.join(RESULTS_DIR, 'metrics_battery_soc.json')}")
    print(f"• Figures (PNG): {len(fig_paths)} publication figures saved to {FIGURES_DIR}")
    print("=" * 80 + "\n")

    return {
        "benchmark_df": bdf,
        "winner_name": winner_name,
        "loso_summary": loso_summary,
        "metrics": metrics_payload,
        "shap_df": shap_df,
        "fi_df": fi_df,
        "fig_paths": fig_paths,
        "audit_df": audit_df,
    }


if __name__ == "__main__":
    run_full_pipeline()
