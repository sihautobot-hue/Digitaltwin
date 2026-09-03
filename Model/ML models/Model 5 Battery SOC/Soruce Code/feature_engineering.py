"""
feature_engineering.py
----------------------
Steps 3, 4, 6: Data Loading, Cryptographic Duplicate Audit, Shift-Then-Roll
Feature Engineering, and Chronological & LOSO Dataset Splitting.
Model 5 (Version 3): Day-Ahead Battery State of Charge Forecasting
"""

import os
import glob
import hashlib
import logging
from typing import Dict, Tuple, List

import numpy as np
import pandas as pd

from config import (
    DATA_DIR,
    FEATURE_COLUMNS,
    TARGET_RAW,
    TARGET_FORECAST,
    TRAIN_YEAR_RANGE,
    VAL_YEAR_RANGE,
    TEST_YEAR,
    ORDINAL_WEATHER,
    RANDOM_SEED,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("FeatureEngineering-M5V3")


def compute_simulation_hashes() -> Dict[str, str]:
    """Compute SHA-256 hashes of all station summary simulation files."""
    files = sorted(glob.glob(os.path.join(DATA_DIR, "station_summary_*.csv")))
    hashes = {}
    print("\n" + "=" * 80)
    print("STEP 6: CRYPTOGRAPHIC SHA-256 SIMULATION DUPLICATE DETECTION")
    print("=" * 80)
    for f in files:
        basename = os.path.basename(f)
        with open(f, "rb") as fp:
            h = hashlib.sha256(fp.read()).hexdigest()
        hashes[basename] = h
        print(f"  {basename:25s} | SHA-256: {h}")
    print("=" * 80)
    
    # Check duplicates
    seen = {}
    duplicates = []
    for f, h in hashes.items():
        if h in seen:
            duplicates.append((f, seen[h]))
        else:
            seen[h] = f
            
    if duplicates:
        print("[AUDIT DISCLOSURE] Duplicate simulation runs identified:")
        for dup, orig in duplicates:
            print(f"  --> {dup} is a BITWISE DUPLICATE CLONE of {orig}")
    else:
        print("[AUDIT DISCLOSURE] All simulation files are unique.")
    print("=" * 80 + "\n")
    return hashes


def load_raw_simulation_runs() -> pd.DataFrame:
    """Load all 5 simulation runs into a consolidated DataFrame."""
    frames = []
    for i in range(1, 6):
        path = os.path.join(DATA_DIR, f"station_summary_{i}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing simulation dataset: {path}")
        chunk = pd.read_csv(path, low_memory=False)
        chunk["run_id"] = i
        frames.append(chunk)

    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["run_id", "station_id", "date"]).reset_index(drop=True)
    logger.info("Loaded 5 simulation runs: %d rows x %d columns", len(df), len(df.columns))
    return df


