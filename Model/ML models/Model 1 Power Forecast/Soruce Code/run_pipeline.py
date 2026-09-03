"""
run_pipeline.py
---------------
Master reproducible pipeline for Model 1 (Version 3: Day-Ahead Power Forecast).
Runs:
  1. Cryptographic hash and duplicate dataset verification
  2. Scientific leakage audit
  3. Strict shift-then-roll feature engineering
  4. Multi-algorithm benchmarking and winner selection
  5. Leave-One-Simulation-Out (LOSO) cross-validation
  6. Detailed evaluation across seasonal, monthly, storm, and transition regimes
  7. Generation of all 13 publication-quality figures (PNG and SVG)
"""

import os
import sys
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Pipeline-V3")

from leakage_audit import generate_audit_report
from feature_engineering import verify_simulation_file_integrity, load_raw_corpus, build_forecast_dataset
from train_models import run_chronological_benchmark, run_loso_cross_validation
from evaluate import run_full_evaluation
from plot_figures import generate_all_13_figures
from config import RESULTS_DIR, MODELS_DIR, FEATURE_COLUMNS
import pickle
import json

def main():
    t_start = time.time()
    logger.info("=" * 80)
    logger.info("  STARTING MODEL 1 (VERSION 3) END-TO-END SCIENTIFIC REBUILD")
    logger.info("=" * 80)

    # 1. Integrity check & hash verification
    logger.info(">>> STEP 1: Cryptographic Hash & Simulation Integrity Audit")
    hashes = verify_simulation_file_integrity()

    # 2. Leakage Audit
    logger.info(">>> STEP 2: Scientific Leakage Audit & Feature Classification")
    df_audit = generate_audit_report()
    audit_csv = os.path.join(RESULTS_DIR, "feature_leakage_audit.csv")
    df_audit.to_csv(audit_csv, index=False)
    logger.info("Saved complete feature audit table to: %s", audit_csv)

    # 3. Feature Engineering
    logger.info(">>> STEP 3: Shift-Then-Roll Day-Ahead Feature Engineering")
    df_raw = load_raw_corpus()
    df_clean = build_forecast_dataset(df_raw)

    cache_path = os.path.join(RESULTS_DIR, "_day_ahead_corpus.pkl")
    with open(cache_path, "wb") as f:
        pickle.dump(df_clean, f, protocol=4)

    # 4. Multi-model Training & Benchmark Selection
    logger.info(">>> STEP 4: Multi-Algorithm Benchmark on Chronological Split")
    benchmarks, best_model, scaler, winner_name = run_chronological_benchmark(df_clean)

    # Save artifacts
    model_file = os.path.join(MODELS_DIR, "best_model_power_v3.pkl")
    scaler_file = os.path.join(MODELS_DIR, "scaler_power_v3.pkl")
    feats_file = os.path.join(MODELS_DIR, "features_power_v3.json")
    metrics_file = os.path.join(RESULTS_DIR, "chronological_metrics_v3.json")

    with open(model_file, "wb") as f: pickle.dump(best_model, f)
    with open(scaler_file, "wb") as f: pickle.dump(scaler, f)
    with open(feats_file, "w") as f: json.dump(FEATURE_COLUMNS, f, indent=2)
    with open(metrics_file, "w") as f: json.dump(benchmarks, f, indent=2)

    with open(os.path.join(RESULTS_DIR, "winner_name.txt"), "w") as f:
        f.write(winner_name)

    # 5. LOSO Validation
    logger.info(">>> STEP 5: Leave-One-Simulation-Out (LOSO) Cross-Validation")
    loso_results = run_loso_cross_validation(df_clean, winner_name)

    # 6. Comprehensive Evaluation & SHAP
    logger.info(">>> STEP 6: In-Depth Regime Evaluation & SHAP Analysis")
    eval_results = run_full_evaluation()

    # 7. Generate all 13 Figures in PNG & SVG
    logger.info(">>> STEP 7: Publication Visualizations (13 Figures in PNG & SVG)")
    generate_all_13_figures()

    total_time = time.time() - t_start
    logger.info("=" * 80)
    logger.info("  MODEL 1 V3 PIPELINE COMPLETED IN %.1f SECONDS", total_time)
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
