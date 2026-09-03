# train_models.py -- Model 6 V3: 4-Algorithm Training Pipeline
# Winner selected exclusively by Validation PR-AUC (tie-break: Val F1).
import os, json, logging, pickle, warnings
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, average_precision_score, brier_score_loss)
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier
from catboost import CatBoostClassifier
from sklearn.ensemble import RandomForestClassifier
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("TrainModels-Model6-V3")
from config import MODELS_DIR, RESULTS_DIR, TARGET_NAME, FEATURE_COLS, MODEL_PARAMS, RANDOM_SEED
from feature_engineering import load_raw_corpus, get_chronological_splits, get_loso_splits

ALGO_MAP = {
    "XGBoost":      lambda p: XGBClassifier(**p),
    "LightGBM":     lambda p: LGBMClassifier(**p),
    "CatBoost":     lambda p: CatBoostClassifier(**p),
    "RandomForest": lambda p: RandomForestClassifier(**p),
}

def prep_xy(df, feat_cols):
    present = [c for c in feat_cols if c in df.columns]
    X = df[present].fillna(0).values
    y = df[TARGET_NAME].fillna(0).astype(int).values
    return X, y

def predict_proba_safe(model, X):
    try:
        return model.predict_proba(X)[:, 1]
    except Exception:
        return model.predict(X).astype(float)

def score_split(model, X, y, scaler, tag):
    Xs = scaler.transform(X)
    p  = predict_proba_safe(model, Xs)
    yp = (p >= 0.5).astype(int)
    acc  = accuracy_score(y, yp)
    prec = precision_score(y, yp, zero_division=0)
    rec  = recall_score(y, yp, zero_division=0)
    f1   = f1_score(y, yp, zero_division=0)
    try:
        auc = roc_auc_score(y, p) if len(np.unique(y)) > 1 else 0.5
    except Exception:
        auc = 0.5
    try:
        pr_auc = average_precision_score(y, p) if len(np.unique(y)) > 1 else float(np.mean(y))
    except Exception:
        pr_auc = float(np.mean(y))
    brier = brier_score_loss(y, p)
    logger.info("[%s [%s]] Acc=%.4f Prec=%.4f Rec=%.4f F1=%.4f ROC-AUC=%.4f PR-AUC=%.4f Brier=%.4f",
        tag, "EVAL", acc, prec, rec, f1, auc, pr_auc, brier)
    return dict(accuracy=round(float(acc),4), precision=round(float(prec),4), recall=round(float(rec),4),
        f1=round(float(f1),4), roc_auc=round(float(auc),4), pr_auc=round(float(pr_auc),4),
        brier_score=round(float(brier),4))

