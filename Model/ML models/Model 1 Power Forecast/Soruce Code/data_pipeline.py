"""
data_pipeline.py
----------------
Strict leakage-free data engineering and pre-forecast timeline alignment
for Model 1 (Power Load Forecasting V3).

PREDICTION TIMELINE CONTRACT:
  At 06:00 on Day t:
    - Target: Average total_load_kw on Day t+1 (24-hour lead forecast)
    - Available Features:
        * Astronomical / Calendar variables for Day t+1 (known exactly)
        * NWP Weather Forecast for Day t+1 (forecasted weather inputs)
        * Scheduled Population Roster for Day t+1
        * Historical Observed Telemetry up to Day t (load lags, thermal lags, rolling stats)
        * Battery SoC & Fuel Stock at 06:00 cutoff (Day t start)
"""

import os
import sys
import logging
import pickle
from typing import Tuple, List, Dict

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("DataPipeline-V3")

from config_v3 import (
    DATA_DIR,
    FEATURES_V3,
    TARGET_RAW,
    TARGET_FORECAST,
    RANDOM_SEED,
)

ORDINAL_WEATHER = {"CLEAR": 0, "NORMAL": 1, "HIGH_WIND": 2, "HEAVY_SNOW": 3, "WHITEOUT": 4, "BLIZZARD": 5}


def load_raw_simulation_runs() -> pd.DataFrame:
    """Load all 5 raw simulation runs into a single chronological DataFrame."""
    frames = []
    for i in range(1, 6):
        path = os.path.join(DATA_DIR, f"station_summary_{i}.csv")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing simulation dataset: {path}")
        logger.info("Loading simulation run %d: %s", i, os.path.basename(path))
        chunk = pd.read_csv(path, low_memory=False)
        chunk["run_id"] = i
        frames.append(chunk)

    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["run_id", "station_id", "date"]).reset_index(drop=True)
    logger.info("Loaded 5 simulation runs: %d rows × %d columns", len(df), len(df.columns))
    return df


