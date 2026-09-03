"""
explainability.py
-----------------
Explainability and feature importance analysis for Model 1 V3.
Computes:
  1. Tree Model Feature Importance (Gain / Split)
  2. SHAP (SHapley Additive exPlanations) values on test set
  3. Permutation Feature Importance on out-of-sample hold-out
"""

import os
import sys
import json
import pickle
import logging
import warnings
import numpy as np
import pandas as pd
import shap
from sklearn.inspection import permutation_importance

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Explainability-V3")

from config_v3 import MODELS_DIR, RESULTS_DIR, FEATURES_V3, TARGET_FORECAST, RANDOM_SEED
from data_pipeline import get_chronological_splits

def compute_explainability():
    logger.info("Computing Model 1 V3 explainability suite (SHAP, Permutation, Tree Importance) ...")

    # 1. Load dataset & model artifacts
    corpus_cache = os.path.join(RESULTS_DIR, "_day_ahead_corpus.pkl")
    with open(corpus_cache, "rb") as f:
        df = pickle.load(f)

    train_df, val_df, test_df = get_chronological_splits(df)

    with open(os.path.join(MODELS_DIR, "best_model_power_v3.pkl"), "rb") as f:
        model = pickle.load(f)
    with open(os.path.join(MODELS_DIR, "scaler_power_v3.pkl"), "rb") as f:
        scaler = pickle.load(f)

    X_te_raw = test_df[FEATURES_V3].values
    y_test   = test_df[TARGET_FORECAST].values
    X_test_s = scaler.transform(X_te_raw)

    X_tr_raw = train_df[FEATURES_V3].values
    y_train  = train_df[TARGET_FORECAST].values
    X_train_s= scaler.transform(X_tr_raw)

    # ── 1. Model Native Feature Importance ─────────────────────────────────────
    logger.info("--> Extracting native tree feature importance ...")
    if hasattr(model, "get_feature_importance"):
        importances = model.get_feature_importance()
    elif hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "feature_importance"):
        importances = model.feature_importance(importance_type="gain")
    else:
        importances = np.zeros(len(FEATURES_V3))

    fi_df = pd.DataFrame({
        "feature": FEATURES_V3,
        "importance": importances,
    }).sort_values("importance", ascending=False)
    fi_df.to_csv(os.path.join(RESULTS_DIR, "feature_importance.csv"), index=False)
    logger.info("Top 10 Tree Features:\n%s", fi_df.head(10).to_string(index=False))

    from sklearn.base import BaseEstimator, RegressorMixin

    class ScaledModelWrapper(BaseEstimator, RegressorMixin):
        def __init__(self, m, sc):
            self.m = m
            self.sc = sc
            self._estimator_type = "regressor"
        def predict(self, X_raw):
            X_s = self.sc.transform(X_raw)
            return self.m.predict(X_s)
        def fit(self, X, y):
            return self

    wrapper = ScaledModelWrapper(model, scaler)
    # Subsample test set for faster permutation scoring if large
    n_sample = min(1500, len(X_te_raw))
    idx = np.random.RandomState(RANDOM_SEED).choice(len(X_te_raw), n_sample, replace=False)
    perm = permutation_importance(
        wrapper, X_te_raw[idx], y_test[idx],
        scoring="neg_root_mean_squared_error",
        n_repeats=5,
        random_state=RANDOM_SEED,
        n_jobs=-1,
    )

    perm_df = pd.DataFrame({
        "feature": FEATURES_V3,
        "importance_mean": perm.importances_mean,
        "importance_std": perm.importances_std,
    }).sort_values("importance_mean", ascending=False)
    perm_df.to_csv(os.path.join(RESULTS_DIR, "permutation_importance.csv"), index=False)
    logger.info("Top 10 Permutation Features:\n%s", perm_df.head(10).to_string(index=False))

    # ── 3. SHAP Values ─────────────────────────────────────────────────────────
    logger.info("--> Calculating TreeSHAP values on test set ...")
    shap_sample_n = min(1000, len(X_test_s))
    shap_idx = np.random.RandomState(RANDOM_SEED).choice(len(X_test_s), shap_sample_n, replace=False)
    X_shap_s = X_test_s[shap_idx]
    X_shap_raw = test_df[FEATURES_V3].iloc[shap_idx]

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_shap_s)
    except Exception as exc:
        logger.warning("TreeExplainer failed (%s); falling back to Explainer ...", exc)
        explainer = shap.Explainer(model.predict, X_train_s[:200])
        shap_obj = explainer(X_shap_s)
        shap_values = shap_obj.values

    # Save SHAP cache for plotting
    with open(os.path.join(RESULTS_DIR, "_shap_cache.pkl"), "wb") as f:
        pickle.dump({
            "shap_values": shap_values,
            "X_sample_raw": X_shap_raw,
            "feature_names": FEATURES_V3,
        }, f, protocol=4)
    logger.info("SHAP values computed and cached successfully.")


if __name__ == "__main__":
    compute_explainability()
