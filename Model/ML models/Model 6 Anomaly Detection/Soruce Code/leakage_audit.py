# leakage_audit.py ? Model 6 V3: Full Feature Leakage Audit Matrix
# Classifies every candidate variable as:
#   SAFE       ? genuinely available at 18:00 Day t, no lookahead
#   HISTORICAL ? safe, lagged version of a raw column
#   LEAKAGE    ? involves Day t+1 realization (future)
#   TARGET-DERIVED ? derived from or co-linear with the anomaly target
#   REJECTED   ? excluded for any reason

import os
import csv
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LeakageAudit-Model6-V3")

from config import RESULTS_DIR

AUDIT_TABLE = [
    # (Feature, Classification, Decision, Reason)

    # ---- TARGET & DIRECTLY DERIVED ----
    ("OperationalAnomaly",            "TARGET-DERIVED", "REJECT", "This IS the base anomaly label at time t. Using it directly leaks same-day realization."),
    ("future_operational_anomaly",    "TARGET",         "TARGET", "Model target: shift(-1) of OperationalAnomaly. Labels Day t+1 outcome."),
    ("power_shortage_event",          "LEAKAGE",        "REJECT", "Same-day flag ? part of OperationalAnomaly definition. Using it directly replicates the target."),
    ("fuel_shortage_event",           "LEAKAGE",        "REJECT", "Same-day flag ? part of OperationalAnomaly definition."),
    ("water_emergency",               "LEAKAGE",        "REJECT", "Same-day flag ? part of OperationalAnomaly definition."),
    ("communication_outage_event",    "LEAKAGE",        "REJECT", "Same-day flag ? part of OperationalAnomaly definition."),
    ("overload_flag",                 "LEAKAGE",        "REJECT", "Same-day flag ? part of OperationalAnomaly definition."),

    # ---- RISK SCORES (simulator computed SAME DAY from same-day variables) ----
    ("overall_risk_score",            "TARGET-DERIVED", "REJECT", "Simulator risk score computed from same-day variables including anomaly components. Circular."),
    ("overall_risk_level",            "TARGET-DERIVED", "REJECT", "Categorical encoding of overall_risk_score. Same circularity."),
    ("risk_score",                    "TARGET-DERIVED", "REJECT", "Duplicate/alias of overall_risk_score."),
    ("risk_level",                    "TARGET-DERIVED", "REJECT", "Duplicate/alias of overall_risk_level."),
    ("power_risk",                    "TARGET-DERIVED", "REJECT", "Simulator risk sub-score derived from same-day power state including overload/shortage flags."),
    ("fuel_risk",                     "TARGET-DERIVED", "REJECT", "Simulator risk sub-score derived from same-day fuel variables."),
    ("inventory_risk",                "TARGET-DERIVED", "REJECT", "Simulator risk sub-score derived from same-day inventory variables."),
    ("weather_risk",                  "TARGET-DERIVED", "REJECT", "Simulator risk sub-score derived from same-day weather."),
    ("water_risk",                    "TARGET-DERIVED", "REJECT", "Simulator risk sub-score derived from same-day water state."),
    ("connectivity_risk",             "TARGET-DERIVED", "REJECT", "Simulator risk sub-score derived from same-day communication state."),
    ("occupancy_risk",                "TARGET-DERIVED", "REJECT", "Simulator risk sub-score from same-day occupancy."),
    ("top_risk_factor",               "TARGET-DERIVED", "REJECT", "Derived from risk score computation. Circular."),
    ("top_risk_reason",               "TARGET-DERIVED", "REJECT", "Derived from risk score computation. Circular."),
    ("risk_breakdown",                "TARGET-DERIVED", "REJECT", "JSON string encoding risk sub-scores. Circular."),
    ("station_health",                "TARGET-DERIVED", "REJECT", "Station health score computed from same-day risk scores. Circular."),

    # ---- TODAY'S REALIZATIONS (SAME-DAY LEAKAGE) ----
    ("fuel_consumed_today_liters",    "LEAKAGE",        "REJECT", "Today's fuel consumption realized at end of day ? not available at 18:00 for forecasting."),
    ("fuel_received_today_liters",    "LEAKAGE",        "REJECT", "Today's shipment arrival ? same-day realization."),
    ("refuel_event",                  "LEAKAGE",        "REJECT", "Same-day refueling indicator. Not predictable before 18:00."),
    ("refuel_quantity_liters",        "LEAKAGE",        "REJECT", "Same-day refuel amount."),
    ("fuel_shipment_created_today",   "LEAKAGE",        "REJECT", "Today's dispatch event ? same-day."),
    ("fuel_shipment_delayed_today",   "LEAKAGE",        "REJECT", "Today's delay event ? same-day."),
    ("water_refill_event",            "LEAKAGE",        "REJECT", "Same-day water event."),
    ("water_shortage_event",          "LEAKAGE",        "REJECT", "Same-day water shortage ? part of anomaly composite."),
    ("load_shedding_kwh",             "LEAKAGE",        "REJECT", "Same-day load shedding realized at end of day."),
    ("unserved_energy_kwh",           "LEAKAGE",        "REJECT", "Same-day unserved energy."),
    ("buffer_uploaded_today_mb",      "LEAKAGE",        "REJECT", "Same-day communication buffer ? end of day metric."),
    ("received_today",                "LEAKAGE",        "REJECT", "Same-day inventory receipt event."),
    ("inventory_orders_created_today","LEAKAGE",        "REJECT", "Same-day dispatch ? not known before 18:00 planning."),

    # ---- SAFE: LAGGED ANOMALY BEHAVIOUR ----
    ("anomaly_lag1",                  "HISTORICAL",     "ACCEPT", "Yesterday's anomaly ? known at 18:00 on Day t."),
    ("anomaly_lag2",                  "HISTORICAL",     "ACCEPT", "2 days ago anomaly ? known at 18:00 on Day t."),
    ("anomaly_lag3",                  "HISTORICAL",     "ACCEPT", "3 days ago anomaly ? known at 18:00 on Day t."),
    ("anomaly_lag7",                  "HISTORICAL",     "ACCEPT", "7 days ago anomaly ? known at 18:00 on Day t."),
    ("anomaly_roll7_mean",            "HISTORICAL",     "ACCEPT", "7-day rolling anomaly rate (shift-then-roll). No lookahead."),
    ("anomaly_roll14_mean",           "HISTORICAL",     "ACCEPT", "14-day rolling anomaly rate. Shift-then-roll."),
    ("anomaly_roll30_mean",           "HISTORICAL",     "ACCEPT", "30-day rolling anomaly frequency. Shift-then-roll."),
    ("anomaly_roll7_std",             "HISTORICAL",     "ACCEPT", "7-day rolling anomaly volatility. Shift-then-roll."),
    ("anomaly_ema7",                  "HISTORICAL",     "ACCEPT", "7-day exponential moving average of anomaly. Shift-then-roll."),
    ("anomaly_frequency30",           "HISTORICAL",     "ACCEPT", "30-day rolling sum of anomaly events."),
    ("anomaly_streak",                "HISTORICAL",     "ACCEPT", "Consecutive anomaly days up to Day t. No lookahead."),
    ("anomaly_free_streak",           "HISTORICAL",     "ACCEPT", "Consecutive clean days up to Day t. Leading indicator."),

    # ---- SAFE: FUEL SYSTEM ----
    ("fuel_stock_lag1",               "HISTORICAL",     "ACCEPT", "Fuel stock at end of yesterday ? known at 18:00 Day t."),
    ("fuel_stock_roll7_mean",         "HISTORICAL",     "ACCEPT", "7-day fuel stock rolling average. Shift-then-roll."),
    ("fuel_stock_roll14_mean",        "HISTORICAL",     "ACCEPT", "14-day fuel stock rolling average. Shift-then-roll."),
    ("fuel_stock_trend7",             "HISTORICAL",     "ACCEPT", "7-day linear fuel stock trend. Shift-then-roll."),
    ("fuel_days_remaining_lag1",      "HISTORICAL",     "ACCEPT", "Yesterday's fuel runway estimate ? known."),
    ("fuel_days_remaining_roll7",     "HISTORICAL",     "ACCEPT", "7-day rolling fuel runway. Shift-then-roll."),
    ("days_since_refuel",             "HISTORICAL",     "ACCEPT", "Days elapsed since last refueling ? known at Day t."),
    ("fuel_shipments_pending_lag1",   "HISTORICAL",     "ACCEPT", "Yesterday's pending shipments ? known."),
    ("fuel_eta_days_lag1",            "HISTORICAL",     "ACCEPT", "Yesterday's shipment ETA ? known."),
    ("fuel_critical_flag",            "SAFE",           "ACCEPT", "Derived from fuel_days_remaining_lag1 < 10. No lookahead."),

    # ---- SAFE: BATTERY ----
    ("battery_soc_lag1",              "HISTORICAL",     "ACCEPT", "Yesterday's battery SOC ? known at 18:00 Day t."),
    ("battery_soc_lag3",              "HISTORICAL",     "ACCEPT", "3-day lagged battery SOC."),
    ("battery_soc_roll7_mean",        "HISTORICAL",     "ACCEPT", "7-day rolling battery SOC. Shift-then-roll."),
    ("battery_soc_roll7_std",         "HISTORICAL",     "ACCEPT", "7-day rolling battery SOC std. Shift-then-roll."),
    ("battery_soc_trend7",            "HISTORICAL",     "ACCEPT", "7-day battery SOC trend. Shift-then-roll."),
    ("battery_soc_low_flag",          "SAFE",           "ACCEPT", "Derived from battery_soc_lag1 < 20. No lookahead."),
    ("battery_discharge_lag1",        "HISTORICAL",     "ACCEPT", "Yesterday's battery discharge rate ? known."),

    # ---- SAFE: POWER SYSTEM ----
    ("power_margin_lag1",             "HISTORICAL",     "ACCEPT", "Yesterday's power margin ? known."),
    ("power_margin_roll7_mean",       "HISTORICAL",     "ACCEPT", "7-day rolling power margin. Shift-then-roll."),
    ("power_shortage_lag1",           "HISTORICAL",     "ACCEPT", "Yesterday's power shortage event ? historical, not tomorrow."),
    ("power_shortage_roll7_mean",     "HISTORICAL",     "ACCEPT", "7-day rolling power shortage rate. Shift-then-roll."),
    ("overload_lag1",                 "HISTORICAL",     "ACCEPT", "Yesterday's overload flag ? historical."),
    ("overload_roll7_mean",           "HISTORICAL",     "ACCEPT", "7-day rolling overload rate. Shift-then-roll."),
    ("generator_output_lag1",         "HISTORICAL",     "ACCEPT", "Yesterday's generator output ? known."),
    ("generator_output_roll7_mean",   "HISTORICAL",     "ACCEPT", "7-day rolling generator output. Shift-then-roll."),
    ("renewable_share_lag1",          "HISTORICAL",     "ACCEPT", "Yesterday's renewable share ? known."),
    ("renewable_share_roll7_mean",    "HISTORICAL",     "ACCEPT", "7-day rolling renewable share. Shift-then-roll."),

    # ---- SAFE: INVENTORY ----
    ("inventory_health_lag1",         "HISTORICAL",     "ACCEPT", "Yesterday's inventory health score ? known."),
    ("inventory_health_roll7_mean",   "HISTORICAL",     "ACCEPT", "7-day rolling inventory health. Shift-then-roll."),
    ("inventory_health_roll14_mean",  "HISTORICAL",     "ACCEPT", "14-day rolling inventory health. Shift-then-roll."),
    ("inventory_health_trend7",       "HISTORICAL",     "ACCEPT", "7-day inventory health trend. Shift-then-roll."),
    ("critical_items_lag1",           "HISTORICAL",     "ACCEPT", "Yesterday's critical item count ? known."),
    ("critical_items_roll7_mean",     "HISTORICAL",     "ACCEPT", "7-day rolling critical items. Shift-then-roll."),
    ("inventory_orders_pending_lag1", "HISTORICAL",     "ACCEPT", "Yesterday's pending inventory orders ? known."),
    ("inventory_eta_days_lag1",       "HISTORICAL",     "ACCEPT", "Yesterday's inventory ETA ? known."),
    ("days_since_last_delivery",      "HISTORICAL",     "ACCEPT", "Days since last inventory delivery ? known at Day t."),
    ("inventory_shortage_lag1",       "HISTORICAL",     "ACCEPT", "Yesterday's inventory shortage flag ? historical."),

    # ---- SAFE: WATER ----
    ("water_storage_lag1",            "HISTORICAL",     "ACCEPT", "Yesterday's water storage level ? known."),
    ("water_storage_roll7_mean",      "HISTORICAL",     "ACCEPT", "7-day rolling water storage. Shift-then-roll."),
    ("water_days_remaining_lag1",     "HISTORICAL",     "ACCEPT", "Yesterday's water runway ? known."),
    ("water_emergency_lag1",          "HISTORICAL",     "ACCEPT", "Yesterday's water emergency flag ? historical."),
    ("water_shortage_lag1",           "HISTORICAL",     "ACCEPT", "Yesterday's water shortage flag ? historical."),

    # ---- SAFE: COMMUNICATION ----
    ("communication_outage_lag1",     "HISTORICAL",     "ACCEPT", "Yesterday's comms outage ? historical."),
    ("communication_outage_roll7_mean","HISTORICAL",    "ACCEPT", "7-day rolling comms outage rate. Shift-then-roll."),
    ("offline_duration_lag1",         "HISTORICAL",     "ACCEPT", "Yesterday's offline duration ? known."),
    ("signal_quality_lag1",           "HISTORICAL",     "ACCEPT", "Yesterday's signal quality ? known."),
    ("signal_quality_roll7_mean",     "HISTORICAL",     "ACCEPT", "7-day rolling signal quality. Shift-then-roll."),
    ("bandwidth_lag1",                "HISTORICAL",     "ACCEPT", "Yesterday's bandwidth ? known."),
    ("packet_loss_lag1",              "HISTORICAL",     "ACCEPT", "Yesterday's packet loss ? known."),

    # ---- SAFE: WEATHER OBSERVATIONS ----
    ("temperature_lag1",              "HISTORICAL",     "ACCEPT", "Yesterday's observed temperature ? known."),
    ("temperature_roll7_mean",        "HISTORICAL",     "ACCEPT", "7-day rolling temperature. Shift-then-roll."),
    ("temperature_roll7_min",         "HISTORICAL",     "ACCEPT", "7-day rolling minimum temperature. Shift-then-roll."),
    ("extreme_cold_flag",             "SAFE",           "ACCEPT", "Derived from temperature_lag1 < -30. No lookahead."),
    ("wind_speed_lag1",               "HISTORICAL",     "ACCEPT", "Yesterday's wind speed ? known."),
    ("wind_speed_roll7_mean",         "HISTORICAL",     "ACCEPT", "7-day rolling wind speed. Shift-then-roll."),
    ("wind_gust_lag1",                "HISTORICAL",     "ACCEPT", "Yesterday's wind gust ? known."),
    ("snowfall_lag1",                 "HISTORICAL",     "ACCEPT", "Yesterday's snowfall ? known."),
    ("snowfall_roll7_mean",           "HISTORICAL",     "ACCEPT", "7-day rolling snowfall. Shift-then-roll."),
    ("visibility_lag1",               "HISTORICAL",     "ACCEPT", "Yesterday's visibility ? known."),
    ("weather_severity_lag1",         "HISTORICAL",     "ACCEPT", "Yesterday's weather severity index ? known."),
    ("weather_severity_roll7_mean",   "HISTORICAL",     "ACCEPT", "7-day rolling weather severity. Shift-then-roll."),
    ("storm_flag",                    "SAFE",           "ACCEPT", "Derived from weather_severity_lag1 > 0.7. No lookahead."),

    # ---- SAFE: WEATHER FORECASTS (Day t+1 NWP forecast available at 18:00) ----
    ("fc_temperature",                "FORECAST",       "ACCEPT", "NWP forecast for Day t+1 temperature ? available at 18:00 Day t."),
    ("fc_wind_speed",                 "FORECAST",       "ACCEPT", "NWP forecast for Day t+1 wind speed ? available at 18:00 Day t."),
    ("fc_wind_gust",                  "FORECAST",       "ACCEPT", "NWP forecast for Day t+1 wind gust ? available at 18:00 Day t."),
    ("fc_snowfall",                   "FORECAST",       "ACCEPT", "NWP forecast for Day t+1 snowfall ? available at 18:00 Day t."),
    ("fc_pressure",                   "FORECAST",       "ACCEPT", "NWP forecast for Day t+1 pressure ? available at 18:00 Day t."),
    ("fc_visibility",                 "FORECAST",       "ACCEPT", "NWP forecast for Day t+1 visibility ? available at 18:00 Day t."),
    ("fc_weather_severity",           "FORECAST",       "ACCEPT", "NWP forecast severity proxy for Day t+1 ? available at 18:00 Day t."),
    ("fc_solar_daylight_hours",       "FORECAST",       "ACCEPT", "Astronomical daylight hours for Day t+1 ? deterministic and known."),

    # ---- SAFE: CREW SCHEDULE ----
    ("scheduled_population",          "SAFE",           "ACCEPT", "Tomorrow's scheduled crew ? typically fixed from manifest 24h+ in advance."),
    ("scheduled_scientists",          "SAFE",           "ACCEPT", "Tomorrow's scheduled scientist count ? from crew manifest."),
    ("scheduled_engineers",           "SAFE",           "ACCEPT", "Tomorrow's scheduled engineer count ? from crew manifest."),
    ("high_population_flag",          "SAFE",           "ACCEPT", "Derived from scheduled_population >= 35. No lookahead."),

    # ---- SAFE: CALENDAR ----
    ("month",                         "SAFE",           "ACCEPT", "Calendar month ? deterministic."),
    ("day_of_year",                   "SAFE",           "ACCEPT", "Day of year ? deterministic."),
    ("doy_sin",                       "SAFE",           "ACCEPT", "Cyclical encoding of day_of_year."),
    ("doy_cos",                       "SAFE",           "ACCEPT", "Cyclical encoding of day_of_year."),
    ("month_sin",                     "SAFE",           "ACCEPT", "Cyclical encoding of month."),
    ("month_cos",                     "SAFE",           "ACCEPT", "Cyclical encoding of month."),
    ("season_enc",                    "SAFE",           "ACCEPT", "Season integer encoding ? deterministic."),
    ("polar_night_flag",              "SAFE",           "ACCEPT", "Polar night indicator from daylight hours ? deterministic."),
    ("polar_day_flag",                "SAFE",           "ACCEPT", "Polar day indicator from daylight hours ? deterministic."),
    ("year",                          "SAFE",           "ACCEPT", "Calendar year ? deterministic."),
    ("station_enc",                   "SAFE",           "ACCEPT", "Station integer encoding (0=BHARATI, 1=MAITRI)."),

    # ---- REJECTED RAW COLUMNS (today's realization) ----
    ("temperature_c",                 "LEAKAGE",        "REJECT", "Today's realized temperature ? replaced by lagged/forecast version."),
    ("wind_speed_kmh",                "LEAKAGE",        "REJECT", "Today's realized wind ? replaced by lag/forecast."),
    ("wind_gust_kmh",                 "LEAKAGE",        "REJECT", "Today's realized gust ? replaced by lag/forecast."),
    ("fuel_stock_liters",             "LEAKAGE",        "REJECT", "Today's fuel stock realized ? replaced by lag."),
    ("fuel_days_remaining",           "LEAKAGE",        "REJECT", "Today's fuel runway ? replaced by lag."),
    ("battery_soc_percent",           "LEAKAGE",        "REJECT", "Today's battery SOC realized ? replaced by lag."),
    ("generator_output_kw",           "LEAKAGE",        "REJECT", "Today's generator output ? replaced by lag."),
    ("total_load_kw",                 "LEAKAGE",        "REJECT", "Today's total load ? same-day realization."),
    ("power_margin_kw",               "LEAKAGE",        "REJECT", "Today's power margin ? same-day realization."),
    ("inventory_health_score",        "LEAKAGE",        "REJECT", "Today's inventory health ? replaced by lag."),
    ("water_storage_liters",          "LEAKAGE",        "REJECT", "Today's water storage ? replaced by lag."),
    ("water_days_remaining",          "LEAKAGE",        "REJECT", "Today's water runway ? replaced by lag."),
    ("signal_quality_percent",        "LEAKAGE",        "REJECT", "Today's signal quality ? replaced by lag."),
    ("bandwidth_mbps",                "LEAKAGE",        "REJECT", "Today's bandwidth ? replaced by lag."),
    ("offline_duration_days",         "LEAKAGE",        "REJECT", "Today's offline duration ? replaced by lag."),
    ("packet_loss_percent",           "LEAKAGE",        "REJECT", "Today's packet loss ? replaced by lag."),
    ("generator_runtime_hours",       "LEAKAGE",        "REJECT", "Today's generator runtime ? same-day realization."),
    ("solar_generation_kw",           "LEAKAGE",        "REJECT", "Today's solar generation ? same-day realization."),
    ("renewable_share_percent",       "LEAKAGE",        "REJECT", "Today's renewable share ? replaced by lag."),
]


def run_leakage_audit():
    logger = logging.getLogger("LeakageAudit-Model6-V3")
    logger.info("=" * 60)
    logger.info("LEAKAGE AUDIT ? MODEL 6 V3: DAY-AHEAD OPERATIONAL RISK FORECAST")
    logger.info("=" * 60)

    accepted = [(f, c, d, r) for f, c, d, r in AUDIT_TABLE if d == "ACCEPT"]
    rejected = [(f, c, d, r) for f, c, d, r in AUDIT_TABLE if d == "REJECT"]
    targets  = [(f, c, d, r) for f, c, d, r in AUDIT_TABLE if d == "TARGET"]

    logger.info("Total entries audited: %d", len(AUDIT_TABLE))
    logger.info("  Accepted features:   %d", len(accepted))
    logger.info("  Rejected features:   %d", len(rejected))
    logger.info("  Target:              %d", len(targets))

    out_path = os.path.join(RESULTS_DIR, "model6_feature_leakage_audit.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Feature", "Classification", "Decision", "Reason"])
        for row in AUDIT_TABLE:
            writer.writerow(row)

    logger.info("Leakage audit saved to: %s", out_path)
    return out_path


if __name__ == "__main__":
    run_leakage_audit()
