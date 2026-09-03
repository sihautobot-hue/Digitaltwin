# feature_engineering.py
# Production feature engineering module for Model 4 (Version 3).

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
logger = logging.getLogger("FeatureEngineering-Model4-V3")

from config import (
    DATA_DIR,
    FEATURE_COLUMNS,
    TARGET_RAW,
    TARGET_NAME,
    SPLIT_CONFIG,
    RANDOM_SEED,
)

STATION_MAP = {"BHARATI": 0, "MAITRI": 1}
SEASON_MAP  = {"SUMMER": 0, "WINTER": 1}


def verify_simulation_hashes() -> Dict[int, Dict[str, str]]:
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
        logger.warning("CROSS-RUN INTEGRITY AUDIT (MODEL 4):")
        for dup, orig in duplicates:
            logger.warning(
                "  Simulation Run %d is a bitwise DUPLICATE of Run %d (SHA-256: %s...)",
                dup, orig, hashes[dup]["sha256"][:16],
            )
        logger.warning("  LOSO cross-validation will report both 5-fold and deduplicated (Runs 1,2,3) results.")
        logger.warning("=" * 78)

    return hashes


def compute_days_since_shipment(df_station: pd.DataFrame) -> pd.Series:
    received = (df_station["received_today"] > 0).values
    n = len(received)
    days_since = np.zeros(n, dtype=float)
    counter = 180.0
    for i in range(n):
        if received[i]:
            counter = 0.0
        else:
            counter += 1.0
        days_since[i] = counter
    return pd.Series(days_since, index=df_station.index)


