# feature_engineering.py -- Model 6 V3: Day-Ahead Operational Risk Forecasting
# Strict Shift-Then-Roll invariant: roll[t] = mean(x[t-1], ..., x[t-k])
import os, hashlib, logging, warnings
from typing import List, Dict
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FE-Model6-V3")

from config import (
    DATA_FILES, ANOMALY_SOURCE_COLS, TARGET_NAME, FEATURE_COLS,
    TRAIN_YEARS, VAL_YEARS, TEST_YEARS,
)

SEASON_MAP  = {"Summer": 0, "Autumn": 0, "Spring": 0, "Winter": 1}
STATION_MAP = {"BHARATI": 0, "MAITRI": 1}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_duplicate_runs(files):
    hashes = {}
    seen = {}
    logger.info("=" * 70)
    logger.info("SHA-256 CRYPTOGRAPHIC SIMULATION DUPLICATE AUDIT")
    logger.info("=" * 70)
    for i, f in enumerate(files, 1):
        h = sha256_file(f)
        hashes[i] = h
        if h in seen:
            logger.warning("  Run %d is a bitwise DUPLICATE of Run %d (SHA-256: %s...)", i, seen[h], h[:16])
        else:
            seen[h] = i
            logger.info("  Run %d: SHA-256 %s... (Unique)", i, h[:16])
    logger.info("  LOSO will report both naive and deduplicated results.")
    logger.info("=" * 70)
    return hashes


def compute_streaks(series):
    arr = series.values.astype(float)
    streak = np.zeros(len(arr), dtype=float)
    free   = np.zeros(len(arr), dtype=float)
    cur_s, cur_f = 0.0, 0.0
    for i in range(len(arr)):
        streak[i] = cur_s
        free[i]   = cur_f
        if np.isnan(arr[i]):
            cur_s, cur_f = 0.0, 0.0
        elif arr[i] == 1:
            cur_s += 1; cur_f = 0.0
        else:
            cur_s = 0.0; cur_f += 1
    return pd.Series(streak, index=series.index), pd.Series(free, index=series.index)


def days_since_event(series):
    arr = series.values
    out = np.full(len(arr), np.nan)
    counter = np.nan
    for i in range(len(arr)):
        out[i] = counter
        v = arr[i]
        try:
            is_ev = bool(v) and not np.isnan(float(v))
        except Exception:
            is_ev = False
        if is_ev:
            counter = 0.0
        elif not np.isnan(counter):
            counter += 1
    return pd.Series(out, index=series.index)


