"""
leakage_audit.py
----------------
Exhaustive scientific leakage audit for Model 1 (Version 3).
Audits all 118 raw simulation columns and derived candidates against the
prediction contract (18:00 cutoff on Day t, predicting Day t+1 load).

Classifications:
  - SAFE: Information known in advance or forecast-safe external inputs
  - HISTORICAL: Observed operational history up to Day t (t <= 0)
  - LEAKAGE: Target-derived, same-day outcome, or post-event simulator variable
  - UNKNOWN: Ambiguous timing or provenance (rejected by default)
"""

import os
import pandas as pd

AUDIT_RULES = [
    # ── ALGEBRAIC IDENTITIES & DOWNSTREAM ENERGY BALANCES (CRITICAL LEAKAGE) ───
    ("total_load_kw", "LEAKAGE", "Raw target variable itself. Must be shifted to t+1 to serve as the predictand.", "REMOVE FROM FEATURES"),
    ("daily_load_energy_kwh", "LEAKAGE", "Algebraic identity: equals total_load_kw * 24. Exact numerical encoding of target.", "REJECT"),
    ("generator_energy_kwh", "LEAKAGE", "Downstream integrated generation to serve load. Direct energy balance leakage.", "REJECT"),
    ("solar_energy_kwh", "LEAKAGE", "Downstream integrated solar generation. Simultaneous same-day energy balance outcome.", "REJECT"),
    ("solar_to_load_kwh", "LEAKAGE", "Downstream dispatch component: solar electricity directed to load during the day.", "REJECT"),
    ("battery_to_load_kwh", "LEAKAGE", "Downstream dispatch component: battery electricity delivered to load during the day.", "REJECT"),
    ("unserved_energy_kwh", "LEAKAGE", "Downstream deficit computed directly from load minus total power supply.", "REJECT"),
    ("load_shedding_kwh", "LEAKAGE", "Emergency curtailment dispatched when total load exceeds available capacity.", "REJECT"),
    ("overload_flag", "LEAKAGE", "Post-event binary flag indicating peak load exceeded station generator rating.", "REJECT"),
    ("power_shortage_event", "LEAKAGE", "Post-event boolean flag triggered when total load could not be fully served.", "REJECT"),

    # ── SUB-LOAD SUMMATION COMPONENTS (DIRECT SUM LEAKAGE) ─────────────────────
    ("accommodation_load_kw", "LEAKAGE", "Direct sub-load component of total load. Summing sub-loads yields target.", "REJECT"),
    ("laboratory_load_kw", "LEAKAGE", "Direct sub-load component of total load. Summing sub-loads yields target.", "REJECT"),
    ("kitchen_load_kw", "LEAKAGE", "Direct sub-load component of total load. Summing sub-loads yields target.", "REJECT"),
    ("heating_load_kw", "LEAKAGE", "Direct sub-load component of total load. Replaced by forecast heating degree days.", "REJECT"),
    ("water_plant_load_kw", "LEAKAGE", "Direct sub-load component of total load. Summing sub-loads yields target.", "REJECT"),
    ("communication_load_kw", "LEAKAGE", "Direct sub-load component of total load. Summing sub-loads yields target.", "REJECT"),
    ("lighting_load_kw", "LEAKAGE", "Direct sub-load component of total load. Replaced by astronomical daylight hours.", "REJECT"),
    ("emergency_load_kw", "LEAKAGE", "Direct sub-load component of total load. Summing sub-loads yields target.", "REJECT"),

    # ── SAME-DAY DISPATCH & OPERATIONAL OUTCOMES (POST-EVENT LEAKAGE) ──────────
    ("generator_output_kw", "LEAKAGE", "Dispatched electrical output across generators to match load during Day t+1.", "REJECT"),
    ("generator_runtime_hours", "LEAKAGE", "Cumulative hours generator ran during Day t+1. Unknown until end of day.", "REJECT"),
    ("generator_status", "LEAKAGE", "Post-hoc operating regime (e.g. OVERLOAD, HIGH) derived from dispatch during day.", "REJECT"),
    ("active_generators", "LEAKAGE", "Staged generator units dispatched during Day t+1 to follow electrical demand.", "REJECT"),
    ("power_margin_kw", "LEAKAGE", "Difference between generator capacity and total load during Day t+1.", "REJECT"),
    ("renewable_share_percent", "LEAKAGE", "Ratio of renewable generation to total load. Explicitly target-derived.", "REJECT"),
    ("per_capita_load", "LEAKAGE", "Ratio of total load to population on Day t+1. Directly leaks target.", "REJECT"),
    ("battery_charge_kw", "LEAKAGE", "Intra-day power flow into battery. Result of generation dispatch during Day t+1.", "REJECT"),
    ("battery_discharge_kw", "LEAKAGE", "Intra-day power flow out of battery. Result of generation dispatch during Day t+1.", "REJECT"),
    ("solar_generation_kw", "LEAKAGE", "Simultaneous same-day solar output. Replaced by NWP solar irradiance forecast.", "REJECT"),
    ("chp_waste_heat_kw", "LEAKAGE", "Waste heat output produced during Day t+1 generator run. Replaced by Lag-1 heat.", "REJECT"),
    ("fuel_consumed_today_liters", "LEAKAGE", "Post-event fuel consumed during Day t+1. Downstream generator outcome.", "REJECT"),
    ("fuel_efficiency_l_per_kwh", "LEAKAGE", "Post-hoc efficiency ratio derived from fuel consumed and generator kWh.", "REJECT"),

    # ── POST-EVENT COMPOSITE RISK & HEALTH SCORES ──────────────────────────────
    ("power_risk", "LEAKAGE", "Power risk index computed at the end of Day t+1 after load shedding and outages.", "REJECT (Use Lag-1)"),
    ("overall_risk_score", "LEAKAGE", "Composite station risk index calculated at end of Day t+1. Use Lag-1.", "REJECT (Use Lag-1)"),
    ("overall_risk_level", "LEAKAGE", "Categorical risk level assigned post-event on Day t+1.", "REJECT"),
    ("station_health", "LEAKAGE", "Composite station health computed post-event on Day t+1.", "REJECT"),
    ("top_risk_factor", "LEAKAGE", "Post-event diagnostic text assigned after all daily incidents occur.", "REJECT"),
    ("top_risk_reason", "LEAKAGE", "Post-event diagnostic text assigned after all daily incidents occur.", "REJECT"),
    ("risk_breakdown", "LEAKAGE", "Detailed risk breakdown text produced at end of day.", "REJECT"),

    # ── POST-EVENT WATER & INVENTORY OUTCOMES ──────────────────────────────────
    ("daily_water_consumption_liters", "LEAKAGE", "Same-day water consumption during Day t+1.", "REJECT"),
    ("daily_water_production_liters", "LEAKAGE", "Same-day water produced during Day t+1 by snow melter.", "REJECT"),
    ("water_balance_liters", "LEAKAGE", "Daily water storage delta at end of Day t+1.", "REJECT"),
    ("water_emergency", "LEAKAGE", "Emergency flag declared during Day t+1.", "REJECT"),
    ("water_refill_event", "LEAKAGE", "Refill action taken during Day t+1.", "REJECT"),
    ("water_shortage_event", "LEAKAGE", "Shortage event occurring during Day t+1.", "REJECT"),
    ("refuel_event", "LEAKAGE", "Refueling action taken during Day t+1.", "REJECT"),
    ("refuel_quantity_liters", "LEAKAGE", "Fuel liters received during Day t+1.", "REJECT"),
    ("fuel_received_today_liters", "LEAKAGE", "Fuel received during Day t+1.", "REJECT"),
    ("fuel_shortage_event", "LEAKAGE", "Shortage event occurring during Day t+1.", "REJECT"),
    ("fuel_shipment_created_today", "LEAKAGE", "Logistics order created during Day t+1.", "REJECT"),
    ("fuel_shipment_delayed_today", "LEAKAGE", "Logistics delay recorded during Day t+1.", "REJECT"),

    # ── SAFE CALENDAR & ASTRONOMICAL GEOMETRY (KNOWN IN ADVANCE FOR t+1) ───────
    ("date", "SAFE", "Calendar date of Day t+1. Known precisely in advance by definition.", "KEEP (Extract time features)"),
    ("month_sin / month_cos", "SAFE", "Trigonometric cyclic encoding of month for Day t+1. Known astronomically.", "KEEP"),
    ("doy_sin / doy_cos", "SAFE", "Trigonometric cyclic encoding of day of year for Day t+1. Known astronomically.", "KEEP"),
    ("dow_sin / dow_cos", "SAFE", "Trigonometric cyclic encoding of day of week for Day t+1. Known in advance.", "KEEP"),
    ("is_shipping_season", "SAFE", "Scheduled Antarctic operational season (Nov–Mar). Calendar based.", "KEEP"),
    ("is_polar_night", "SAFE", "Astronomical flag: sun stays below horizon for 24h on Day t+1. Pure ephemeris.", "KEEP"),
    ("is_polar_day", "SAFE", "Astronomical flag: continuous 24h sunlight on Day t+1. Pure ephemeris.", "KEEP"),
    ("solar_elevation_deg", "SAFE", "Noon solar elevation angle for Day t+1. Deterministic orbital mechanics.", "KEEP (fc_solar_elevation_deg)"),
    ("solar_daylight_hours", "SAFE", "Theoretical daylight duration for Day t+1. Deterministic orbital mechanics.", "KEEP (fc_solar_daylight_hours)"),

    # ── SAFE DAY-AHEAD NWP WEATHER FORECASTS (FOR DAY t+1) ─────────────────────
    ("fc_temperature_c", "SAFE", "Numerical Weather Prediction (NWP) forecast of mean ambient temperature for Day t+1.", "KEEP"),
    ("fc_wind_speed_kmh", "SAFE", "NWP forecast of mean wind speed for Day t+1.", "KEEP"),
    ("fc_wind_gust_kmh", "SAFE", "NWP forecast of maximum wind gusts for Day t+1.", "KEEP"),
    ("fc_solar_radiation_wm2", "SAFE", "NWP forecast of solar irradiance for Day t+1.", "KEEP"),
    ("fc_snowfall_cm", "SAFE", "NWP forecast of snowfall precipitation for Day t+1.", "KEEP"),
    ("fc_snow_depth_cm", "SAFE", "NWP forecast of snow pack depth for Day t+1.", "KEEP"),
    ("fc_weather_severity", "SAFE", "NWP forecast of meteorological storm severity index for Day t+1.", "KEEP"),
    ("fc_weather_type_enc", "SAFE", "NWP forecast of weather regime classification (blizzard, whiteout, clear).", "KEEP"),
    ("fc_wind_chill_c", "SAFE", "Derived physical index from NWP forecast wind speed and temperature.", "KEEP"),
    ("fc_katabatic_index", "SAFE", "Derived katabatic proxy from NWP wind and negative temperature.", "KEEP"),
    ("fc_heating_degree_days", "SAFE", "Physical thermodynamic heating driver derived from forecast temperature.", "KEEP"),

    # ── SAFE SCHEDULED POPULATION & ROSTER (KNOWN FOR DAY t+1) ─────────────────
    ("scheduled_population", "SAFE", "Pre-planned station personnel roster for Day t+1.", "KEEP"),
    ("scheduled_occupancy_pct", "SAFE", "Scheduled capacity utilization percentage for Day t+1.", "KEEP"),
    ("scheduled_scientists", "SAFE", "Scheduled scientific personnel (primary lab power driver) for Day t+1.", "KEEP"),
    ("scheduled_engineers", "SAFE", "Scheduled station engineering and utilities personnel for Day t+1.", "KEEP"),
    ("scheduled_technicians", "SAFE", "Scheduled technical and workshop staff for Day t+1.", "KEEP"),
    ("scheduled_medical", "SAFE", "Scheduled medical bay staff for Day t+1.", "KEEP"),

    # ── HISTORICAL TELEMETRY (OBSERVED STRICTLY UP TO 18:00 OF DAY t) ──────────
    ("load_lag1", "HISTORICAL", "Observed electrical demand on Day t. Fully available at 18:00 cutoff.", "KEEP"),
    ("load_lag2", "HISTORICAL", "Observed electrical demand on Day t-1 (48h prior).", "KEEP"),
    ("load_lag3", "HISTORICAL", "Observed electrical demand on Day t-2 (72h prior).", "KEEP"),
    ("load_lag7", "HISTORICAL", "Observed electrical demand on same day last week (168h prior).", "KEEP"),
    ("load_lag14", "HISTORICAL", "Observed electrical demand 2 weeks ago (336h prior).", "KEEP"),
    ("load_roll3_mean", "HISTORICAL", "3-day trailing rolling mean load [t-2, t]. Shifted before rolling.", "KEEP"),
    ("load_roll7_mean", "HISTORICAL", "7-day trailing rolling mean load [t-6, t]. Shifted before rolling.", "KEEP"),
    ("load_roll14_mean", "HISTORICAL", "14-day trailing rolling mean load [t-13, t]. Shifted before rolling.", "KEEP"),
    ("load_roll30_mean", "HISTORICAL", "30-day trailing rolling mean load [t-29, t]. Shifted before rolling.", "KEEP"),
    ("load_roll7_std", "HISTORICAL", "7-day trailing load volatility. Shifted before rolling.", "KEEP"),
    ("load_roll14_std", "HISTORICAL", "14-day trailing load volatility. Shifted before rolling.", "KEEP"),
    ("load_trend_3d", "HISTORICAL", "Short-term demand trajectory (load_lag1 - load_lag3).", "KEEP"),
    ("load_trend_7d", "HISTORICAL", "Weekly demand trajectory (load_lag1 - load_lag7).", "KEEP"),
    ("obs_temp_lag1", "HISTORICAL", "Observed ambient temperature on Day t.", "KEEP"),
    ("obs_temp_lag2", "HISTORICAL", "Observed ambient temperature on Day t-1.", "KEEP"),
    ("obs_temp_lag3", "HISTORICAL", "Observed ambient temperature on Day t-2.", "KEEP"),
    ("obs_temp_roll7_mean", "HISTORICAL", "7-day trailing mean observed temperature (thermal inertia proxy).", "KEEP"),
    ("obs_temp_trend3", "HISTORICAL", "3-day observed cooling/warming trajectory.", "KEEP"),
    ("obs_wind_lag1", "HISTORICAL", "Observed wind speed on Day t.", "KEEP"),
    ("obs_wind_roll7_mean", "HISTORICAL", "7-day trailing mean wind speed.", "KEEP"),
    ("obs_weather_sev_lag1", "HISTORICAL", "Observed weather severity on Day t.", "KEEP"),
    ("obs_weather_sev_roll7", "HISTORICAL", "7-day trailing mean weather severity.", "KEEP"),
    ("pop_lag1", "HISTORICAL", "Actual observed population on Day t.", "KEEP"),
    ("pop_trend7", "HISTORICAL", "7-day net population shift.", "KEEP"),
    ("battery_soc_start_pct", "HISTORICAL", "Battery State of Charge observed at 18:00 cutoff on Day t.", "KEEP"),
    ("soc_lag1", "HISTORICAL", "Battery State of Charge on Day t-1.", "KEEP"),
    ("soc_delta_lag1", "HISTORICAL", "Rate of battery charge/discharge over past 24h.", "KEEP"),
    ("fuel_stock_start_liters", "HISTORICAL", "Fuel tank level observed at 18:00 cutoff on Day t.", "KEEP"),
    ("days_since_refuel_start", "HISTORICAL", "Elapsed days since previous refueling event.", "KEEP"),
    ("chp_heat_lag1", "HISTORICAL", "Generator waste heat recovered on Day t (thermal offset proxy).", "KEEP"),
    ("chp_heat_roll7_mean", "HISTORICAL", "7-day trailing average CHP waste heat contribution.", "KEEP"),
    ("power_risk_lag1", "HISTORICAL", "Power risk score observed on Day t.", "KEEP"),
    ("overall_risk_lag1", "HISTORICAL", "Composite station risk score observed on Day t.", "KEEP"),
    ("risk_roll7_mean", "HISTORICAL", "7-day trailing average composite station risk score.", "KEEP"),
    ("station_enc", "HISTORICAL", "Static physical station identifier (Maitri vs Bharati).", "KEEP"),
]

def generate_audit_report():
    df = pd.DataFrame(AUDIT_RULES, columns=["Feature", "Classification", "Reason", "Decision"])
    return df

if __name__ == "__main__":
    df_audit = generate_audit_report()
    out_path = os.path.join(os.path.dirname(__file__), "results_v3", "feature_leakage_audit.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df_audit.to_csv(out_path, index=False)
    print("=" * 80)
    print("SCIENTIFIC LEAKAGE AUDIT SUMMARY")
    print("=" * 80)
    print(df_audit["Classification"].value_counts())
    print(f"\nAudit table saved to: {out_path}")
