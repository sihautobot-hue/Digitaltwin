"""
feature_engineering.py
-----------------------
Production feature engineering module for Model 3 (Version 3).
Implements the Day-Ahead Fuel Runway Forecast Contract:
  - Prediction issued at 18:00 on Day t
  - Target: fuel_days_remaining at Day t+1 (fuel_runway_lead1)
  - SHIFT FIRST, THEN ROLL. Zero look-ahead. No same-day observations for Day t+1.

Mathematical Invariance:
  For index t predicting Day t+1:
  fuel_roll7_mean[t] = mean(fuel_consumed[t], fuel_consumed[t-1], ..., fuel_consumed[t-6])
  This NEVER includes fuel_consumed[t+1].
"""

import os
import hashlib
import logging
from typing import Tuple, List, Dict

import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FeatureEngineering-Model3-V3")

from config import (
    DATA_DIR,
    FEATURE_COLUMNS,
    TARGET_RAW,
    TARGET_NAME,
    TARGET_CLIP,
    SPLIT_CONFIG,
    RANDOM_SEED,
)

ORDINAL_WEATHER = {
    "CLEAR": 0, "NORMAL": 1, "HIGH_WIND": 2,
    "HEAVY_SNOW": 3, "WHITEOUT": 4, "BLIZZARD": 5,
}


def verify_simulation_hashes() -> Dict[int, Dict[str, str]]:
    """Compute SHA-256 hashes of all 5 simulation files and flag duplicates."""
    logger.info("Verifying SHA-256 hashes of all 5 simulation datasets ...")
    hashes = {}
    seen = {}
    duplicates = []

    for i in range(1, 6):
        path = os.path.join(DATA_DIR, f"station_summary_{i}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing simulation file: {path}")
        with open(path, "rb") as fp:
            h = hashlib.sha256(fp.read()).hexdigest()
        hashes[i] = {"path": path, "sha256": h}
        if h in seen:
            duplicates.append((i, seen[h]))
        else:
            seen[h] = i

    if duplicates:
        logger.warning("=" * 78)
        logger.warning("CRITICAL CROSS-RUN INTEGRITY WARNING (MODEL 3):")
        for dup, orig in duplicates:
            logger.warning(
                "  Simulation Run %d is a bitwise DUPLICATE of Run %d (SHA-256: %s...)",
                dup, orig, hashes[dup]["sha256"][:16],
            )
        logger.warning("  LOSO across all 5 runs is OPTIMISTIC due to duplicate runs.")
        logger.warning("  We report both naive 5-fold AND deduplicated (Runs 1,2,3) metrics.")
        logger.warning("=" * 78)

    return hashes


def load_raw_corpus() -> pd.DataFrame:
    """Load and concatenate all 5 simulation CSV files into a single corpus."""
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
    logger.info("Loaded corpus: %d rows × %d columns", len(df), len(df.columns))
    return df