def engineer_features(df):
    df = df.copy().sort_values("date").reset_index(drop=True)
    anom = np.zeros(len(df), dtype=float)
    for col in ANOMALY_SOURCE_COLS:
        if col in df.columns:
            anom = anom | df[col].fillna(False).astype(bool).astype(float).values
    df["OperationalAnomaly"] = anom.astype(float)
    df[TARGET_NAME] = df["OperationalAnomaly"].shift(-1)

    def lag(col, n=1):
        return df[col].shift(n)
    def roll_mean(col, w, min_p=1):
        return df[col].shift(1).rolling(w, min_periods=min_p).mean()
    def roll_std(col, w, min_p=2):
        return df[col].shift(1).rolling(w, min_periods=min_p).std().fillna(0.0)
    def roll_min(col, w, min_p=1):
        return df[col].shift(1).rolling(w, min_periods=min_p).min()
    def trend_slope(col, w):
        s = df[col].shift(1)
        def _slope(x):
            v = x.dropna()
            if len(v) < 3: return np.nan
            return float(np.polyfit(np.arange(len(v)), v.values, 1)[0])
        return s.rolling(w, min_periods=3).apply(_slope, raw=False)
    def ema_col(col, span):
        return df[col].shift(1).ewm(span=span, min_periods=1).mean()

    # Anomaly history
    df["anomaly_lag1"]        = lag("OperationalAnomaly", 1)
    df["anomaly_lag2"]        = lag("OperationalAnomaly", 2)
    df["anomaly_lag3"]        = lag("OperationalAnomaly", 3)
    df["anomaly_lag7"]        = lag("OperationalAnomaly", 7)
    df["anomaly_roll7_mean"]  = roll_mean("OperationalAnomaly", 7)
    df["anomaly_roll14_mean"] = roll_mean("OperationalAnomaly", 14)
    df["anomaly_roll30_mean"] = roll_mean("OperationalAnomaly", 30)
    df["anomaly_roll7_std"]   = roll_std("OperationalAnomaly", 7)
    df["anomaly_ema7"]        = ema_col("OperationalAnomaly", 7)
    df["anomaly_frequency30"] = df["OperationalAnomaly"].shift(1).rolling(30, min_periods=1).sum()
    streak, free_streak = compute_streaks(df["OperationalAnomaly"])
    df["anomaly_streak"]      = streak
    df["anomaly_free_streak"] = free_streak

    # Fuel
    df["fuel_stock_lag1"]             = lag("fuel_stock_liters", 1)
    df["fuel_stock_roll7_mean"]       = roll_mean("fuel_stock_liters", 7)
    df["fuel_stock_roll14_mean"]      = roll_mean("fuel_stock_liters", 14)
    df["fuel_stock_trend7"]           = trend_slope("fuel_stock_liters", 7)
    df["fuel_days_remaining_lag1"]    = lag("fuel_days_remaining", 1)
    df["fuel_days_remaining_roll7"]   = roll_mean("fuel_days_remaining", 7)
    df["days_since_refuel"]           = days_since_event(df["refuel_event"].shift(1))
    df["fuel_shipments_pending_lag1"] = lag("fuel_shipments_pending", 1)
    df["fuel_eta_days_lag1"]          = lag("fuel_eta_days", 1)
    df["fuel_critical_flag"]          = (df["fuel_days_remaining_lag1"] < 10).astype(float)

    # Battery
    df["battery_soc_lag1"]        = lag("battery_soc_percent", 1)
    df["battery_soc_lag3"]        = lag("battery_soc_percent", 3)
    df["battery_soc_roll7_mean"]  = roll_mean("battery_soc_percent", 7)
    df["battery_soc_roll7_std"]   = roll_std("battery_soc_percent", 7)
    df["battery_soc_trend7"]      = trend_slope("battery_soc_percent", 7)
    df["battery_soc_low_flag"]    = (df["battery_soc_lag1"] < 20).astype(float)
    df["battery_discharge_lag1"]  = lag("battery_discharge_kw", 1)

    # Power
    df["power_margin_lag1"]          = lag("power_margin_kw", 1)
    df["power_margin_roll7_mean"]    = roll_mean("power_margin_kw", 7)
    df["power_shortage_lag1"]        = lag("power_shortage_event", 1).astype(float)
    df["power_shortage_roll7_mean"]  = roll_mean("power_shortage_event", 7)
    df["overload_lag1"]              = lag("overload_flag", 1).astype(float)
    df["overload_roll7_mean"]        = roll_mean("overload_flag", 7)
    df["generator_output_lag1"]      = lag("generator_output_kw", 1)
    df["generator_output_roll7_mean"]= roll_mean("generator_output_kw", 7)
    df["renewable_share_lag1"]       = lag("renewable_share_percent", 1)
    df["renewable_share_roll7_mean"] = roll_mean("renewable_share_percent", 7)

    # Inventory
    df["inventory_health_lag1"]         = lag("inventory_health_score", 1)
    df["inventory_health_roll7_mean"]   = roll_mean("inventory_health_score", 7)
    df["inventory_health_roll14_mean"]  = roll_mean("inventory_health_score", 14)
    df["inventory_health_trend7"]       = trend_slope("inventory_health_score", 7)
    df["critical_items_lag1"]           = lag("critical_items", 1)
    df["critical_items_roll7_mean"]     = roll_mean("critical_items", 7)
    df["inventory_orders_pending_lag1"] = lag("inventory_orders_pending", 1)
    df["inventory_eta_days_lag1"]       = lag("inventory_eta_days", 1)
    df["days_since_last_delivery"]      = days_since_event(df["received_today"].shift(1) > 0)
    df["inventory_shortage_lag1"]       = (lag("inventory_shortage_items", 1) > 0).astype(float)

    # Water
    df["water_storage_lag1"]        = lag("water_storage_liters", 1)
    df["water_storage_roll7_mean"]  = roll_mean("water_storage_liters", 7)
    df["water_days_remaining_lag1"] = lag("water_days_remaining", 1)
    df["water_emergency_lag1"]      = lag("water_emergency", 1).astype(float)
    df["water_shortage_lag1"]       = lag("water_shortage_event", 1).astype(float)

    # Communication
    df["communication_outage_lag1"]       = lag("communication_outage_event", 1).astype(float)
    df["communication_outage_roll7_mean"] = roll_mean("communication_outage_event", 7)
    df["offline_duration_lag1"]           = lag("offline_duration_days", 1)
    df["signal_quality_lag1"]             = lag("signal_quality_percent", 1)
    df["signal_quality_roll7_mean"]       = roll_mean("signal_quality_percent", 7)
    df["bandwidth_lag1"]                  = lag("bandwidth_mbps", 1)
    df["packet_loss_lag1"]                = lag("packet_loss_percent", 1)

    # Weather obs (lagged)
    df["temperature_lag1"]           = lag("temperature_c", 1)
    df["temperature_roll7_mean"]     = roll_mean("temperature_c", 7)
    df["temperature_roll7_min"]      = roll_min("temperature_c", 7)
    df["extreme_cold_flag"]          = (df["temperature_lag1"] < -30).astype(float)
    df["wind_speed_lag1"]            = lag("wind_speed_kmh", 1)
    df["wind_speed_roll7_mean"]      = roll_mean("wind_speed_kmh", 7)
    df["wind_gust_lag1"]             = lag("wind_gust_kmh", 1)
    df["snowfall_lag1"]              = lag("snowfall_cm", 1)
    df["snowfall_roll7_mean"]        = roll_mean("snowfall_cm", 7)
    df["visibility_lag1"]            = lag("visibility_m", 1)
    df["weather_severity_lag1"]      = lag("weather_severity", 1)
    df["weather_severity_roll7_mean"]= roll_mean("weather_severity", 7)
    df["storm_flag"]                 = (df["weather_severity_lag1"] > 0.7).astype(float)

    # NWP weather forecasts for Day t+1
    df["fc_temperature"]          = df["temperature_c"].shift(-1)
    df["fc_wind_speed"]           = df["wind_speed_kmh"].shift(-1)
    df["fc_wind_gust"]            = df["wind_gust_kmh"].shift(-1)
    df["fc_snowfall"]             = df["snowfall_cm"].shift(-1)
    df["fc_pressure"]             = df["pressure_hpa"].shift(-1)
    df["fc_visibility"]           = df["visibility_m"].shift(-1)
    df["fc_weather_severity"]     = df["weather_severity"].shift(-1)
    df["fc_solar_daylight_hours"] = df["solar_daylight_hours"].shift(-1)

    # Crew schedule
    df["scheduled_population"] = df["total_population"].shift(-1)
    df["scheduled_scientists"] = df["scientists"].shift(-1)
    df["scheduled_engineers"]  = df["engineers"].shift(-1)
    df["high_population_flag"] = (df["scheduled_population"] >= 35).astype(float)

    # Calendar
    dt = pd.to_datetime(df["date"])
    df["month"]        = dt.dt.month
    df["day_of_year"]  = dt.dt.dayofyear
    doy = df["day_of_year"].values
    df["doy_sin"]          = np.sin(2 * np.pi * doy / 365.25)
    df["doy_cos"]          = np.cos(2 * np.pi * doy / 365.25)
    df["month_sin"]        = np.sin(2 * np.pi * df["month"].values / 12)
    df["month_cos"]        = np.cos(2 * np.pi * df["month"].values / 12)
    df["season_enc"]       = df["season"].map(SEASON_MAP).fillna(0).astype(int)
    df["polar_night_flag"] = (df["solar_daylight_hours"] < 1).astype(float)
    df["polar_day_flag"]   = (df["solar_daylight_hours"] > 20).astype(float)
    df["year"]             = dt.dt.year
    df["station_enc"]      = df["station_id"].map(STATION_MAP).fillna(0).astype(int)
    return df