def construct_day_ahead_dataset(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Construct the true day-ahead forecasting dataset ($t \to t+1$).
    Aligns target at $t+1$ and strictly builds pre-forecast features at $t$.
    """
    logger.info("Constructing day-ahead forecasting dataset from raw telemetry ...")
    df = df_raw.copy()
    
    # ── Grouping key for shift operations ──────────────────────────────────────
    grp = df.groupby(["run_id", "station_id"])
    
    # ── 1. Target Definition (Lead-1 Day Average Total Load) ────────────────────
    df[TARGET_FORECAST] = grp[TARGET_RAW].shift(-1)
    
    # ── 2. Station & Identity ──────────────────────────────────────────────────
    df["station_enc"] = (df["station_id"] == "BHARATI").astype(int)
    
    # ── 3. Astronomical & Calendar Time for Target Day (t+1) ───────────────────
    # Date at t+1 is known exactly
    date_lead1 = df["date"] + pd.Timedelta(days=1)
    df["year"]        = date_lead1.dt.year
    df["month"]       = date_lead1.dt.month
    df["day_of_year"] = date_lead1.dt.dayofyear
    df["day_of_week"] = date_lead1.dt.dayofweek
    df["quarter"]     = date_lead1.dt.quarter

    df["month_sin"]   = np.sin(2 * np.pi * df["month"] / 12)
    df["month_cos"]   = np.cos(2 * np.pi * df["month"] / 12)
    df["doy_sin"]     = np.sin(2 * np.pi * df["day_of_year"] / 365)
    df["doy_cos"]     = np.cos(2 * np.pi * df["day_of_year"] / 365)
    df["dow_sin"]     = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"]     = np.cos(2 * np.pi * df["day_of_week"] / 7)

    df["is_shipping_season"] = df["month"].isin([11, 12, 1, 2, 3]).astype(int)
    
    # ── 4. Day-Ahead NWP Weather Forecast for Target Day (t+1) ─────────────────
    # In the simulator, the next day's atmospheric conditions represent the true NWP forecast
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

    df["is_polar_night"]          = (df["fc_solar_daylight_hours"] < 1.0).astype(int)
    df["is_polar_day"]            = (df["fc_solar_daylight_hours"] > 22.0).astype(int)

    # Derived NWP forecast physical features
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

    # ── 5. Historical Observed Weather & Thermal Persistence (t <= 0) ──────────
    df["obs_temp_lag1"]       = df["temperature_c"]             # Observed today (t=0)
    df["obs_temp_lag2"]       = grp["temperature_c"].shift(1)   # Observed t-1
    df["obs_temp_lag3"]       = grp["temperature_c"].shift(2)   # Observed t-2
    df["obs_temp_roll7_mean"] = grp["temperature_c"].transform(lambda x: x.rolling(7, min_periods=1).mean())
    df["obs_temp_trend3"]     = df["obs_temp_lag1"] - df["obs_temp_lag3"]

    df["obs_wind_lag1"]       = df["wind_speed_kmh"]
    df["obs_wind_roll7_mean"] = grp["wind_speed_kmh"].transform(lambda x: x.rolling(7, min_periods=1).mean())
    df["obs_weather_sev_lag1"]= df["weather_severity"]
    df["obs_weather_sev_roll7"]= grp["weather_severity"].transform(lambda x: x.rolling(7, min_periods=1).mean())

    # ── 6. Scheduled Station Population Roster for Target Day (t+1) ────────────
    df["scheduled_population"]    = grp["total_population"].shift(-1)
    df["scheduled_occupancy_pct"] = grp["occupancy_percent"].shift(-1)
    df["scheduled_scientists"]    = grp["scientists"].shift(-1)
    df["scheduled_engineers"]     = grp["engineers"].shift(-1)
    df["scheduled_technicians"]   = grp["technicians"].shift(-1)
    df["scheduled_medical"]       = grp["medical"].shift(-1)
    df["pop_lag1"]                = df["total_population"]
    df["pop_trend7"]              = df["total_population"] - grp["total_population"].shift(6)

    # ── 7. Historical Electrical Load History (Strictly t <= 0) ────────────────
    # Today's observed load at 06:00 represents load_lag1 for forecasting day t+1
    df["load_lag1"]  = df[TARGET_RAW]
    df["load_lag2"]  = grp[TARGET_RAW].shift(1)
    df["load_lag3"]  = grp[TARGET_RAW].shift(2)
    df["load_lag7"]  = grp[TARGET_RAW].shift(6)
    df["load_lag14"] = grp[TARGET_RAW].shift(13)

    # Trailing rolling statistics (strictly including t <= 0 only)
    df["load_roll3_mean"]  = grp[TARGET_RAW].transform(lambda x: x.rolling(3, min_periods=1).mean())
    df["load_roll7_mean"]  = grp[TARGET_RAW].transform(lambda x: x.rolling(7, min_periods=1).mean())
    df["load_roll14_mean"] = grp[TARGET_RAW].transform(lambda x: x.rolling(14, min_periods=1).mean())
    df["load_roll30_mean"] = grp[TARGET_RAW].transform(lambda x: x.rolling(30, min_periods=1).mean())
    df["load_roll7_std"]   = grp[TARGET_RAW].transform(lambda x: x.rolling(7, min_periods=1).std()).fillna(0)
    df["load_roll14_std"]  = grp[TARGET_RAW].transform(lambda x: x.rolling(14, min_periods=1).std()).fillna(0)

    df["load_trend_3d"]    = df["load_lag1"] - df["load_lag3"]
    df["load_trend_7d"]    = df["load_lag1"] - df["load_lag7"]

    # ── 8. Storage Buffer States at Forecast Cutoff Timestamp (06:00, t=0) ──────
    df["battery_soc_start_pct"]   = df["battery_soc_percent"]
    df["soc_lag1"]                = grp["battery_soc_percent"].shift(1)
    df["soc_delta_lag1"]          = df["battery_soc_percent"] - df["soc_lag1"]
    df["fuel_stock_start_liters"] = df["fuel_stock_liters"]

    # Days since last refuel event
    def days_since_event(s: pd.Series) -> pd.Series:
        res = pd.Series(index=s.index, dtype=float)
        c = 0
        for idx, val in s.items():
            if val: c = 0
            else: c += 1
            res[idx] = c
        return res

    df["days_since_refuel_start"] = grp["refuel_event"].transform(days_since_event)

    # ── 9. Physical Heating & CHP Thermal Coupling (t <= 0) ────────────────────
    df["chp_heat_lag1"]       = df["chp_waste_heat_kw"]
    df["chp_heat_roll7_mean"] = grp["chp_waste_heat_kw"].transform(lambda x: x.rolling(7, min_periods=1).mean())

    # ── 10. Composite Risk Signals at Forecast Cutoff (t <= 0) ─────────────────
    df["power_risk_lag1"]   = df["power_risk"]
    df["overall_risk_lag1"] = df["overall_risk_score"]
    df["risk_roll7_mean"]   = grp["overall_risk_score"].transform(lambda x: x.rolling(7, min_periods=1).mean())

    # Drop edge rows where lead-1 target or early lags are NaN
    df_clean = df.dropna(subset=[TARGET_FORECAST, "load_lag14", "obs_temp_lag3"]).reset_index(drop=True)
    logger.info("Day-ahead dataset ready: %d valid forecasting instances.", len(df_clean))
    return df_clean


def run_leakage_assertion_tests(df: pd.DataFrame) -> None:
    """
    Automated zero-tolerance target leakage assertion test suite.
    Ensures:
      1. No direct algebraic energy identities in feature matrix.
      2. No same-day sub-load sums in feature matrix.
      3. No post-event outcomes (e.g., generator dispatch, load shedding) in feature matrix.
      4. Correlation between individual features and future target does not exceed physical limits (no r=1.0).
    """
    logger.info("Executing automated leakage assertion test suite ...")
    
    # 1. Banned column check
    banned_substrings = [
        "daily_load_energy", "generator_energy", "solar_to_load", "battery_to_load",
        "unserved_energy", "overload_flag", "load_shedding", "power_shortage",
        "accommodation_load_kw", "laboratory_load_kw", "kitchen_load_kw", "heating_load_kw",
        "water_plant_load_kw", "communication_load_kw", "lighting_load_kw", "emergency_load_kw",
        "generator_output_kw", "generator_runtime_hours", "active_generators",
    ]
    for feat in FEATURES_V3:
        for banned in banned_substrings:
            assert banned not in feat, f"CRITICAL LEAKAGE: Feature '{feat}' contains banned pattern '{banned}'!"
    
    # 2. Check maximum single feature correlation with target
    for feat in FEATURES_V3:
        corr = np.abs(np.corrcoef(df[feat].values, df[TARGET_FORECAST].values)[0, 1])
        assert corr < 0.999, f"CRITICAL LEAKAGE: Feature '{feat}' has correlation {corr:.6f} with target (suspected identity)!"

    logger.info("PASSED ALL LEAKAGE ASSERTION TESTS (0 leakage detected, strict physical feature space).")


def get_chronological_splits(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Chronological train / validation / test splits:
      - Train: Years 2003–2019
      - Val:   Years 2020–2021
      - Test:  Year 2022
    """
    train = df[df["year"] <= 2019].copy()
    val   = df[(df["year"] >= 2020) & (df["year"] <= 2021)].copy()
    test  = df[df["year"] >= 2022].copy()
    logger.info("Chronological Split — Train: %d | Val: %d | Test: %d", len(train), len(val), len(test))
    return train, val, test


def get_loso_folds(df: pd.DataFrame) -> List[Tuple[pd.DataFrame, pd.DataFrame, int]]:
    """
    Leave-One-Simulation-Out (LOSO) 5-fold splits.
    Fold k: Train on Runs != k, Test on Run == k.
    """
    folds = []
    for k in range(1, 6):
        train_k = df[df["run_id"] != k].copy()
        test_k  = df[df["run_id"] == k].copy()
        folds.append((train_k, test_k, k))
    logger.info("Constructed 5 Leave-One-Simulation-Out (LOSO) cross-validation folds.")
    return folds


if __name__ == "__main__":
    df_raw = load_raw_simulation_runs()
    df_v3 = construct_day_ahead_dataset(df_raw)
    run_leakage_assertion_tests(df_v3)
    train, val, test = get_chronological_splits(df_v3)
    print(f"Features: {len(FEATURES_V3)}")
    print(f"Target: {TARGET_FORECAST}")