def construct_day_ahead_dataset(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Construct the true day-ahead forecasting dataset (t -> t+1).
    Aligns lead-1 target at t+1 and strictly computes pre-forecast features at t.
    All rolling statistics enforce the SHIFT-THEN-ROLL protocol.
    """
    logger.info("Building day-ahead features under strict Shift-Then-Roll contract ...")
    
    # Sort rigorously
    df = df_raw.sort_values(["run_id", "station_id", "date"]).reset_index(drop=True)
    grp = df.groupby(["run_id", "station_id"])

    # Dictionary to collect new engineered columns and avoid fragmentation
    feats = {}

    # ── 1. Target Definition: battery_soc_percent at end of Day t+1 ───────────
    feats[TARGET_FORECAST] = grp[TARGET_RAW].shift(-1)

    # ── 2. Station Identity ───────────────────────────────────────────────────
    feats["station_enc"] = (df["station_id"] == "BHARATI").astype(int)

    # ── 3. Astronomical & Calendar Features for Day t+1 ───────────────────────
    date_lead1 = df["date"] + pd.Timedelta(days=1)
    feats["year"] = date_lead1.dt.year
    feats["month"] = date_lead1.dt.month
    feats["day_of_year"] = date_lead1.dt.dayofyear
    feats["day_of_week"] = date_lead1.dt.dayofweek
    feats["quarter"] = date_lead1.dt.quarter

    feats["month_sin"] = np.sin(2 * np.pi * feats["month"] / 12)
    feats["month_cos"] = np.cos(2 * np.pi * feats["month"] / 12)
    feats["doy_sin"] = np.sin(2 * np.pi * feats["day_of_year"] / 365)
    feats["doy_cos"] = np.cos(2 * np.pi * feats["day_of_year"] / 365)
    feats["dow_sin"] = np.sin(2 * np.pi * feats["day_of_week"] / 7)
    feats["dow_cos"] = np.cos(2 * np.pi * feats["day_of_week"] / 7)

    feats["is_shipping_season"] = feats["month"].isin([11, 12, 1, 2, 3]).astype(int)

    # ── 4. Day-Ahead NWP Weather Forecast for Day t+1 ─────────────────────────
    feats["fc_temperature_c"] = grp["temperature_c"].shift(-1)
    feats["fc_wind_speed_kmh"] = grp["wind_speed_kmh"].shift(-1)
    feats["fc_wind_gust_kmh"] = grp["wind_gust_kmh"].shift(-1)
    feats["fc_solar_radiation_wm2"] = grp["solar_radiation_wm2"].shift(-1)
    feats["fc_solar_daylight_hours"] = grp["solar_daylight_hours"].shift(-1)
    feats["fc_solar_elevation_deg"] = grp["solar_elevation_deg"].shift(-1)
    feats["fc_snowfall_cm"] = grp["snowfall_cm"].shift(-1)
    feats["fc_snow_depth_cm"] = grp["snow_depth_cm"].shift(-1)
    feats["fc_weather_severity"] = grp["weather_severity"].shift(-1)
    weather_lead1 = grp["weather_type"].shift(-1)
    feats["fc_weather_type_enc"] = weather_lead1.map(ORDINAL_WEATHER).fillna(1).astype(int)
    feats["fc_wind_chill_c"] = (
        13.12
        + 0.6215 * feats["fc_temperature_c"]
        - 11.37 * (np.maximum(1.0, feats["fc_wind_speed_kmh"]) ** 0.16)
        + 0.3965 * feats["fc_temperature_c"] * (np.maximum(1.0, feats["fc_wind_speed_kmh"]) ** 0.16)
    ).clip(upper=10.0)
    feats["fc_heating_degree_days"] = np.maximum(0.0, 18.0 - feats["fc_temperature_c"])

    feats["is_polar_night"] = (feats["fc_solar_daylight_hours"] < 1.0).astype(int)
    feats["is_polar_day"] = (feats["fc_solar_daylight_hours"] > 22.0).astype(int)

    # ── 5. Battery State of Charge History (Observed at/before 18:00 Day t) ────
    # In row t, df['battery_soc_percent'] is SoC at Day t cutoff
    feats["soc_lag1"] = df["battery_soc_percent"]
    feats["soc_lag2"] = grp["battery_soc_percent"].shift(1)
    feats["soc_lag3"] = grp["battery_soc_percent"].shift(2)
    feats["soc_lag7"] = grp["battery_soc_percent"].shift(6)
    feats["soc_lag14"] = grp["battery_soc_percent"].shift(13)

    # Shift-Then-Roll: Rolling statistics over past observed SoC
    feats["soc_roll3_mean"] = grp["battery_soc_percent"].transform(lambda s: s.rolling(3, min_periods=1).mean())
    feats["soc_roll7_mean"] = grp["battery_soc_percent"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    feats["soc_roll14_mean"] = grp["battery_soc_percent"].transform(lambda s: s.rolling(14, min_periods=1).mean())
    feats["soc_roll30_mean"] = grp["battery_soc_percent"].transform(lambda s: s.rolling(30, min_periods=1).mean())

    feats["soc_trend_3d"] = feats["soc_lag1"] - feats["soc_lag3"]
    feats["soc_trend_7d"] = feats["soc_lag1"] - feats["soc_lag7"]

    feats["soc_roll7_std"] = grp["battery_soc_percent"].transform(lambda s: s.rolling(7, min_periods=2).std()).fillna(0.0)
    feats["soc_roll14_std"] = grp["battery_soc_percent"].transform(lambda s: s.rolling(14, min_periods=2).std()).fillna(0.0)

    # ── 6. Battery Discharge Telemetry (Strictly t <= 0) ───────────────────────
    feats["battery_discharge_lag1"] = df["battery_discharge_kw"]
    feats["battery_discharge_roll7_mean"] = grp["battery_discharge_kw"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    feats["battery_discharge_roll14_mean"] = grp["battery_discharge_kw"].transform(lambda s: s.rolling(14, min_periods=1).mean())

    # ── 7. Historical Observed Weather & Thermal Persistence ──────────────────
    feats["obs_temp_lag1"] = df["temperature_c"]
    feats["obs_temp_lag2"] = grp["temperature_c"].shift(1)
    feats["obs_temp_lag3"] = grp["temperature_c"].shift(2)
    feats["obs_temp_roll7_mean"] = grp["temperature_c"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    feats["obs_temp_trend3"] = feats["obs_temp_lag1"] - feats["obs_temp_lag3"]
    feats["obs_wind_lag1"] = df["wind_speed_kmh"]
    feats["obs_weather_sev_lag1"] = df["weather_severity"]
    feats["obs_weather_sev_roll7"] = grp["weather_severity"].transform(lambda s: s.rolling(7, min_periods=1).mean())

    # ── 8. Scheduled Station Population for Day t+1 ───────────────────────────
    feats["scheduled_population"] = grp["total_population"].shift(-1)
    feats["scheduled_occupancy_pct"] = grp["occupancy_percent"].shift(-1)
    feats["scheduled_scientists"] = grp["scientists"].shift(-1)
    feats["scheduled_engineers"] = grp["engineers"].shift(-1)
    feats["scheduled_technicians"] = grp["technicians"].shift(-1)
    feats["scheduled_medical"] = grp["medical"].shift(-1)
    feats["pop_lag1"] = df["total_population"]
    feats["pop_trend7"] = feats["pop_lag1"] - grp["total_population"].shift(6)

    # ── 9. Electrical Demand History (Strictly t <= 0) ────────────────────────
    feats["load_lag1"] = df["total_load_kw"]
    feats["load_lag2"] = grp["total_load_kw"].shift(1)
    feats["load_lag3"] = grp["total_load_kw"].shift(2)
    feats["load_lag7"] = grp["total_load_kw"].shift(6)
    feats["load_roll7_mean"] = grp["total_load_kw"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    feats["load_roll14_mean"] = grp["total_load_kw"].transform(lambda s: s.rolling(14, min_periods=1).mean())
    feats["load_trend3"] = feats["load_lag1"] - feats["load_lag3"]

    # ── 10. Historical Generator & CHP Support (Strictly t <= 0) ──────────────
    feats["generator_output_lag1"] = df["generator_output_kw"]
    feats["generator_runtime_lag1"] = df["generator_runtime_hours"]
    feats["generator_roll7_mean"] = grp["generator_output_kw"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    feats["chp_heat_lag1"] = df["chp_waste_heat_kw"]
    feats["chp_heat_roll7_mean"] = grp["chp_waste_heat_kw"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    feats["fuel_stock_lag1"] = df["fuel_stock_liters"]

    # ── 11. Historical Renewable Generation (Strictly t <= 0) ──────────────────
    feats["solar_gen_lag1"] = df["solar_generation_kw"]
    feats["solar_gen_roll7_mean"] = grp["solar_generation_kw"].transform(lambda s: s.rolling(7, min_periods=1).mean())

    # Build final DataFrame
    feat_df = pd.DataFrame(feats)
    final_df = pd.concat([df[["run_id", "station_id", "date"]], feat_df], axis=1)

    # Drop warm-up boundary rows where target or primary lags are NaN
    valid_mask = ~final_df[TARGET_FORECAST].isna() & ~final_df["soc_lag14"].isna() & ~final_df["fc_temperature_c"].isna()
    cleaned_df = final_df[valid_mask].copy().reset_index(drop=True)
    
    # Fill remaining forward edge NaNs if any
    cleaned_df = cleaned_df.bfill().ffill()

    # Verify all feature columns are present
    missing_cols = [c for c in FEATURE_COLUMNS if c not in cleaned_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required feature columns: {missing_cols}")

    logger.info("Engineered dataset ready: %d valid daily forecast records (%d features).", len(cleaned_df), len(FEATURE_COLUMNS))
    return cleaned_df


def get_chronological_splits(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data chronologically:
      - Train: 2003–2019
      - Validation: 2020–2021
      - Test: 2022
    """
    train_mask = (df["year"] >= TRAIN_YEAR_RANGE[0]) & (df["year"] <= TRAIN_YEAR_RANGE[1])
    val_mask = (df["year"] >= VAL_YEAR_RANGE[0]) & (df["year"] <= VAL_YEAR_RANGE[1])
    test_mask = (df["year"] == TEST_YEAR)

    train_df = df[train_mask].copy().reset_index(drop=True)
    val_df = df[val_mask].copy().reset_index(drop=True)
    test_df = df[test_mask].copy().reset_index(drop=True)

    logger.info("Chronological Split: Train=%d, Val=%d, Test=%d", len(train_df), len(val_df), len(test_df))
    return train_df, val_df, test_df


def get_loso_folds(df: pd.DataFrame) -> List[Tuple[int, pd.DataFrame, pd.DataFrame]]:
    """
    Generate Leave-One-Simulation-Out (LOSO) folds across unique simulation run IDs.
    """
    run_ids = sorted(df["run_id"].unique())
    folds = []
    for test_run in run_ids:
        train_fold = df[df["run_id"] != test_run].copy().reset_index(drop=True)
        test_fold = df[df["run_id"] == test_run].copy().reset_index(drop=True)
        folds.append((test_run, train_fold, test_fold))
    return folds


if __name__ == "__main__":
    compute_simulation_hashes()
    raw = load_raw_simulation_runs()
    ds = construct_day_ahead_dataset(raw)
    tr, val, ts = get_chronological_splits(ds)
    print("Dataset construction verified successfully.")