def load_raw_corpus(deduplicate=False):
    hashes = detect_duplicate_runs(DATA_FILES)
    unique_runs = set()
    seen_hashes = set()
    for rn, h in hashes.items():
        if h not in seen_hashes:
            unique_runs.add(rn)
            seen_hashes.add(h)
    frames = []
    for i, fpath in enumerate(DATA_FILES, 1):
        if deduplicate and i not in unique_runs:
            logger.info("Skipping duplicate Run %d", i)
            continue
        logger.info("Processing simulation run %d: %s", i, fpath)
        raw = pd.read_csv(fpath, low_memory=False)
        raw["run_id"] = i
        raw["date"] = pd.to_datetime(raw["date"])
        processed = []
        for station, grp in raw.groupby("station_id", sort=False):
            processed.append(engineer_features(grp))
        frames.append(pd.concat(processed, ignore_index=True))
    corpus = pd.concat(frames, ignore_index=True)
    corpus = corpus.dropna(subset=[TARGET_NAME]).reset_index(drop=True)
    pos_rate = corpus[TARGET_NAME].mean()
    fp = sum(1 for c in FEATURE_COLS if c in corpus.columns)
    logger.info("Full corpus: %d rows, target pos=%.2f%%, features=%d/%d", len(corpus), pos_rate*100, fp, len(FEATURE_COLS))
    return corpus