def train_and_select():
    logger.info("=" * 60)
    logger.info("MODEL 6 V3 -- 4-ALGORITHM TRAINING PIPELINE")
    logger.info("=" * 60)
    corpus = load_raw_corpus(deduplicate=False)
    train_df, val_df, test_df = get_chronological_splits(corpus)
    X_tr, y_tr = prep_xy(train_df, FEATURE_COLS)
    X_va, y_va = prep_xy(val_df,   FEATURE_COLS)
    X_te, y_te = prep_xy(test_df,  FEATURE_COLS)
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_va_s = scaler.transform(X_va)
    X_te_s = scaler.transform(X_te)
    best_model, best_name, best_pr_auc, best_f1 = None, None, -1, -1
    benchmark = {}
    for algo_name, builder in ALGO_MAP.items():
        logger.info("-" * 40)
        logger.info("Training: %s", algo_name)
        model = builder(MODEL_PARAMS[algo_name])
        if algo_name == "XGBoost":
            model.fit(X_tr_s, y_tr, eval_set=[(X_va_s, y_va)], verbose=False)
        elif algo_name == "LightGBM":
            model.fit(X_tr_s, y_tr, eval_set=[(X_va_s, y_va)])
        else:
            model.fit(X_tr_s, y_tr)
        tr_m  = score_split(model, X_tr, y_tr, scaler, f"{algo_name}[TRAIN]")
        val_m = score_split(model, X_va, y_va, scaler, f"{algo_name}[VAL]")
        te_m  = score_split(model, X_te, y_te, scaler, f"{algo_name}[TEST]")
        benchmark[algo_name] = {"train": tr_m, "val": val_m, "test": te_m}
        vpr = val_m["pr_auc"]; vf1 = val_m["f1"]
        if vpr > best_pr_auc or (vpr == best_pr_auc and vf1 > best_f1):
            best_pr_auc = vpr; best_f1 = vf1
            best_model = model; best_name = algo_name
    logger.info("=" * 60)
    logger.info("WINNER (by Val PR-AUC): %s (Val PR-AUC=%.4f, F1=%.4f)", best_name, best_pr_auc, best_f1)
    logger.info("=" * 60)
    # LOSO cross-validation
    loso_5fold  = run_loso(corpus, ALGO_MAP[best_name](MODEL_PARAMS[best_name]), scaler, deduplicated=False)
    loso_dedup  = run_loso(corpus, ALGO_MAP[best_name](MODEL_PARAMS[best_name]), scaler, deduplicated=True)
    # Save artifacts
    feat_present = [c for c in FEATURE_COLS if c in train_df.columns]
    with open(os.path.join(MODELS_DIR, "best_model_v3.pkl"), "wb") as f:
        pickle.dump(best_model, f)
    with open(os.path.join(MODELS_DIR, "scaler_v3.pkl"), "wb") as f:
        pickle.dump(scaler, f)
    with open(os.path.join(MODELS_DIR, "feature_columns_v3.json"), "w") as f:
        json.dump(feat_present, f, indent=2)
    results = {
        "winner": best_name,
        "val_pr_auc_winner": best_pr_auc,
        "benchmark": benchmark,
        "loso_5fold": loso_5fold,
        "loso_dedup_3fold": loso_dedup,
    }
    with open(os.path.join(RESULTS_DIR, "benchmark_results_v3.json"), "w") as f:
        json.dump(results, f, indent=2)
    logger.info("Artifacts saved to %s and %s", MODELS_DIR, RESULTS_DIR)
    return best_model, scaler, feat_present, benchmark, loso_5fold, loso_dedup, best_name

def run_loso(corpus, model_template, ref_scaler, deduplicated=False):
    tag = "Dedup" if deduplicated else "Naive"
    results = []
    for fold_id, tr, te in get_loso_splits(corpus, deduplicated=deduplicated):
        X_tr, y_tr = prep_xy(tr, FEATURE_COLS)
        X_te, y_te = prep_xy(te, FEATURE_COLS)
        sc = StandardScaler()
        X_tr_s = sc.fit_transform(X_tr)
        X_te_s = sc.transform(X_te)
        from sklearn.base import clone
        try:
            m = clone(model_template)
        except Exception:
            import copy; m = copy.deepcopy(model_template)
        m.fit(X_tr_s, y_tr)
        p = predict_proba_safe(m, X_te_s)
        yp = (p >= 0.5).astype(int)
        acc  = accuracy_score(y_te, yp)
        f1   = f1_score(y_te, yp, zero_division=0)
        try:
            auc = roc_auc_score(y_te, p) if len(np.unique(y_te)) > 1 else 0.5
        except Exception:
            auc = 0.5
        try:
            pr_auc = average_precision_score(y_te, p) if len(np.unique(y_te)) > 1 else float(np.mean(y_te))
        except Exception:
            pr_auc = float(np.mean(y_te))
        logger.info("[LOSO-%s Run-%d] Acc=%.4f F1=%.4f ROC-AUC=%.4f PR-AUC=%.4f", tag, fold_id, acc, f1, auc, pr_auc)
        results.append(dict(run_id=int(fold_id), accuracy=round(float(acc),4), f1=round(float(f1),4),
            roc_auc=round(float(auc),4), pr_auc=round(float(pr_auc),4)))
    pr_aucs = [r["pr_auc"] for r in results]
    f1s     = [r["f1"]     for r in results]
    logger.info("LOSO-%s Mean PR-AUC=%.4f +/-%.4f | Mean F1=%.4f", tag, np.mean(pr_aucs), np.std(pr_aucs), np.mean(f1s))
    return results

if __name__ == "__main__":
    train_and_select()
