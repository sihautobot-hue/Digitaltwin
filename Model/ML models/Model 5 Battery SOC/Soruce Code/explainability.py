"""
explainability.py
-----------------
Step 8: Model Interpretability via TreeSHAP and Feature Importance Analysis.
Model 5 (Version 3): Day-Ahead Battery State of Charge Forecasting
"""

import os
import logging
from typing import Dict, Any, Tuple

import numpy as np
import pandas as pd
import shap

from config import FEATURE_COLUMNS, RESULTS_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("Explainability-M5V3")


def compute_shap_and_feature_importance(
    model: Any,
    test_df: pd.DataFrame,
    sample_size: int = 600
) -> Tuple[pd.DataFrame, pd.DataFrame, np.ndarray, pd.DataFrame]:
    """
    Compute TreeSHAP values and extract native feature importance rankings.
    """
    X_test = test_df[FEATURE_COLUMNS]
    
    # Subsample for SHAP computation
    np.random.seed(42)
    if len(X_test) > sample_size:
        sample_idx = np.random.choice(len(X_test), size=sample_size, replace=False)
        X_sample = X_test.iloc[sample_idx].copy()
    else:
        X_sample = X_test.copy()

    logger.info("Computing TreeSHAP values on %d test samples ...", len(X_sample))
    
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X_sample)
        if isinstance(shap_values, list):
            shap_vals_mat = np.array(shap_values[0])
        else:
            shap_vals_mat = np.array(shap_values)
    except Exception as e:
        logger.warning("TreeExplainer fallback to generic Explainer: %s", e)
        explainer = shap.Explainer(model.predict, X_sample)
        shap_exp = explainer(X_sample)
        shap_vals_mat = shap_exp.values

    # Mean absolute SHAP importance
    mean_abs_shap = np.mean(np.abs(shap_vals_mat), axis=0)
    shap_importance_df = pd.DataFrame({
        "Feature": FEATURE_COLUMNS,
        "Mean_Abs_SHAP": mean_abs_shap,
    }).sort_values("Mean_Abs_SHAP", ascending=False).reset_index(drop=True)

    # Native Feature Importance
    if hasattr(model, "feature_importances_"):
        native_fi = model.feature_importances_
        if np.sum(native_fi) > 0:
            native_fi = native_fi / np.sum(native_fi) * 100.0
    elif hasattr(model, "get_feature_importance"):
        native_fi = model.get_feature_importance()
        if np.sum(native_fi) > 0:
            native_fi = native_fi / np.sum(native_fi) * 100.0
    else:
        native_fi = mean_abs_shap / np.sum(mean_abs_shap) * 100.0

    native_fi_df = pd.DataFrame({
        "Feature": FEATURE_COLUMNS,
        "Importance_Pct": native_fi,
    }).sort_values("Importance_Pct", ascending=False).reset_index(drop=True)

    print("\n" + "=" * 80)
    print("STEP 8: TOP 15 PREDICTORS BY MEAN ABSOLUTE SHAP AND NATIVE TREE GAIN")
    print("=" * 80)
    merged_top = shap_importance_df.head(15).merge(native_fi_df, on="Feature")
    print(merged_top.to_string(index=False))
    print("=" * 80 + "\n")

    return shap_importance_df, native_fi_df, shap_vals_mat, X_sample