def process_single_simulation(file_path: str, sim_run_id: int) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["station_id", "date"]).reset_index(drop=True)
    df["sim_run_id"] = sim_run_id

    station_dfs = []
    for station, sdf in df.groupby("station_id", as_index=False):
        sdf = sdf.sort_values("date").reset_index(drop=True)

        # 1. Day t+1 Forecast Target (Binary Classification)
        sdf[TARGET_NAME] = (sdf[TARGET_RAW].shift(-1) > 0).astype(float)
        sdf["shortage_count_lead1"] = sdf[TARGET_RAW].shift(-1)
        sdf["critical_items_lead1"] = sdf["critical_items"].shift(-1)

        # 2. Station & Temporal Encodings
        sdf["station_enc"] = sdf["station_id"].map(STATION_MAP).fillna(0).astype(int)
        dt = sdf["date"].dt
        sdf["year"]        = dt.year
        sdf["month"]       = dt.month
        sdf["quarter"]     = dt.quarter
        sdf["day_of_year"] = dt.dayofyear

        # Cyclical transforms for Day t+1
        doy_next = (sdf["day_of_year"] % 365) + 1
        month_next = ((sdf["month"]) % 12) + 1
        sdf["month_sin"]   = np.sin(2 * np.pi * month_next / 12.0)
        sdf["month_cos"]   = np.cos(2 * np.pi * month_next / 12.0)
        sdf["doy_sin"]     = np.sin(2 * np.pi * doy_next / 365.25)
        sdf["doy_cos"]     = np.cos(2 * np.pi * doy_next / 365.25)
        sdf["season_enc"]  = sdf["season"].map(SEASON_MAP).fillna(0).astype(int)

        # 3. Inventory Health & Stock State at 18:00 on Day t
        sdf["inv_health_lag0"] = sdf["inventory_health_score"]
        sdf["inv_health_lag1"] = sdf["inventory_health_score"].shift(1).bfill()
        sdf["inv_health_lag7"] = sdf["inventory_health_score"].shift(7).bfill()
        sdf["inv_health_roll7_mean"]  = sdf["inv_health_lag0"].rolling(7, min_periods=1).mean()
        sdf["inv_health_roll14_mean"] = sdf["inv_health_lag0"].rolling(14, min_periods=1).mean()
        sdf["inv_health_trend_7d"]    = sdf["inv_health_lag0"] - sdf["inv_health_lag7"]

        sdf["critical_items_lag0"] = sdf["critical_items"]
        sdf["critical_items_lag1"] = sdf["critical_items"].shift(1).bfill()
        sdf["critical_items_roll7_mean"] = sdf["critical_items_lag0"].rolling(7, min_periods=1).mean()

        sdf["low_items_lag0"] = sdf["low_items"]
        sdf["low_items_lag1"] = sdf["low_items"].shift(1).bfill()
        sdf["low_items_roll7_mean"] = sdf["low_items_lag0"].rolling(7, min_periods=1).mean()

        sdf["inventory_risk_lag0"] = sdf["inventory_risk"]
        sdf["inv_risk_roll7_mean"]  = sdf["inventory_risk_lag0"].rolling(7, min_periods=1).mean()

        # 4. Historical Shortage Dynamics (Strict Shift-Then-Roll from Day t backwards)
        sdf["shortage_items_lag0"]  = sdf[TARGET_RAW]
        sdf["shortage_items_lag1"]  = sdf[TARGET_RAW].shift(1).bfill()
        sdf["shortage_items_lag2"]  = sdf[TARGET_RAW].shift(2).bfill()
        sdf["shortage_items_lag7"]  = sdf[TARGET_RAW].shift(7).bfill()
        sdf["shortage_items_lag14"] = sdf[TARGET_RAW].shift(14).bfill()

        sdf["shortage_roll3_mean"]  = sdf["shortage_items_lag0"].rolling(3, min_periods=1).mean()
        sdf["shortage_roll7_mean"]  = sdf["shortage_items_lag0"].rolling(7, min_periods=1).mean()
        sdf["shortage_roll14_mean"] = sdf["shortage_items_lag0"].rolling(14, min_periods=1).mean()
        sdf["shortage_roll30_mean"] = sdf["shortage_items_lag0"].rolling(30, min_periods=1).mean()
        sdf["shortage_trend_7d"]    = sdf["shortage_items_lag0"] - sdf["shortage_items_lag7"]

        sdf["shortage_binary_lag0"]   = (sdf["shortage_items_lag0"] > 0).astype(int)
        sdf["shortage_days_in_past_7"]  = sdf["shortage_binary_lag0"].rolling(7, min_periods=1).sum()
        sdf["shortage_days_in_past_30"] = sdf["shortage_binary_lag0"].rolling(30, min_periods=1).sum()

        # 5. Inbound Supply Chain & Logistics State at Day t
        sdf["inv_orders_pending_lag0"] = sdf["inventory_orders_pending"]
        sdf["inv_eta_days_lag0"]       = sdf["inventory_eta_days"]
        sdf["delayed_shipments_lag0"]  = sdf["delayed_shipments"].fillna(0)
        sdf["inv_batch_count_lag0"]    = sdf["inventory_batch_count"]
        sdf["expired_items_lag0"]      = sdf["expired_items"]
        sdf["expired_quantity_lag0"]   = sdf["expired_quantity"]
        sdf["days_since_shipment_received"] = compute_days_since_shipment(sdf)

        # Shipping season geometry (Nov 1 to Mar 31 in Antarctica)
        month = sdf["month"].values
        doy   = sdf["day_of_year"].values
        is_ship = np.isin(month, [11, 12, 1, 2, 3]).astype(int)
        sdf["is_shipping_season"] = is_ship
        sdf["shipping_window_open"] = is_ship
        sdf["days_into_shipping_season"] = np.where(is_ship == 1, np.maximum(0, doy - 305), 0)
        sdf["days_until_shipping_season"] = np.where(is_ship == 0, np.maximum(0, 305 - doy), 0)

        # 6. Scheduled Population Roster for Day t+1
        sdf["scheduled_population"]        = sdf["total_population"].shift(-1).ffill()
        sdf["scheduled_occupancy_percent"] = sdf["occupancy_percent"].shift(-1).ffill()
        sdf["scheduled_scientists"]        = sdf["scientists"].shift(-1).ffill()
        sdf["scheduled_engineers"]         = sdf["engineers"].shift(-1).ffill()
        sdf["scheduled_technicians"]       = sdf["technicians"].shift(-1).ffill()
        sdf["scheduled_logistics"]         = sdf["logistics"].shift(-1).ffill()
        sdf["scheduled_medical"]           = sdf["medical"].shift(-1).ffill()

        sdf["pop_lag1"]        = sdf["total_population"].shift(1).bfill()
        sdf["pop_roll14_mean"] = sdf["total_population"].rolling(14, min_periods=1).mean()
        sdf["pop_trend_7d"]    = sdf["total_population"] - sdf["total_population"].shift(7).bfill()

        # 7. Day-Ahead NWP Weather Forecast for Day t+1
        sdf["fc_temperature_c"]        = sdf["temperature_c"].shift(-1).ffill()
        sdf["fc_wind_speed_kmh"]       = sdf["wind_speed_kmh"].shift(-1).ffill()
        sdf["fc_wind_gust_kmh"]        = sdf["wind_gust_kmh"].shift(-1).ffill()
        sdf["fc_weather_severity"]     = sdf["weather_severity"].shift(-1).ffill()
        sdf["fc_solar_radiation_wm2"]  = sdf["solar_radiation_wm2"].shift(-1).ffill()
        sdf["fc_solar_daylight_hours"] = sdf["solar_daylight_hours"].shift(-1).ffill()
        sdf["fc_heating_degree_days"]  = np.maximum(0.0, 18.0 - sdf["fc_temperature_c"])
        sdf["fc_blizzard_risk"]        = ((sdf["fc_wind_speed_kmh"] > 60) & (sdf["fc_temperature_c"] < -15)).astype(int)
        sdf["fc_is_extreme_weather"]   = (sdf["fc_weather_severity"] >= 4).astype(int)

        # Astronomical daylight flags for Day t+1
        sdf["is_polar_night"] = (sdf["fc_solar_daylight_hours"] < 0.5).astype(int)
        sdf["is_polar_day"]   = (sdf["fc_solar_daylight_hours"] > 23.5).astype(int)

        # 8. Historical Equipment Telemetry & Subsystem Risk at 18:00 Day t
        sdf["gen_runtime_lag0"]      = sdf["generator_runtime_hours"]
        sdf["gen_output_lag0"]       = sdf["generator_output_kw"]
        sdf["active_gen_lag0"]       = sdf["active_generators"]
        sdf["power_risk_lag0"]       = sdf["power_risk"]
        sdf["fuel_risk_lag0"]        = sdf["fuel_risk"]
        sdf["water_risk_lag0"]       = sdf["water_risk"]
        sdf["water_plant_util_lag0"] = sdf["water_plant_utilisation_percent"].fillna(0)
        sdf["risk_score_lag0"]       = sdf["risk_score"]
        sdf["station_health_lag0"]   = sdf["station_health"]

        # Drop the very last row where Day t+1 target is NaN
        sdf = sdf.dropna(subset=[TARGET_NAME]).reset_index(drop=True)
        station_dfs.append(sdf)

    return pd.concat(station_dfs, ignore_index=True)


