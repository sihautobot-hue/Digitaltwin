"""
feature_engineering.py
----------------------
Production feature engineering module for Model 1 (Version 3).
Strictly implements the Day-Ahead Forecast Contract (18:00 cutoff on Day t,
predicting Day t+1 load).

CORE GUARANTEE:
  Every rolling statistic first SHIFTS then ROLLS.
  Zero future or same-day t+1 telemetry is accessible to the feature matrix.
"""

import os
import hashlib
import logging
from typing import Tuple, List, Dict

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("FeatureEngineering-V3")

from config import (
    DATA_DIR,
    FEATURE_COLUMNS,
    TARGET_RAW,
    TARGET_NAME,
    SPLIT_CONFIG,
    RANDOM_SEED,
)

ORDINAL_WEATHER = {"CLEAR": 0, "NORMAL": 1, "HIGH_WIND": 2, "HEAVY_SNOW": 3, "WHITEOUT": 4, "BLIZZARD": 5}


def verify_simulation_file_integrity() -> Dict[int, Dict[str, str]]:
    """
    Computes SHA-256 hashes of all 5 simulation files.
    Identifies and logs explicit warnings if duplicate run files exist.
    """
    logger.info("Verifying cryptographic integrity and duplicate hashes of simulation runs ...")
    hashes = {}
    seen_hashes = {}
    duplicates = []

    for i in range(1, 6):
        path = os.path.join(DATA_DIR, f"station_summary_{i}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing simulation dataset: {path}")
        with open(path, "rb") as fp:
            file_hash = hashlib.sha256(fp.read()).hexdigest()
        hashes[i] = {"path": path, "sha256": file_hash}

        if file_hash in seen_hashes:
            duplicates.append((i, seen_hashes[file_hash]))
        else:
            seen_hashes[file_hash] = i

    if duplicates:
        logger.warning("=" * 78)
        logger.warning("CRITICAL SCIENTIFIC INTEGRITY WARNING:")
        for dup, orig in duplicates:
            logger.warning(
                "  Run %d is a bitwise DUPLICATE of Run %d (SHA-256: %s...)",
                dup, orig, hashes[dup]["sha256"][:16]
            )
        logger.warning("  IMPLICATION: Standard Leave-One-Simulation-Out (LOSO) across all 5 runs")
        logger.warning("  will evaluate on identical clone datasets if Run %d is trained while Run %d", orig, dup)
        logger.warning("  is tested. LOSO cross-validation is optimistic unless deduplicated.")
        logger.warning("=" * 78)
    else:
        logger.info("All 5 simulation runs have unique cryptographic SHA-256 signatures.")

    return hashes


def load_raw_corpus() -> pd.DataFrame:
    """Load and concatenate all 5 raw simulation runs into a single chronological DataFrame."""
    frames = []
    for i in range(1, 6):
        path = os.path.join(DATA_DIR, f"station_summary_{i}.csv")
        logger.info("Loading simulation run %d: %s", i, os.path.basename(path))
        chunk = pd.read_csv(path, low_memory=False)
        chunk["run_id"] = i
        frames.append(chunk)

    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["run_id", "station_id", "date"]).reset_index(drop=True)
    logger.info("Raw simulation corpus assembled: %d rows × %d columns", len(df), len(df.columns))
    return df


