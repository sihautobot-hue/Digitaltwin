"""
run_pipeline.py
---------------
Master reproducible orchestration pipeline for Model 2 (Version 3: Day-Ahead Fuel Forecast).
Executes:
  1. Cryptographic hash and duplicate dataset audit
  2. Scientific leakage audit
  3. Strict shift-then-roll feature engineering
  4. Multi-algorithm benchmarking across 8 model families and winner selection
  5. Leave-One-Simulation-Out (LOSO) cross-validation with duplicate run disclosure
  6. Comprehensive scientific evaluation and stress testing across 6 regimes
  7. Generation of all 18 publication-quality figures (PNG and SVG)
"""

import os
import sys
import time
import json
import pickle
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Pipeline-Model2-V3")

from leakage_audit import generate_audit_report
from feature_engineering import verify_simulation_hashes, load_raw_corpus, build_day_ahead_fuel_dataset
from train_models import run_chronological_benchmark, run_loso_cross_validation
from evaluate import run_full_evaluation
from plot_figures import generate_all_18_figures
from config import RESULTS_DIR, MODELS_DIR, FEATURE_COLUMNS

def main():
    t0 = time.time()
    logger.info("=" * 80)
    logger.info("  STARTING MODEL 2 (VERSION 3) SCIENTIFIC REBUILD PIPELINE")
    logger.info("=" * 80)

    # 1. Cryptographic SHA256 integrity check
    logger.info(">>> STEP 1: Cryptographic Hash & Simulation Integrity Audit")
    hashes = verify_simulation_hashes()

    # 2. Leakage Audit
    logger.info(">>> STEP 2: Scientific Leakage Audit & Feature Classification")
    df_audit = generate_audit_report()
    audit_path = os.path.join(RESULTS_DIR, "model2_feature_leakage_audit.csv")
    df_audit.to_csv(audit_path, index=False)
    logger.info("Saved feature leakage audit table to: %s", audit_path)

    # 3. Shift-then-roll Feature Engineering
    logger.info(">>> STEP 3: Shift-Then-Roll Day-Ahead Feature Engineering")
    df_raw = load_raw_corpus()
    df_clean = build_day_ahead_fuel_dataset(df_raw)

    cache_path = os.path.join(RESULTS_DIR, "_day_ahead_corpus.pkl")
    with open(cache_path, "wb") as f:
        pickle.dump(df_clean, f, protocol=4)
    logger.info("Cached pre-processed dataset to: %s", cache_path)

    # 4. Multi-Algorithm Benchmarking across 8 models
    logger.info(">>> STEP 4: Multi-Algorithm Benchmark on Chronological Split")
    benchmarks, best_model, scaler, winner_name = run_chronological_benchmark(df_clean)

    # Save best model artifacts
    model_file = os.path.join(MODELS_DIR, "best_model_fuel_v3.pkl")
    scaler_file = os.path.join(MODELS_DIR, "scaler_fuel_v3.pkl")
    feats_file = os.path.join(MODELS_DIR, "features_fuel_v3.json")
    metrics_file = os.path.join(RESULTS_DIR, "chronological_metrics_v3.json")

    with open(model_file, "wb") as f: pickle.dump(best_model, f)
    with open(scaler_file, "wb") as f: pickle.dump(scaler, f)
    with open(feats_file, "w") as f: json.dump(FEATURE_COLUMNS, f, indent=2)
    with open(metrics_file, "w") as f: json.dump(benchmarks, f, indent=2)

    with open(os.path.join(RESULTS_DIR, "winner_name.txt"), "w") as f:
        f.write(winner_name)

    # 5. Leave-One-Simulation-Out Cross-Validation
    logger.info(">>> STEP 5: Leave-One-Simulation-Out (LOSO) Cross-Validation")
    loso_results = run_loso_cross_validation(df_clean, winner_name)

    # 6. Evaluation, Stress Tests, and Interpretability
    logger.info(">>> STEP 6: Scientific Stress Tests, Metrics & TreeSHAP")
    eval_results = run_full_evaluation()

    # 7. Generate all 18 publication-quality figures
    logger.info(">>> STEP 7: Publication Visualizations (18 Figures in PNG & SVG)")
    generate_all_18_figures()

    elapsed = time.time() - t0
    logger.info("=" * 80)
    logger.info("  MODEL 2 V3 PIPELINE COMPLETED IN %.1f SECONDS", elapsed)
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