def load_raw_corpus(deduplicate: bool = False) -> pd.DataFrame:
    runs_to_load = [1, 2, 3] if deduplicate else [1, 2, 3, 4, 5]
    dfs = []
    for run_id in runs_to_load:
        path = os.path.join(DATA_DIR, f"station_summary_{run_id}.csv")
        logger.info("Processing simulation run %d: %s ...", run_id, path)
        proc_df = process_single_simulation(path, run_id)
        dfs.append(proc_df)
    
    full_corpus = pd.concat(dfs, ignore_index=True)
    logger.info(
        "Full corpus built: %d rows, %d features, target positive rate = %.2f%%",
        len(full_corpus),
        len(FEATURE_COLUMNS),
        full_corpus[TARGET_NAME].mean() * 100,
    )
    return full_corpus


def get_chronological_splits(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    train_df = df[df["year"] <= SPLIT_CONFIG["train_end_year"]].copy().reset_index(drop=True)
    val_df   = df[(df["year"] >= SPLIT_CONFIG["val_start_year"]) &
                  (df["year"] <= SPLIT_CONFIG["val_end_year"])].copy().reset_index(drop=True)
    test_df  = df[df["year"] >= SPLIT_CONFIG["test_start_year"]].copy().reset_index(drop=True)

    logger.info(
        "Chronological Splits -> Train: %d (pos=%.2f%%) | Val: %d (pos=%.2f%%) | Test: %d (pos=%.2f%%)",
        len(train_df), train_df[TARGET_NAME].mean() * 100,
        len(val_df),   val_df[TARGET_NAME].mean() * 100,
        len(test_df),  test_df[TARGET_NAME].mean() * 100,
    )
    return train_df, val_df, test_df


def get_loso_splits(df: pd.DataFrame, runs: List[int]) -> List[Tuple[pd.DataFrame, pd.DataFrame, int]]:
    splits = []
    for held_out in runs:
        tr = df[df["sim_run_id"] != held_out].copy().reset_index(drop=True)
        ho = df[df["sim_run_id"] == held_out].copy().reset_index(drop=True)
        splits.append((tr, ho, held_out))
    return splits


if __name__ == "__main__":
    verify_simulation_hashes()
    corpus = load_raw_corpus()
    tr, va, te = get_chronological_splits(corpus)
    print("Feature count:", len(FEATURE_COLUMNS))
