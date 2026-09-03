"""
leakage_audit.py
----------------
Step 2: Rigorous Information Boundary and Feature Leakage Audit
Model 5 (Version 3): Day-Ahead Battery State of Charge Forecasting

Classifications:
  - Historical: Observed telemetry strictly up to 18:00 on Day t
  - Forecast Available: Exogenous NWP forecast or known astronomical/calendar state for Day t+1
  - Leakage: Realized physical/operational state occurring during Day t+1
  - Simulator Arithmetic: Direct simulator equation component or energy balance
  - Target Derived: Variable algebraically containing the predictand
  - Unknown: Unclassified or ambiguous source
"""

import os
import sys
import pandas as pd
from typing import List, Dict

# Local imports
from config import BASE_DIR, DATA_DIR, RESULTS_DIR

AUDIT_DEFINITIONS: List[Dict[str, str]] = [
    # --- Target & Derived Variables ---
    {
        "Feature": "battery_soc_percent(t+1)",
        "Classification": "Target Derived",
        "Reason": "The predictand itself at the end of Day t+1. Must be isolated as the forecast target.",
        "Decision": "TARGET ONLY (REJECT AS FEATURE)",
    },
    {
        "Feature": "soc_delta using future SoC",
        "Classification": "Target Derived",
        "Reason": "Difference between future SoC and today's SoC (SoC(t+1) - SoC(t)). Leaks the target directly.",
        "Decision": "REJECT",
    },
    {
        "Feature": "battery_soc_percent (same day t)",
        "Classification": "Historical",
        "Reason": "Battery SoC observed at 18:00 cutoff on Day t. Represents starting state for lead-1 forecast.",
        "Decision": "KEEP (as soc_lag1)",
    },
    
    # --- Battery Power & Energy Telemetry on Day t+1 ---
    {
        "Feature": "battery_charge_kw (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Total charging power executed into the battery bank during Day t+1. Unknown at 18:00 cutoff.",
        "Decision": "REJECT",
    },
    {
        "Feature": "battery_discharge_kw (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Total discharge power drawn from the battery during Day t+1. Realized concurrently with SoC drawdown.",
        "Decision": "REJECT",
    },
    {
        "Feature": "battery_to_load_kwh (Day t+1)",
        "Classification": "Simulator Arithmetic",
        "Reason": "Integrated energy dispatched from battery to station microgrid on Day t+1. Direct simulator state equation driver.",
        "Decision": "REJECT",
    },
    {
        "Feature": "future battery efficiency (t+1)",
        "Classification": "Simulator Arithmetic",
        "Reason": "Coulombic / round-trip efficiency realized under thermal dynamics during Day t+1.",
        "Decision": "REJECT",
    },
    
    # --- Solar & Renewable Telemetry on Day t+1 ---
    {
        "Feature": "solar_generation_kw (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Actual realized electrical output from solar array on Day t+1. Must use NWP irradiance forecast instead.",
        "Decision": "REJECT",
    },
    {
        "Feature": "solar_to_load_kwh (Day t+1)",
        "Classification": "Simulator Arithmetic",
        "Reason": "Solar energy directly supplied to load on Day t+1, bypassing battery.",
        "Decision": "REJECT",
    },
    {
        "Feature": "solar_energy_kwh (Day t+1)",
        "Classification": "Simulator Arithmetic",
        "Reason": "Integrated renewable generation on Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "renewable_share_percent (Day t+1)",
        "Classification": "Simulator Arithmetic",
        "Reason": "Calculated after day ends as solar_energy / daily_load_energy.",
        "Decision": "REJECT",
    },
    
    # --- Generator Dispatch & Thermal on Day t+1 ---
    {
        "Feature": "generator_output_kw (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Realized generator electrical output dispatched during Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "generator_runtime_hours (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Operational run hours accumulated on gensets during Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "active_generators (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Number of active diesel generators online during Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "generator_status (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Operational status (NORMAL, OVERLOAD, etc.) realized during Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "generator_to_battery (Day t+1)",
        "Classification": "Simulator Arithmetic",
        "Reason": "Generator surplus power diverted to charge battery during Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "chp_waste_heat_kw (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Waste heat recovery realized from diesel gensets during Day t+1.",
        "Decision": "REJECT",
    },
    
    # --- Electrical Demand & Energy Balances on Day t+1 ---
    {
        "Feature": "total_load_kw (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Total station electrical power load realized during Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "heating_load_kw (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Heating sub-load realized during Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "sub-loads (accommodation, lab, kitchen, lighting, water, comms) (t+1)",
        "Classification": "Leakage",
        "Reason": "Disaggregated end-use loads realized during Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "daily_load_energy_kwh (Day t+1)",
        "Classification": "Simulator Arithmetic",
        "Reason": "Total energy integrated across all 24 hours of Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "generator_energy_kwh (Day t+1)",
        "Classification": "Simulator Arithmetic",
        "Reason": "Total generator energy produced during Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "unserved_energy_kwh (Day t+1)",
        "Classification": "Simulator Arithmetic",
        "Reason": "Microgrid deficit resulting from battery depletion and generator cap.",
        "Decision": "REJECT",
    },
    {
        "Feature": "power_shortage_event (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Binary event indicating unserved load occurred on Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "overload_flag (Day t+1)",
        "Classification": "Leakage",
        "Reason": "Post-event flag indicating microgrid threshold violation on Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "load_shedding_kwh (Day t+1)",
        "Classification": "Simulator Arithmetic",
        "Reason": "Load curtailment executed to protect battery/generator on Day t+1.",
        "Decision": "REJECT",
    },
    {
        "Feature": "per_capita_load (Day t+1)",
        "Classification": "Simulator Arithmetic",
        "Reason": "total_load_kw / scheduled_population on Day t+1.",
        "Decision": "REJECT",
    },
    
    # --- Forecast Available Features (Allowed) ---
    {
        "Feature": "fc_temperature_c",
        "Classification": "Forecast Available",
        "Reason": "Day-ahead Numerical Weather Prediction (NWP) 24h ambient temperature forecast.",
        "Decision": "KEEP",
    },
    {
        "Feature": "fc_wind_speed_kmh / gust",
        "Classification": "Forecast Available",
        "Reason": "NWP wind velocity forecast driving structural heat loss.",
        "Decision": "KEEP",
    },
    {
        "Feature": "fc_solar_radiation_wm2",
        "Classification": "Forecast Available",
        "Reason": "NWP solar irradiance forecast driving potential photovoltaic charging.",
        "Decision": "KEEP",
    },
    {
        "Feature": "fc_solar_daylight_hours / elevation",
        "Classification": "Forecast Available",
        "Reason": "Exact astronomical solar ephemeris for Day t+1.",
        "Decision": "KEEP",
    },
    {
        "Feature": "is_polar_night / is_polar_day",
        "Classification": "Forecast Available",
        "Reason": "Astronomical geometry indicating presence or complete absence of daylight.",
        "Decision": "KEEP",
    },
    {
        "Feature": "fc_heating_degree_days",
        "Classification": "Forecast Available",
        "Reason": "max(0, 18 - fc_temperature_c), thermodynamic proxy for heating load.",
        "Decision": "KEEP",
    },
    {
        "Feature": "scheduled_population & roster",
        "Classification": "Forecast Available",
        "Reason": "Pre-scheduled station roster and crew assignment for Day t+1.",
        "Decision": "KEEP",
    },
    {
        "Feature": "station_enc",
        "Classification": "Forecast Available",
        "Reason": "Physical station identity (Bharati vs Maitri microgrid topology).",
        "Decision": "KEEP",
    },
    
    # --- Historical Telemetry (Allowed up to 18:00 Day t) ---
    {
        "Feature": "soc_lag1, lag2, lag3, lag7, lag14",
        "Classification": "Historical",
        "Reason": "Observed battery State of Charge at 18:00 on Day t, Day t-1, etc.",
        "Decision": "KEEP",
    },
    {
        "Feature": "soc_roll3, 7, 14, 30_mean (shifted)",
        "Classification": "Historical",
        "Reason": "Trailing rolling average SoC strictly shifted before rolling.",
        "Decision": "KEEP",
    },
    {
        "Feature": "soc_trend_3d / 7d (shifted)",
        "Classification": "Historical",
        "Reason": "Observed multi-day SoC drawdown / charging trajectories.",
        "Decision": "KEEP",
    },
    {
        "Feature": "soc_roll7_std, roll14_std (shifted)",
        "Classification": "Historical",
        "Reason": "Observed battery cycling volatility over trailing window.",
        "Decision": "KEEP",
    },
    {
        "Feature": "battery_discharge_lag1, roll7, roll14",
        "Classification": "Historical",
        "Reason": "Observed discharge power history up to Day t.",
        "Decision": "KEEP",
    },
    {
        "Feature": "load_lag1, lag2, lag3, lag7, roll7, roll14",
        "Classification": "Historical",
        "Reason": "Observed total station electrical load history up to Day t.",
        "Decision": "KEEP",
    },
    {
        "Feature": "generator_output_lag1, runtime_lag1, roll7",
        "Classification": "Historical",
        "Reason": "Observed generator dispatch history up to Day t.",
        "Decision": "KEEP",
    },
    {
        "Feature": "chp_heat_lag1, roll7",
        "Classification": "Historical",
        "Reason": "Observed CHP waste heat recovery history up to Day t.",
        "Decision": "KEEP",
    },
    {
        "Feature": "solar_gen_lag1, roll7",
        "Classification": "Historical",
        "Reason": "Observed solar array output history up to Day t.",
        "Decision": "KEEP",
    },
    {
        "Feature": "fuel_stock_lag1",
        "Classification": "Historical",
        "Reason": "Observed fuel tank inventory at 18:00 cutoff (governs genset availability).",
        "Decision": "KEEP",
    },
    {
        "Feature": "obs_temp_lag1, lag2, lag3, roll7, trend3",
        "Classification": "Historical",
        "Reason": "Observed station thermal history up to Day t.",
        "Decision": "KEEP",
    },
    {
        "Feature": "water / inventory / comms columns",
        "Classification": "Unknown / Unrelated",
        "Reason": "Logistics and inventory levels that do not directly govern battery charge/discharge.",
        "Decision": "REJECT",
    },
]


def run_leakage_audit() -> pd.DataFrame:
    """Generate and display the complete leakage audit table."""
    audit_df = pd.DataFrame(AUDIT_DEFINITIONS)
    print("=" * 80)
    print("MODEL 5 (V3) INFORMATION BOUNDARY & LEAKAGE AUDIT TABLE")
    print("=" * 80)
    print(audit_df.to_string(index=False))
    print("=" * 80)
    
    kept = audit_df[audit_df["Decision"].str.contains("KEEP")]
    rejected = audit_df[~audit_df["Decision"].str.contains("KEEP")]
    print(f"Total Audited Candidates: {len(audit_df)}")
    print(f"Features Kept (Forecast Safe): {len(kept)}")
    print(f"Features Rejected (Leakage / Prohibited): {len(rejected)}")
    print("=" * 80)
    return audit_df


if __name__ == "__main__":
    run_leakage_audit()