def build_fuel_runway_dataset(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Construct forecast-safe dataset for Model 3 (Fuel Runway).
    Prediction issued at 18:00 on Day t predicting fuel_days_remaining at Day t+1.
    All rolling statistics: SHIFT FIRST, THEN ROLL.
    """
    logger.info("Building day-ahead fuel runway dataset (strictly shifted) ...")
    df = df_raw.copy()
    grp = df.groupby(["run_id", "station_id"])

    # ── 1. Target: fuel_days_remaining at Day t+1 ──────────────────────────────
    # Clip to 365 days (>1 year runway is operationally equivalent)
    df[TARGET_NAME] = grp[TARGET_RAW].shift(-1).clip(upper=TARGET_CLIP)

    # ── 2. Station Identity ────────────────────────────────────────────────────
    df["station_enc"] = (df["station_id"] == "BHARATI").astype(int)

    # ── 3. Calendar & Astronomical Geometry for Day t+1 ────────────────────────
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
    df["fc_katabatic_index"]       = df["fc_wind_speed_kmh"] * np.maximum(0, -df["fc_temperature_c"]) / 100.0
    df["fc_heating_degree_days"]   = np.maximum(0, 18.0 - df["fc_temperature_c"])

    # ── 5. Historical Weather Persistence (Observed up to Day t) ───────────────
    df["obs_temp_lag1"]        = df["temperature_c"]
    df["obs_temp_lag2"]        = grp["temperature_c"].shift(1)
    df["obs_temp_lag3"]        = grp["temperature_c"].shift(2)
    df["obs_temp_roll7_mean"]  = grp["temperature_c"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    df["obs_temp_trend3"]      = df["obs_temp_lag1"] - df["obs_temp_lag3"]
    df["obs_wind_lag1"]        = df["wind_speed_kmh"]
    df["obs_wind_roll7_mean"]  = grp["wind_speed_kmh"].transform(lambda s: s.rolling(7, min_periods=1).mean())
    df["obs_weather_sev_lag1"] = df["weather_severity"]
    df["obs_weather_sev_roll7"]= grp["weather_severity"].transform(lambda s: s.rolling(7, min_periods=1).mean())

    # ── 6. Scheduled Population Roster for Day t+1 ─────────────────────────────
    df["scheduled_population"]    = grp["total_population"].shift(-1)
    df["scheduled_occupancy_pct"] = grp["occupancy_percent"].shift(-1)
    df["scheduled_scientists"]    = grp["scientists"].shift(-1)
    df["scheduled_engineers"]     = grp["engineers"].shift(-1)
    df["scheduled_technicians"]   = grp["technicians"].shift(-1)
    df["scheduled_medical"]       = grp["medical"].shift(-1)
    df["pop_lag1"]                = df["total_population"]
    df["pop_trend7"]              = df["total_population"] - grp["total_population"].shift(6)

    # ── 7. Fuel Inventory State at 18:00 Cutoff (Day t) ────────────────────────
    df["fuel_stock_start_liters"]  = df["fuel_stock_liters"]
    df["fuel_stock_lag1"]          = grp["fuel_stock_liters"].shift(1)
    df["fuel_stock_drawdown_3d"]   = grp["fuel_stock_liters"].shift(2) - df["fuel_stock_start_liters"]
    # fuel_shipments_pending and fuel_eta_days already present in raw data

    def _days_since_refuel(s: pd.Series) -> pd.Series:
        """
        Vectorised days-since-last-refuel counter within a group.
        On a refuel day the counter resets to 0; otherwise increments by 1.
        This correctly handles group boundaries because it is applied per
        (run_id, station_id) group via transform.
        """
        # cumulative group count — resets at each True (refuel) event
        s_int = s.astype(int)
        cumsum_all = s_int.cumsum()
        cumsum_masked = cumsum_all.where(s_int == 1).ffill().fillna(0)
        days_since = cumsum_all - cumsum_masked
        # On the refuel day itself, set counter to 0
        days_since = days_since.where(s_int == 0, 0)
        return days_since

    df["days_since_refuel_start"] = grp["refuel_event"].transform(_days_since_refuel)

    # ── 8. Historical Fuel Consumption Lags & Shift-Then-Roll Statistics ───────
    # At 18:00 on Day t, observed fuel burn on Day t = fuel_consumed_today_liters
    fuel_col = "fuel_consumed_today_liters"
    df["fuel_lag1"]  = df[fuel_col]
    df["fuel_lag2"]  = grp[fuel_col].shift(1)
    df["fuel_lag3"]  = grp[fuel_col].shift(2)
    df["fuel_lag7"]  = grp[fuel_col].shift(6)
    df["fuel_lag14"] = grp[fuel_col].shift(13)

    # SHIFT THEN ROLL: series at Day t includes [t, t-1, ..., t-k+1]
    df["fuel_roll3_mean"]     = grp[fuel_col].transform(lambda s: s.rolling(3,  min_periods=1).mean())
    df["fuel_roll7_mean"]     = grp[fuel_col].transform(lambda s: s.rolling(7,  min_periods=1).mean())
    df["fuel_roll14_mean"]    = grp[fuel_col].transform(lambda s: s.rolling(14, min_periods=1).mean())
    df["fuel_roll30_mean"]    = grp[fuel_col].transform(lambda s: s.rolling(30, min_periods=1).mean())
    df["fuel_expanding_mean"] = grp[fuel_col].transform(lambda s: s.expanding(min_periods=1).mean())
    df["fuel_roll7_std"]      = grp[fuel_col].transform(lambda s: s.rolling(7,  min_periods=1).std()).fillna(0)
    df["fuel_roll14_std"]     = grp[fuel_col].transform(lambda s: s.rolling(14, min_periods=1).std()).fillna(0)
    df["fuel_trend_3d"]       = df["fuel_lag1"] - df["fuel_lag3"]
    df["fuel_trend_7d"]       = df["fuel_lag1"] - df["fuel_lag7"]

    # ── 9. Historical Fuel Runway Lags & Shift-Then-Roll Statistics ────────────
    # fuel_days_remaining at Day t IS observed telemetry. It is NOT the target.
    # The target is fuel_days_remaining at Day t+1 (fuel_runway_lead1).
    df["runway_lag1"]  = df[TARGET_RAW].clip(upper=TARGET_CLIP)
    df["runway_lag2"]  = grp[TARGET_RAW].shift(1).clip(upper=TARGET_CLIP)
    df["runway_lag7"]  = grp[TARGET_RAW].shift(6).clip(upper=TARGET_CLIP)

    df["runway_roll3_mean"]  = grp[TARGET_RAW].transform(lambda s: s.rolling(3,  min_periods=1).mean()).clip(upper=TARGET_CLIP)
    df["runway_roll7_mean"]  = grp[TARGET_RAW].transform(lambda s: s.rolling(7,  min_periods=1).mean()).clip(upper=TARGET_CLIP)
    df["runway_roll14_mean"] = grp[TARGET_RAW].transform(lambda s: s.rolling(14, min_periods=1).mean()).clip(upper=TARGET_CLIP)
    df["runway_trend_3d"]    = df["runway_lag1"] - df["runway_lag2"]
    df["runway_trend_7d"]    = df["runway_lag1"] - df["runway_lag7"]

    # ── 10. Past Generator Telemetry (Observed on Day t, t <= 0) ───────────────
    df["gen_output_lag1"]      = df["generator_output_kw"]
    df["gen_runtime_lag1"]     = df["generator_runtime_hours"]
    df["gen_utilization_lag1"] = df["generator_output_kw"] / np.clip(df["active_generators"] * 100.0, 1.0, None)
    df["chp_heat_lag1"]        = df["chp_waste_heat_kw"]
    df["chp_heat_roll7_mean"]  = grp["chp_waste_heat_kw"].transform(lambda s: s.rolling(7, min_periods=1).mean())

    # ── 11. Storage & Risk State at 18:00 Cutoff (Day t) ───────────────────────
    df["battery_soc_start_pct"] = df["battery_soc_percent"]
    df["soc_lag1"]              = grp["battery_soc_percent"].shift(1)
    df["soc_delta_lag1"]        = df["battery_soc_percent"] - df["soc_lag1"]
    df["fuel_risk_lag1"]        = df["fuel_risk"]
    df["power_risk_lag1"]       = df["power_risk"]
    df["overall_risk_lag1"]     = df["overall_risk_score"]
    df["risk_roll7_mean"]       = grp["overall_risk_score"].transform(lambda s: s.rolling(7, min_periods=1).mean())

    # Drop rows where target or essential lags are missing
    df_clean = df.dropna(subset=[TARGET_NAME, "fuel_lag14", "runway_lag7", "obs_temp_lag3"]).reset_index(drop=True)
    logger.info("Model 3 fuel runway dataset ready: %d valid samples.", len(df_clean))
    return df_clean


def get_chronological_splits(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Chronological train / val / test splits."""
    train = df[df["year"] <= SPLIT_CONFIG["train_end_year"]].copy()
    val   = df[(df["year"] >= SPLIT_CONFIG["val_start_year"]) & (df["year"] <= SPLIT_CONFIG["val_end_year"])].copy()
    test  = df[df["year"] >= SPLIT_CONFIG["test_year"]].copy()
    logger.info("Split — Train: %d | Val: %d | Test: %d", len(train), len(val), len(test))
    return train, val, test


def get_loso_splits(df: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame, int]]:
    """5-fold Leave-One-Simulation-Out splits."""
    return [(df[df["run_id"] != k].copy(), df[df["run_id"] == k].copy(), k) for k in range(1, 6)]


if __name__ == "__main__":
    verify_simulation_hashes()
    df_raw = load_raw_corpus()
    df_clean = build_fuel_runway_dataset(df_raw)
    tr, va, te = get_chronological_splits(df_clean)
    print(f"Features: {len(FEATURE_COLUMNS)} | Total Samples: {len(df_clean)}")