def get_chronological_splits(corpus):
    year = pd.to_datetime(corpus["date"]).dt.year
    train = corpus[year.isin(TRAIN_YEARS)].reset_index(drop=True)
    val   = corpus[year.isin(VAL_YEARS)].reset_index(drop=True)
    test  = corpus[year.isin(TEST_YEARS)].reset_index(drop=True)
    logger.info("Splits -> Train: %d (pos=%.2f%%) | Val: %d (pos=%.2f%%) | Test: %d (pos=%.2f%%)",
        len(train), train[TARGET_NAME].mean()*100,
        len(val),   val[TARGET_NAME].mean()*100,
        len(test),  test[TARGET_NAME].mean()*100)
    return train, val, test


def get_loso_splits(corpus, deduplicated=False):
    hashes = detect_duplicate_runs(DATA_FILES)
    run_ids = sorted(corpus["run_id"].unique())
    if deduplicated:
        seen_h = {}
        unique_runs = []
        for rn, h in sorted(hashes.items()):
            if h not in seen_h:
                unique_runs.append(rn)
                seen_h[h] = rn
        run_ids = [r for r in run_ids if r in unique_runs]
    for held_out in run_ids:
        tv = corpus[corpus["run_id"] != held_out].reset_index(drop=True)
        te = corpus[corpus["run_id"] == held_out].reset_index(drop=True)
        yr = pd.to_datetime(tv["date"]).dt.year
        tr = tv[yr.isin(TRAIN_YEARS + VAL_YEARS)].reset_index(drop=True)
        yield held_out, tr, te


if __name__ == "__main__":
    corpus = load_raw_corpus()
    get_chronological_splits(corpus)
