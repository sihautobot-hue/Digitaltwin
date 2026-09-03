# leakage_audit.py -- Full Feature Leakage Audit
import os, sys, csv, logging
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LeakageAudit-Model6-V3")
from config import RESULTS_DIR

AUDIT_TABLE = [
    ("OperationalAnomaly",            "TARGET-DERIVED", "REJECT", "Base anomaly label at time t. Using directly leaks same-day outcome."),
    ("future_operational_anomaly",    "TARGET",         "TARGET", "Model target: shift(-1) of OperationalAnomaly. Labels Day t+1."),
    ("power_shortage_event",          "LEAKAGE",        "REJECT", "Same-day flag composing OperationalAnomaly."),
    ("fuel_shortage_event",           "LEAKAGE",        "REJECT", "Same-day flag composing OperationalAnomaly."),
    ("water_emergency",               "LEAKAGE",        "REJECT", "Same-day flag composing OperationalAnomaly."),
    ("communication_outage_event",    "LEAKAGE",        "REJECT", "Same-day flag composing OperationalAnomaly."),
    ("overload_flag",                 "LEAKAGE",        "REJECT", "Same-day flag composing OperationalAnomaly."),
    ("overall_risk_score",            "TARGET-DERIVED", "REJECT", "Simulator risk score computed from same-day variables. Circular."),
    ("overall_risk_level",            "TARGET-DERIVED", "REJECT", "Categorical encoding of overall_risk_score. Circular."),
    ("risk_score",                    "TARGET-DERIVED", "REJECT", "Duplicate of overall_risk_score."),
    ("risk_level",                    "TARGET-DERIVED", "REJECT", "Duplicate of overall_risk_level."),
    ("power_risk",                    "TARGET-DERIVED", "REJECT", "Simulator risk sub-score from same-day power state."),
    ("fuel_risk",                     "TARGET-DERIVED", "REJECT", "Simulator risk sub-score from same-day fuel state."),
    ("inventory_risk",                "TARGET-DERIVED", "REJECT", "Simulator risk sub-score from same-day inventory."),
    ("weather_risk",                  "TARGET-DERIVED", "REJECT", "Simulator risk sub-score from same-day weather."),
    ("water_risk",                    "TARGET-DERIVED", "REJECT", "Simulator risk sub-score from same-day water state."),
    ("connectivity_risk",             "TARGET-DERIVED", "REJECT", "Simulator risk sub-score from same-day connectivity."),
    ("occupancy_risk",                "TARGET-DERIVED", "REJECT", "Simulator risk sub-score from same-day occupancy."),
    ("station_health",                "TARGET-DERIVED", "REJECT", "Station health score computed from same-day risk scores."),
    ("fuel_consumed_today_liters",    "LEAKAGE",        "REJECT", "Today fuel consumption realized at end of day."),
    ("fuel_received_today_liters",    "LEAKAGE",        "REJECT", "Today shipment arrival realization."),
    ("refuel_event",                  "LEAKAGE",        "REJECT", "Same-day refueling indicator."),
    ("water_refill_event",            "LEAKAGE",        "REJECT", "Same-day water refill event."),
    ("load_shedding_kwh",             "LEAKAGE",        "REJECT", "Same-day load shedding realization."),
    ("unserved_energy_kwh",           "LEAKAGE",        "REJECT", "Same-day unserved energy."),
    ("buffer_uploaded_today_mb",      "LEAKAGE",        "REJECT", "Same-day communication buffer upload."),
    ("received_today",                "LEAKAGE",        "REJECT", "Same-day inventory receipt."),
    ("anomaly_lag1",                  "HISTORICAL",     "ACCEPT", "Yesterday anomaly -- available at 18:00 Day t."),
    ("anomaly_roll7_mean",            "HISTORICAL",     "ACCEPT", "7-day rolling anomaly rate (shift-then-roll)."),
    ("anomaly_frequency30",           "HISTORICAL",     "ACCEPT", "30-day rolling sum of anomalies."),
    ("anomaly_streak",                "HISTORICAL",     "ACCEPT", "Consecutive anomaly days up to Day t."),
    ("fuel_stock_lag1",               "HISTORICAL",     "ACCEPT", "Yesterday fuel stock -- known at 18:00 Day t."),
    ("fuel_days_remaining_lag1",      "HISTORICAL",     "ACCEPT", "Yesterday fuel runway -- known."),
    ("days_since_refuel",             "HISTORICAL",     "ACCEPT", "Days elapsed since last refueling."),
    ("battery_soc_lag1",              "HISTORICAL",     "ACCEPT", "Yesterday battery SOC -- known at 18:00."),
    ("battery_soc_roll7_mean",        "HISTORICAL",     "ACCEPT", "7-day rolling battery SOC (shift-then-roll)."),
    ("power_margin_lag1",             "HISTORICAL",     "ACCEPT", "Yesterday power margin -- known."),
    ("inventory_health_lag1",         "HISTORICAL",     "ACCEPT", "Yesterday inventory health -- known."),
    ("water_storage_lag1",            "HISTORICAL",     "ACCEPT", "Yesterday water storage -- known."),
    ("signal_quality_lag1",           "HISTORICAL",     "ACCEPT", "Yesterday signal quality -- known."),
    ("temperature_lag1",              "HISTORICAL",     "ACCEPT", "Yesterday temperature -- known."),
    ("wind_speed_lag1",               "HISTORICAL",     "ACCEPT", "Yesterday wind speed -- known."),
    ("fc_temperature",                "FORECAST",       "ACCEPT", "NWP forecast for Day t+1 temperature -- available at 18:00."),
    ("fc_wind_speed",                 "FORECAST",       "ACCEPT", "NWP forecast for Day t+1 wind speed -- available at 18:00."),
    ("fc_weather_severity",           "FORECAST",       "ACCEPT", "NWP forecast severity index for Day t+1."),
    ("scheduled_population",          "SAFE",           "ACCEPT", "Tomorrow scheduled crew from roster manifest."),
    ("month",                         "SAFE",           "ACCEPT", "Calendar month -- deterministic."),
    ("day_of_year",                   "SAFE",           "ACCEPT", "Day of year -- deterministic."),
    ("polar_night_flag",              "SAFE",           "ACCEPT", "Polar night indicator from solar astronomy.")
]

def run_leakage_audit():
    logger.info("Running Leakage Audit ...")
    out_path = os.path.join(RESULTS_DIR, "model6_feature_leakage_audit.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Feature", "Classification", "Decision", "Reason"])
        for row in AUDIT_TABLE:
            writer.writerow(row)
    logger.info("Saved: %s", out_path)
    return out_path

if __name__ == "__main__":
    run_leakage_audit()
