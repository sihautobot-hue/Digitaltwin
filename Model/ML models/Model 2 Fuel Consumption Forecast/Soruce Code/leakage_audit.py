"""
leakage_audit.py
----------------
Exhaustive scientific leakage audit for Model 2 (Fuel Consumption Forecast V3).
Audits all candidate variables against the 18:00 cutoff contract on Day t
predicting fuel_consumed_today_liters for Day t+1.

Classifications:
  - Safe: Available before Day t+1 begins (deterministic or NWP forecast)
  - Historical: Observed telemetry strictly up to Day t (t <= 0)
  - Questionable: Ambiguous timing or proxy risk (removed or strictly lagged)
  - Leakage: Simultaneous same-day operational outcome
  - Future information: Occurs or recorded after forecast issue time
  - Simulator arithmetic: Computed directly from or with target inside simulator
  - Derived target: Encodes target via algebraic transformation
"""

import os
import pandas as pd

AUDIT_RULES = [
    # ── DERIVED TARGET & ALGEBRAIC SIMULATOR ARITHMETIC ───────────────────────
    ("fuel_consumed_today_liters", "Derived target", "Raw predictand itself. Must be shifted to Day t+1 to serve as the forecast target.", "REMOVE FROM FEATURES"),
    ("fuel_days_remaining", "Derived target", "Algebraic identity: fuel_stock / fuel_consumed_today. Direct numerical encoding of target.", "REJECT"),
    ("fuel_efficiency_l_per_kwh", "Derived target", "Post-hoc ratio: fuel_consumed_today / generator_energy_kwh. Direct target encoding.", "REJECT"),
    ("gen_energy_proxy", "Simulator arithmetic", "Computed as generator_output_kw * generator_runtime_hours. In the simulator, fuel burn is directly calculated from this energy proxy via SFC curve.", "REJECT"),
    ("per_capita_load", "Simulator arithmetic", "Ratio of Day t+1 electrical load to population. Directly related to generator dispatch.", "REJECT"),
    ("renewable_share_percent", "Simulator arithmetic", "Ratio of solar generation to total load on Day t+1. Encodes residual generator load.", "REJECT"),
    ("generator_energy_kwh", "Simulator arithmetic", "Integrated generation dispatched to meet load during Day t+1. Primary driver of fuel burn equation.", "REJECT"),
    ("daily_load_energy_kwh", "Simulator arithmetic", "Total load energy on Day t+1. Determines generator dispatch and fuel consumption.", "REJECT"),

    # ── SAME-DAY DISPATCH & OPERATIONAL OUTCOMES (LEAKAGE / FUTURE INFO) ──────
    ("generator_output_kw", "Leakage", "Mean electrical output of generators dispatched during Day t+1. Known only after dispatch occurs.", "REJECT"),
    ("generator_runtime_hours", "Leakage", "Hours generator ran during Day t+1. Unknown until Day t+1 finishes.", "REJECT"),
    ("active_generators", "Leakage", "Number of generator units staged during Day t+1. Consequence of same-day load dispatch.", "REJECT"),
    ("gen_utilization_pct", "Leakage", "Generator load factor during Day t+1. Drives non-linear SFC curve in simulator.", "REJECT"),
    ("generator_status", "Leakage", "Post-event operational status assigned based on Day t+1 dispatch.", "REJECT"),
    ("gen_status_enc", "Leakage", "Ordinal encoding of same-day generator status during Day t+1.", "REJECT"),
    ("total_load_kw", "Leakage", "Total electrical demand realized on Day t+1. Fuel is burned to meet this demand.", "REJECT"),
    ("heating_load_kw", "Leakage", "Electrical heating demand on Day t+1. Sub-component of total load.", "REJECT"),
    ("solar_generation_kw", "Leakage", "Realized solar power generation on Day t+1. Offsets generator dispatch intra-day.", "REJECT"),
    ("solar_roll7_mean", "Questionable", "Rolling mean solar power including Day t+1 outcome if not shifted. Replaced by NWP solar irradiance.", "REPLACE"),
    ("load_roll7_mean", "Questionable", "Rolling mean load if not explicitly shifted before Day t+1. Replaced by pre-forecast load lags.", "REPLACE"),
    ("chp_waste_heat_kw", "Leakage", "Thermal heat recovered from Day t+1 generator fuel burn. Downstream physical consequence.", "REJECT (Use Lag-1)"),
    ("battery_soc_percent", "Leakage", "State of Charge at the end of Day t+1. Post-event storage balance.", "REJECT (Use 18:00 Cutoff SoC)"),
    ("battery_charge_kw", "Leakage", "Intra-day power flow into battery during Day t+1.", "REJECT"),
    ("battery_discharge_kw", "Leakage", "Intra-day power flow out of battery during Day t+1.", "REJECT"),
    ("solar_to_load_kwh", "Leakage", "Intra-day energy balance flow during Day t+1.", "REJECT"),
    ("battery_to_load_kwh", "Leakage", "Intra-day energy balance flow during Day t+1.", "REJECT"),
    ("unserved_energy_kwh", "Leakage", "Power deficit on Day t+1.", "REJECT"),
    ("load_shedding_kwh", "Leakage", "Emergency load curtailment on Day t+1.", "REJECT"),
    ("power_shortage_event", "Leakage", "Shortage event on Day t+1.", "REJECT"),
    ("overload_flag", "Leakage", "Generator overload flag on Day t+1.", "REJECT"),
    ("power_margin_kw", "Leakage", "Power margin on Day t+1.", "REJECT"),

    # ── POST-EVENT LOGISTICS & RISK OUTCOMES (FUTURE INFORMATION) ─────────────
    ("refuel_event", "Future information", "Whether a refueling tanker transferred fuel during Day t+1. Realized during the day.", "REJECT (Use lag/days_since)"),
    ("refuel_quantity_liters", "Future information", "Fuel volume transferred during Day t+1.", "REJECT"),
    ("fuel_received_today_liters", "Future information", "Fuel liters received during Day t+1.", "REJECT"),
    ("fuel_shortage_event", "Future information", "Fuel outage incident during Day t+1.", "REJECT"),
    ("fuel_shipment_created_today", "Future information", "Tanker order created during Day t+1.", "REJECT"),
    ("fuel_shipment_delayed_today", "Future information", "Shipping delay recorded during Day t+1.", "REJECT"),
    ("fuel_status", "Future information", "Fuel status level assessed at end of Day t+1.", "REJECT"),
    ("fuel_risk", "Future information", "Risk score computed at end of Day t+1.", "REJECT (Use Lag-1)"),
    ("power_risk", "Future information", "Risk score computed at end of Day t+1.", "REJECT (Use Lag-1)"),
    ("overall_risk_score", "Future information", "Composite risk computed at end of Day t+1.", "REJECT (Use Lag-1)"),

    # ── SAFE PRE-FORECAST PREDICTORS (KNOWN BEFORE DAY t+1 BEGINS) ─────────────
    ("station_enc", "Safe", "Station physical topology and generator layout (Maitri vs Bharati). Static constant.", "KEEP"),
    ("month_sin / month_cos", "Safe", "Calendar month cyclic encoding for Day t+1. Known astronomically in advance.", "KEEP"),
    ("doy_sin / doy_cos", "Safe", "Day of year cyclic encoding for Day t+1. Known astronomically in advance.", "KEEP"),
    ("dow_sin / dow_cos", "Safe", "Day of week cyclic encoding for Day t+1. Known in advance.", "KEEP"),
    ("is_shipping_season", "Safe", "Scheduled Antarctic maritime access window (Nov–Mar). Calendar based.", "KEEP"),
    ("is_polar_night", "Safe", "Astronomical flag: sun stays below horizon for 24h on Day t+1. Deterministic ephemeris.", "KEEP"),
    ("is_polar_day", "Safe", "Astronomical flag: continuous 24h sunlight on Day t+1. Deterministic ephemeris.", "KEEP"),
    ("fc_solar_elevation_deg", "Safe", "Noon solar elevation angle for Day t+1. Deterministic orbital mechanics.", "KEEP"),
    ("fc_solar_daylight_hours", "Safe", "Theoretical daylight duration for Day t+1. Deterministic orbital mechanics.", "KEEP"),
    ("fc_temperature_c", "Safe", "Day-ahead Numerical Weather Prediction (NWP) ambient temperature forecast for Day t+1.", "KEEP"),
    ("fc_wind_speed_kmh", "Safe", "Day-ahead NWP wind speed forecast for Day t+1.", "KEEP"),
    ("fc_wind_gust_kmh", "Safe", "Day-ahead NWP wind gust forecast for Day t+1.", "KEEP"),
    ("fc_solar_radiation_wm2", "Safe", "Day-ahead NWP solar irradiance forecast for Day t+1.", "KEEP"),
    ("fc_snowfall_cm", "Safe", "Day-ahead NWP snowfall precipitation forecast for Day t+1.", "KEEP"),
    ("fc_snow_depth_cm", "Safe", "Day-ahead NWP snow pack depth forecast for Day t+1.", "KEEP"),
    ("fc_weather_severity", "Safe", "Day-ahead NWP weather severity index forecast for Day t+1.", "KEEP"),
    ("fc_weather_type_enc", "Safe", "Day-ahead NWP weather regime classification forecast for Day t+1.", "KEEP"),
    ("fc_wind_chill_c", "Safe", "Thermodynamic wind chill index derived from NWP forecast wind and temperature.", "KEEP"),
    ("fc_katabatic_index", "Safe", "Katabatic wind proxy derived from NWP forecast wind and sub-zero temperature.", "KEEP"),
    ("fc_heating_degree_days", "Safe", "Heating demand driver derived from forecast temperature: max(0, 18 - T_fc).", "KEEP"),
    ("scheduled_population", "Safe", "Pre-planned station crew roster count for Day t+1. Known in advance.", "KEEP"),
    ("scheduled_occupancy_pct", "Safe", "Scheduled station capacity utilization percentage for Day t+1.", "KEEP"),
    ("scheduled_scientists", "Safe", "Scheduled scientific personnel roster count for Day t+1.", "KEEP"),
    ("scheduled_engineers", "Safe", "Scheduled operations and engineering staff for Day t+1.", "KEEP"),
    ("scheduled_technicians", "Safe", "Scheduled maintenance/workshop technicians for Day t+1.", "KEEP"),
    ("scheduled_medical", "Safe", "Scheduled medical bay staff for Day t+1.", "KEEP"),
    ("fuel_shipments_pending", "Safe", "Number of inbound fuel supply tankers currently scheduled/in transit.", "KEEP"),
    ("fuel_eta_days", "Safe", "Estimated days until next scheduled fuel delivery based on voyage plan.", "KEEP"),

    # ── HISTORICAL TELEMETRY (OBSERVED STRICTLY UP TO 18:00 ON DAY t) ──────────
    ("fuel_stock_start_liters", "Historical", "Fuel tank level observed at 18:00 cutoff on Day t. Current reserve baseline.", "KEEP"),
    ("fuel_stock_lag1", "Historical", "Fuel tank level observed on Day t-1.", "KEEP"),
    ("fuel_stock_drawdown_3d", "Historical", "Observed 3-day net fuel inventory drawdown rate (Liters).", "KEEP"),
    ("days_since_refuel_start", "Historical", "Elapsed days since last verified refueling event.", "KEEP"),
    ("fuel_lag1", "Historical", "Actual fuel consumed on Day t (observed by 18:00 cutoff).", "KEEP"),
    ("fuel_lag2", "Historical", "Actual fuel consumed on Day t-1 (48h prior).", "KEEP"),
    ("fuel_lag3", "Historical", "Actual fuel consumed on Day t-2 (72h prior).", "KEEP"),
    ("fuel_lag7", "Historical", "Actual fuel consumed on same day last week (168h prior).", "KEEP"),
    ("fuel_lag14", "Historical", "Actual fuel consumed 2 weeks ago (336h prior).", "KEEP"),
    ("fuel_roll3_mean", "Historical", "3-day trailing mean fuel burn [t-2, t]. Shifted before rolling.", "KEEP"),
    ("fuel_roll7_mean", "Historical", "7-day trailing mean fuel burn [t-6, t]. Shifted before rolling.", "KEEP"),
    ("fuel_roll14_mean", "Historical", "14-day trailing mean fuel burn [t-13, t]. Shifted before rolling.", "KEEP"),
    ("fuel_roll30_mean", "Historical", "30-day trailing mean fuel burn [t-29, t]. Shifted before rolling.", "KEEP"),
    ("fuel_expanding_mean", "Historical", "Cumulative expanding mean fuel burn up to Day t.", "KEEP"),
    ("fuel_roll7_std", "Historical", "7-day trailing fuel consumption volatility. Shifted before rolling.", "KEEP"),
    ("fuel_roll14_std", "Historical", "14-day trailing fuel consumption volatility. Shifted before rolling.", "KEEP"),
    ("fuel_trend_3d", "Historical", "3-day fuel burn gradient (fuel_lag1 - fuel_lag3).", "KEEP"),
    ("fuel_trend_7d", "Historical", "Weekly fuel burn gradient (fuel_lag1 - fuel_lag7).", "KEEP"),
    ("obs_temp_lag1", "Historical", "Observed ambient temperature on Day t.", "KEEP"),
    ("obs_temp_lag2", "Historical", "Observed ambient temperature on Day t-1.", "KEEP"),
    ("obs_temp_lag3", "Historical", "Observed ambient temperature on Day t-2.", "KEEP"),
    ("obs_temp_roll7_mean", "Historical", "7-day trailing mean observed temperature (thermal inertia proxy).", "KEEP"),
    ("obs_temp_trend3", "Historical", "3-day observed temperature gradient.", "KEEP"),
    ("obs_wind_lag1", "Historical", "Observed wind speed on Day t.", "KEEP"),
    ("obs_wind_roll7_mean", "Historical", "7-day trailing mean wind speed.", "KEEP"),
    ("obs_weather_sev_lag1", "Historical", "Observed weather severity on Day t.", "KEEP"),
    ("obs_weather_sev_roll7", "Historical", "7-day trailing mean weather severity.", "KEEP"),
    ("pop_lag1", "Historical", "Actual station population present on Day t.", "KEEP"),
    ("pop_trend7", "Historical", "7-day net crew size change.", "KEEP"),
    ("battery_soc_start_pct", "Historical", "Battery State of Charge observed at 18:00 cutoff on Day t.", "KEEP"),
    ("soc_lag1", "Historical", "Battery State of Charge on Day t-1.", "KEEP"),
    ("soc_delta_lag1", "Historical", "24-hour battery SoC rate of change.", "KEEP"),
    ("gen_output_lag1", "Historical", "Generator output observed on Day t (kW).", "KEEP"),
    ("gen_runtime_lag1", "Historical", "Generator operating hours observed on Day t.", "KEEP"),
    ("gen_utilization_lag1", "Historical", "Generator load factor observed on Day t.", "KEEP"),
    ("chp_heat_lag1", "Historical", "Generator waste heat recovered on Day t (kW).", "KEEP"),
    ("chp_heat_roll7_mean", "Historical", "7-day trailing mean CHP waste heat contribution.", "KEEP"),
    ("fuel_risk_lag1", "Historical", "Fuel sub-system risk score observed on Day t.", "KEEP"),
    ("power_risk_lag1", "Historical", "Power sub-system risk score observed on Day t.", "KEEP"),
    ("overall_risk_lag1", "Historical", "Composite station risk score observed on Day t.", "KEEP"),
    ("risk_roll7_mean", "Historical", "7-day trailing average composite station risk.", "KEEP"),
]

def generate_audit_report():
    df = pd.DataFrame(AUDIT_RULES, columns=["Feature", "Classification", "Reason", "Decision"])
    return df

if __name__ == "__main__":
    df_audit = generate_audit_report()
    out_path = os.path.join(os.path.dirname(__file__), "results_v3", "model2_feature_leakage_audit.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df_audit.to_csv(out_path, index=False)
    print("=" * 80)
    print("SCIENTIFIC LEAKAGE AUDIT SUMMARY FOR MODEL 2")
    print("=" * 80)
    print(df_audit["Classification"].value_counts())
    print(f"\nAudit table saved to: {out_path}")
