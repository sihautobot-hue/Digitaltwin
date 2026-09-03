"""
feature_audit.py
----------------
Exhaustive scientific feature audit for Model 1 (Power Load Forecast V3).
Evaluates all simulator variables for:
  - Availability at prediction timestamp (06:00, t=0)
  - Leakage risk (algebraic identity, same-day outcome, target contamination)
  - Action taken: KEEP, REMOVE, REPLACE, ENGINEER NEW
"""

import pandas as pd

AUDIT_DATA = [
    # ── IDENTITIES / DIRECT TARGET LEAKAGE ─────────────────────────────────────
    {
        "Feature": "daily_load_energy_kwh",
        "Known at 06:00": "NO",
        "Leakage Risk": "CRITICAL (Algebraic Identity)",
        "Reason": "Equals total_load_kw × 24 exactly. Directly leaks the continuous target value.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "generator_energy_kwh",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Post-Event Outcome)",
        "Reason": "Energy dispatched to meet load during the day. Directly proportional to load.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "solar_to_load_kwh",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Post-Event Outcome)",
        "Reason": "Solar energy actually routed to load during the day. Part of daily energy balance.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "battery_to_load_kwh",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Post-Event Outcome)",
        "Reason": "Battery energy delivered to load during the day. Part of daily energy balance.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "unserved_energy_kwh",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Post-Event Outcome)",
        "Reason": "Shortfall computed from total load minus total generation capacity.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "overload_flag",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Post-Event State)",
        "Reason": "Boolean flag indicating whether peak load exceeded generator threshold.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "load_shedding_kwh",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Post-Event Action)",
        "Reason": "Emergency load shed during the day, directly triggered by load surge.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "power_shortage_event",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Post-Event Outcome)",
        "Reason": "Event triggered when station load cannot be fully served.",
        "Decision": "REMOVE"
    },

    # ── SUB-LOAD SUMMATION COMPONENTS ──────────────────────────────────────────
    {
        "Feature": "accommodation_load_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Sub-component Sum)",
        "Reason": "Sub-load component of today's target. Sum of sub-loads = total_load_kw.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "laboratory_load_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Sub-component Sum)",
        "Reason": "Sub-load component of today's target. Sum of sub-loads = total_load_kw.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "kitchen_load_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Sub-component Sum)",
        "Reason": "Sub-load component of today's target. Sum of sub-loads = total_load_kw.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "heating_load_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Sub-component Sum)",
        "Reason": "Sub-load component of today's target. Replaced by thermodynamic weather drivers.",
        "Decision": "REPLACE (with NWP forecast temperature & wind chill)"
    },
    {
        "Feature": "water_plant_load_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Sub-component Sum)",
        "Reason": "Sub-load component of today's target.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "communication_load_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Sub-component Sum)",
        "Reason": "Sub-load component of today's target.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "lighting_load_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Sub-component Sum)",
        "Reason": "Sub-load component of today's target. Replaced by astronomical daylight hours.",
        "Decision": "REPLACE (with solar daylight hours)"
    },
    {
        "Feature": "emergency_load_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Sub-component Sum)",
        "Reason": "Sub-load component of today's target.",
        "Decision": "REMOVE"
    },

    # ── SAME-DAY DISPATCH & OPERATIONAL OUTCOMES ────────────────────────────────
    {
        "Feature": "generator_output_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Simultaneous Dispatch)",
        "Reason": "Electrical generation dispatched during the day to match load demand.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "generator_runtime_hours",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Post-Event Duration)",
        "Reason": "Total hours genset ran during the forecast day.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "generator_status",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Post-Event Status)",
        "Reason": "Full-day generator status classification.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "active_generators",
        "Known at 06:00": "NO",
        "Leakage Risk": "MEDIUM (Simultaneous Staging)",
        "Reason": "Number of staged units during the day.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "battery_charge_kw / discharge_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "HIGH (Simultaneous Dispatch)",
        "Reason": "Intra-day power flow into/out of battery storage.",
        "Decision": "REMOVE"
    },
    {
        "Feature": "solar_generation_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "MEDIUM (Simultaneous Outcome)",
        "Reason": "Actual solar output generated during the day. Replaced by NWP solar radiation.",
        "Decision": "REPLACE (with NWP solar radiation forecast)"
    },
    {
        "Feature": "chp_waste_heat_kw",
        "Known at 06:00": "NO",
        "Leakage Risk": "MEDIUM (Simultaneous Thermal Output)",
        "Reason": "Heat recovered from today's generator burn. Replaced by Lag-1 CHP heat.",
        "Decision": "REPLACE (with Lag-1 CHP heat observed yesterday)"
    },

    # ── VALID PRE-FORECAST FEATURES (LEGITIMATE PREDICTORS) ────────────────────
    {
        "Feature": "station_id",
        "Known at 06:00": "YES",
        "Leakage Risk": "NONE",
        "Reason": "Station identity (Maitri / Bharati) and physical structural topology.",
        "Decision": "KEEP"
    },
    {
        "Feature": "Calendar & Astronomical Geometry",
        "Known at 06:00": "YES",
        "Leakage Risk": "NONE",
        "Reason": "Exact astronomical solar elevation, daylight duration, and seasonal cycles.",
        "Decision": "KEEP / ENGINEER NEW (month_sin, doy_sin, etc.)"
    },
    {
        "Feature": "Day-Ahead Weather Forecast (NWP)",
        "Known at 06:00": "YES",
        "Leakage Risk": "NONE (NWP Standard)",
        "Reason": "Forecasted ambient temperature, wind speed, solar radiation, snowfall for t+1.",
        "Decision": "ENGINEER NEW (fc_temperature_c, fc_wind_chill, etc.)"
    },
    {
        "Feature": "Historical Load Lags (t-1, t-2, t-3, t-7, t-14)",
        "Known at 06:00": "YES",
        "Leakage Risk": "NONE (Strictly Past Data)",
        "Reason": "Station electrical demand observed in past 24h cycles.",
        "Decision": "KEEP / ENGINEER NEW"
    },
    {
        "Feature": "Trailing Rolling Load Stats [t-k, t-1]",
        "Known at 06:00": "YES",
        "Leakage Risk": "NONE (Window strictly excludes t=0 and t+1)",
        "Reason": "Baseline load level and load volatility over 3, 7, 14, 30 days.",
        "Decision": "ENGINEER NEW (strict shift(1) rolling)"
    },
    {
        "Feature": "Scheduled Station Population Roster",
        "Known at 06:00": "YES",
        "Leakage Risk": "NONE",
        "Reason": "Planned expedition staff count and capacity utilization for the day.",
        "Decision": "KEEP / ENGINEER NEW"
    },
    {
        "Feature": "Battery SoC at Forecast Cutoff (06:00)",
        "Known at 06:00": "YES",
        "Leakage Risk": "NONE",
        "Reason": "Storage state available at the moment of dispatch planning.",
        "Decision": "KEEP (battery_soc_start_pct)"
    },
    {
        "Feature": "Observed Thermal & Weather Persistence",
        "Known at 06:00": "YES",
        "Leakage Risk": "NONE",
        "Reason": "Lagged observed temperatures (t-1, t-2, t-3) providing thermal inertia proxy.",
        "Decision": "ENGINEER NEW (obs_temp_lag1, obs_temp_trend3)"
    },
]

def generate_audit_table():
    df = pd.DataFrame(AUDIT_DATA)
    return df

if __name__ == "__main__":
    df = generate_audit_table()
    print(df.to_string(index=False))