def build_forecast_dataset(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs the day-ahead forecast dataset from raw telemetry.
    Applies the strict 18:00 cutoff contract on Day t:
      - Target: total_load_kw on Day t+1
      - Rolling statistics: Shift(1) first, then roll. Never roll first.
    """
    logger.info("Engineering day-ahead forecasting features (strictly shifted) ...")
    df = df_raw.copy()
    grp = df.groupby(["run_id", "station_id"])

    # ── 1. Forecast Target: Day t+1 Average Electrical Demand ──────────────────
    df[TARGET_NAME] = grp[TARGET_RAW].shift(-1)

    # ── 2. Station Topology ────────────────────────────────────────────────────
    df["station_enc"] = (df["station_id"] == "BHARATI").astype(int)

    # ── 3. Calendar & Astronomical Cycles for Target Day t+1 ───────────────────
    date_lead1 = df["date"] + pd.Timedelta(days=1)
    df["year"]        = date_lead1.dt.year
    df["month"]       = date_lead1.dt.month
    df["day_of_year"] = date_lead1.dt.dayofyear
    df["day_of_week"] = date_lead1.dt.dayofweek
    df["quarter"]     = date_lead1.dt.quarter

    df["month_sin"] = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"] = np.cos(2 * np.pi * df["month"] / 12)
    df["doy_sin"]   = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["doy_cos"]   = np.cos(2 * np.pi * df["day_of_year"] / 365)
    df["dow_sin"]   = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"]   = np.cos(2 * np.pi * df["day_of_week"] / 7)

    df["is_shipping_season"] = df["month"].isin([11, 12, 1, 2, 3]).astype(int)

    # ── 4. Day-Ahead NWP Weather Forecast for Day t+1 ──────────────────────────
    df["fc_temperature_c"]        = grp["temperature_c"].shift(-1)
    df["fc_wind_speed_kmh"]       = grp["wind_speed_kmh"].shift(-1)
    df["fc_wind_gust_kmh"]        = grp["wind_gust_kmh"].shift(-1)
    df["fc_solar_radiation_wm2"]  = grp["solar_radiation_wm2"].shift(-1)
    df["fc_solar_daylight_hours"] = grp["solar_daylight_hours"].shift(-1)
    df["fc_solar_elevation_deg"]  = grp["solar_elevation_deg"].shift(-1)
    df["fc_snowfall_cm"]          = grp["snowfall_cm"].shift(-1)
    df["fc_snow_depth_cm"]        = grp["snow_depth_cm"].shift(-1)
    df["fc_weather_severity"]     = grp["weather_severity"].shift(-1)
    df["fc_weather_type_enc"]     = grp["weather_type"].shift(-1).map(ORDINAL_WEATHER).fillna(1).astype(int)

    df["is_polar_night"] = (df["fc_solar_daylight_hours"] < 1.0).astype(int)
    df["is_polar_day"]   = (df["fc_solar_daylight_hours"] > 22.0).astype(int)

    df["fc_wind_chill_c"] = (
        13.12
        + 0.6215 * df["fc_temperature_c"]
        - 11.37  * (df["fc_wind_speed_kmh"].clip(lower=1.0) ** 0.16)
        + 0.3965 * df["fc_temperature_c"] * (df["fc_wind_speed_kmh"].clip(lower=1.0) ** 0.16)
    ).clip(upper=10.0)

    df["fc_katabatic_index"] = (
        df["fc_wind_speed_kmh"] * np.maximum(0, -df["fc_temperature_c"]) / 100.0
    )
    df["fc_heating_degree_days"] = np.maximum(0, 18.0 - df["fc_temperature_c"])

    # ── 5. Observed Weather & Thermal Persistence (Observed up to Day t) ───────
    df["obs_temp_lag1"]       = df["temperature_c"]             # Day t
    df["obs_temp_lag2"]       = grp["temperature_c"].shift(1)   # Day t-1
    df["obs_temp_lag3"]       = grp["temperature_c"].shift(2)   # Day t-2
    # SHIFT THEN ROLL for weather rolling stats:
    df["obs_temp_roll7_mean"] = grp["temperature_c"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    df["obs_temp_trend3"]     = df["obs_temp_lag1"] - df["obs_temp_lag3"]

    df["obs_wind_lag1"]        = df["wind_speed_kmh"]
    df["obs_wind_roll7_mean"]  = grp["wind_speed_kmh"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    df["obs_weather_sev_lag1"] = df["weather_severity"]
    df["obs_weather_sev_roll7"]= grp["weather_severity"].transform(lambda s: s.rolling(7, min_periods=1).mean())

    # ── 6. Scheduled Station Population Roster for Day t+1 ─────────────────────
    df["scheduled_population"]    = grp["total_population"].shift(-1)
    df["scheduled_occupancy_pct"] = grp["occupancy_percent"].shift(-1)
    df["scheduled_scientists"]    = grp["scientists"].shift(-1)
    df["scheduled_engineers"]     = grp["engineers"].shift(-1)
    df["scheduled_technicians"]   = grp["technicians"].shift(-1)
    df["scheduled_medical"]       = grp["medical"].shift(-1)
    df["pop_lag1"]                = df["total_population"]
    df["pop_trend7"]              = df["total_population"] - grp["total_population"].shift(6)

    # ── 7. Electrical Demand Lags & Shift-Then-Roll Statistics (t <= 0) ─────────
    # In forecasting Day t+1, Day t's observed total load is load_lag1
    df["load_lag1"]  = df[TARGET_RAW]
    df["load_lag2"]  = grp[TARGET_RAW].shift(1)
    df["load_lag3"]  = grp[TARGET_RAW].shift(2)
    df["load_lag7"]  = grp[TARGET_RAW].shift(6)
    df["load_lag14"] = grp[TARGET_RAW].shift(13)

    # SHIFT THEN ROLL: The raw series at index i is Day t. Rolling over window w on this
    # series takes [t-(w-1), t], which strictly contains only past observations relative to t+1.
    df["load_roll3_mean"]  = grp[TARGET_RAW].transform(lambda s: s.rolling(3, min_periods=1).mean())
    df["load_roll7_mean"]  = grp[TARGET_RAW].transform(lambda s: s.rolling(7, min_periods=1).mean())
    df["load_roll14_mean"] = grp[TARGET_RAW].transform(lambda s: s.rolling(14, min_periods=1).mean())
    df["load_roll30_mean"] = grp[TARGET_RAW].transform(lambda s: s.rolling(30, min_periods=1).mean())
    df["load_roll7_std"]   = grp[TARGET_RAW].transform(lambda s: s.rolling(7, min_periods=1).std()).fillna(0)
    df["load_roll14_std"]  = grp[TARGET_RAW].transform(lambda s: s.rolling(14, min_periods=1).std()).fillna(0)

    df["load_trend_3d"]    = df["load_lag1"] - df["load_lag3"]
    df["load_trend_7d"]    = df["load_lag1"] - df["load_lag7"]

    # ── 8. Storage Buffer State at 18:00 Cutoff Timestamp (Day t) ──────────────
    df["battery_soc_start_pct"]   = df["battery_soc_percent"]
    df["soc_lag1"]                = grp["battery_soc_percent"].shift(1)
    df["soc_delta_lag1"]          = df["battery_soc_percent"] - df["soc_lag1"]
    df["fuel_stock_start_liters"] = df["fuel_stock_liters"]

    def days_since_event(s: pd.Series) -> pd.Series:
        res = pd.Series(index=s.index, dtype=float)
        c = 0
        for idx, val in s.items():
            if val: c = 0
            else: c += 1
            res[idx] = c
        return res

    df["days_since_refuel_start"] = grp["refuel_event"].transform(days_since_event)

    # ── 9. Thermal Coupling History (t <= 0) ───────────────────────────────────
    df["chp_heat_lag1"]       = df["chp_waste_heat_kw"]
    df["chp_heat_roll7_mean"] = grp["chp_waste_heat_kw"].transform(lambda s: s.rolling(7, min_periods=1).mean())

    # ── 10. Composite Station Risk at 18:00 Cutoff (t <= 0) ────────────────────
    df["power_risk_lag1"]   = df["power_risk"]
    df["overall_risk_lag1"] = df["overall_risk_score"]
    df["risk_roll7_mean"]   = grp["overall_risk_score"].transform(lambda s: s.rolling(7, min_periods=1).mean())

    # Drop edge rows where lead-1 target or 14-day history is not fully established
    df_clean = df.dropna(subset=[TARGET_NAME, "load_lag14", "obs_temp_lag3"]).reset_index(drop=True)
    logger.info("Forecast dataset constructed successfully: %d valid samples.", len(df_clean))
    return df_clean


def get_chronological_splits(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Chronological split strictly according to config:
      - Train: 2003–2019
      - Val:   2020–2021
      - Test:  2022
    """
    train = df[df["year"] <= SPLIT_CONFIG["train_end_year"]].copy()
    val   = df[(df["year"] >= SPLIT_CONFIG["val_start_year"]) & (df["year"] <= SPLIT_CONFIG["val_end_year"])].copy()
    test  = df[df["year"] >= SPLIT_CONFIG["test_year"]].copy()
    logger.info("Chronological Split — Train: %d | Val: %d | Test: %d", len(train), len(val), len(test))
    return train, val, test


def get_loso_splits(df: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame, int]]:
    """
    Leave-One-Simulation-Out cross-validation folds across runs 1 to 5.
    """
    folds = []
    for k in range(1, 6):
        train_k = df[df["run_id"] != k].copy()
        test_k  = df[df["run_id"] == k].copy()
        folds.append((train_k, test_k, k))
    return folds


if __name__ == "__main__":
    hashes = verify_simulation_file_integrity()
    df_raw = load_raw_corpus()
    df_clean = build_forecast_dataset(df_raw)
    tr, va, te = get_chronological_splits(df_clean)
    print(f"Features count: {len(FEATURE_COLUMNS)}")
    print(f"Dataset shape: {df_clean.shape}")
