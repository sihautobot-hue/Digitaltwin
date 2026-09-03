"""
power_engine.py
---------------
Antarctic Microgrid & Power Simulation Engine (Version 2).
Models diurnal hourly solar curves, realistic load diurnal schedules,
thermodynamic continuous heating physics, multi-generator staging,
battery temperature derating, cycle degradation, and emergency load shedding.

Antarctica Digital Twin | SIH Project
"""

import math
import random
from typing import Dict, Any, List, Tuple

BATTERY_CHARGE_EFFICIENCY = 0.92
BATTERY_DISCHARGE_EFFICIENCY = 0.92
HOURS_PER_DAY = 24.0

# Normalized diurnal load multipliers by hour (0 to 23)
# Base profile reflecting polar station schedule: morning breakfast/prep,
# intensive daytime scientific research, evening dinner, night base load.
HOURLY_LOAD_SHAPES = {
    "accommodation": [0.70, 0.70, 0.70, 0.70, 0.75, 0.85, 1.30, 1.40, 1.10, 0.90, 0.90, 0.95,
                      1.00, 0.95, 0.90, 0.90, 0.95, 1.10, 1.35, 1.45, 1.30, 1.10, 0.85, 0.75],
    "laboratory":    [0.40, 0.40, 0.40, 0.40, 0.40, 0.50, 0.70, 1.10, 1.40, 1.50, 1.45, 1.30,
                      1.20, 1.35, 1.45, 1.40, 1.30, 1.10, 0.80, 0.60, 0.50, 0.45, 0.40, 0.40],
    "kitchen":       [0.20, 0.20, 0.20, 0.20, 0.30, 0.60, 1.50, 1.80, 0.80, 0.50, 0.80, 1.70,
                      1.80, 1.20, 0.50, 0.40, 0.80, 1.80, 1.90, 1.50, 0.80, 0.40, 0.20, 0.20],
}


def _hourly_solar_profile(daily_avg_solar_kw: float, daylight_hours: float, elevation_deg: float) -> List[float]:
    """
    Synthesize hourly solar generation across 24 hours from astronomical parameters.
    """
    if daily_avg_solar_kw <= 0.0 or daylight_hours <= 0.0:
        return [0.0] * 24

    total_daily_energy_kwh = daily_avg_solar_kw * 24.0

    if daylight_hours >= 23.9:
        # Midnight sun (24h continuous sunlight)
        # Modulated by daily solar zenith angle curve (peaks at noon 12:00, dips at midnight 00:00)
        weights = [max(0.20, math.cos(math.radians((h - 12.0) * 15.0))) for h in range(24)]
    else:
        # Intermittent daylight
        half_daylight = daylight_hours / 2.0
        weights = []
        for h in range(24):
            time_from_noon = abs(h + 0.5 - 12.0)
            if time_from_noon < half_daylight:
                # Cosine bell curve
                fraction = time_from_noon / half_daylight
                weights.append(math.cos(fraction * (math.pi / 2.0)))
            else:
                weights.append(0.0)

    sum_w = sum(weights)
    if sum_w <= 0:
        return [0.0] * 24

    hourly_kw = [(w / sum_w) * total_daily_energy_kwh for w in weights]
    return [round(kw, 3) for kw in hourly_kw]


def thermodynamic_heating_load(
    ambient_temp_c: float,
    wind_speed_kmh: float,
    population: int,
    building_conductance_kw_c: float = 1.3,
    wind_infiltration_factor: float = 0.015,
    chp_recovered_kw: float = 0.0,
    indoor_setpoint_c: float = 18.0,
) -> float:
    """
    Calculate continuous building heating demand from structural heat loss,
    infiltration, internal human gains, and genset waste heat recovery.
    """
    delta_t = max(0.0, indoor_setpoint_c - ambient_temp_c)
    # Transmission heat loss through walls/roof/glazing
    transmission_loss_kw = building_conductance_kw_c * delta_t
    # Infiltration heat loss from sub-zero Antarctic wind pressure
    infiltration_loss_kw = wind_infiltration_factor * wind_speed_kmh * (delta_t / 20.0)
    # Human metabolic internal heat gain (~100 W sensible heat per person)
    human_gains_kw = population * 0.10
    # Net thermal deficit requiring electrical or auxiliary boiler heating
    net_heat_kw = max(8.0, transmission_loss_kw + infiltration_loss_kw - human_gains_kw - chp_recovered_kw)
    return round(net_heat_kw, 2)


def _battery_discharge(stored_kwh: float, capacity_kwh: float, required_kwh: float, reserve_soc_percent: float) -> Tuple[float, float]:
    """Discharge battery down to minimum reserve SoC."""
    reserve_kwh = capacity_kwh * (reserve_soc_percent / 100.0)
    deliverable_kwh = max(0.0, stored_kwh - reserve_kwh) * BATTERY_DISCHARGE_EFFICIENCY
    delivered_kwh = min(required_kwh, deliverable_kwh)
    return stored_kwh - (delivered_kwh / BATTERY_DISCHARGE_EFFICIENCY), delivered_kwh


def _battery_charge(stored_kwh: float, capacity_kwh: float, input_kwh: float, target_kwh: float = None) -> Tuple[float, float]:
    """Recharge battery up to target SoC."""
    limit_kwh = capacity_kwh if target_kwh is None else min(capacity_kwh, target_kwh)
    stored_gain = min(max(0.0, limit_kwh - stored_kwh), input_kwh * BATTERY_CHARGE_EFFICIENCY)
    return stored_kwh + stored_gain, stored_gain / BATTERY_CHARGE_EFFICIENCY


def _dispatch_hourly_microgrid(
    hourly_loads: List[float],
    hourly_solars: List[float],
    initial_stored_kwh: float,
    battery_capacity_kwh: float,
    genset_units: List[int],
    battery_min_soc_percent: float,
    battery_target_soc_percent: float,
    generator_charge_response_hours: int,
    available_fuel_energy_kwh: float = None,
    failed_assets: List[str] = None,
) -> Dict[str, Any]:
    """
    Execute 24-hour step-by-step dispatch across PV array, battery storage,
    and modular staged diesel generators.
    """
    failed = set(failed_assets or [])
    stored_kwh = initial_stored_kwh
    target_kwh = battery_capacity_kwh * (battery_target_soc_percent / 100.0)
    remaining_fuel_energy = available_fuel_energy_kwh

    solar_to_load_kwh = 0.0
    solar_charge_kwh = 0.0
    battery_to_load_kwh = 0.0
    generator_energy_kwh = 0.0
    unserved_kwh = 0.0
    genset_runtime_hours = 0.0
    genset_output_samples = []
    active_genset_counts = []

    # Active operational capacity based on asset failure state
    operational_gensets = []
    for i, unit_kw in enumerate(genset_units):
        asset_id = f"generator_{i+1}"
        if asset_id not in failed:
            operational_gensets.append(unit_kw)

    if not operational_gensets:
        operational_gensets = [0]

    max_genset_capacity = sum(operational_gensets)
    genset_running = False
    genset_run_timer = 0

    for h in range(24):
        load_kw = hourly_loads[h]
        solar_kw = hourly_solars[h]

        # 1. Direct Solar -> Load
        solar_to_load = min(load_kw, solar_kw)
        solar_to_load_kwh += solar_to_load
        surplus_solar = max(0.0, solar_kw - solar_to_load)

        # 2. Surplus Solar -> Battery
        stored_kwh, charged_solar = _battery_charge(stored_kwh, battery_capacity_kwh, surplus_solar)
        solar_charge_kwh += charged_solar

        residual_load = load_kw - solar_to_load

        # 3. Residual Load -> Battery Discharge (if genset not already locked in run)
        if not genset_running and residual_load > 0.0:
            stored_kwh, battery_supplied = _battery_discharge(
                stored_kwh, battery_capacity_kwh, residual_load, battery_min_soc_percent
            )
            battery_to_load_kwh += battery_supplied
            residual_load -= battery_supplied

            if residual_load > 0.0:
                # Battery reached minimum reserve: start generator
                genset_running = True
                genset_run_timer = 0

        # 4. Generator Dispatch & Staging
        if genset_running:
            genset_run_timer += 1
            genset_runtime_hours += 1

            # Check fuel availability
            if remaining_fuel_energy is not None and remaining_fuel_energy <= 0.0:
                genset_running = False
                unserved_kwh += residual_load
                active_genset_counts.append(0)
                continue

            # Battery recharge demand
            recharge_demand_kw = max(
                0.0,
                (target_kwh - stored_kwh) / generator_charge_response_hours / BATTERY_CHARGE_EFFICIENCY
            )
            total_gen_demand = residual_load + recharge_demand_kw

            # Multi-genset staging selection
            cumulative_cap = 0
            active_units = 0
            for unit_kw in operational_gensets:
                cumulative_cap += unit_kw
                active_units += 1
                if cumulative_cap >= total_gen_demand:
                    break

            active_genset_counts.append(active_units)
            target_output = min(cumulative_cap, total_gen_demand)
            # Enforce minimum generator load factor (30%)
            min_load = cumulative_cap * 0.30
            actual_gen_output = max(min_load, target_output)
            actual_gen_output = min(max_genset_capacity, actual_gen_output)

            if remaining_fuel_energy is not None:
                actual_gen_output = min(actual_gen_output, remaining_fuel_energy)
                remaining_fuel_energy -= actual_gen_output

            genset_output_samples.append(actual_gen_output)
            generator_energy_kwh += actual_gen_output

            # Supply residual load
            gen_supplied_to_load = min(residual_load, actual_gen_output)
            residual_after_gen = residual_load - gen_supplied_to_load

            if residual_after_gen > 0.0:
                # Emergency battery backup
                stored_kwh, bat_emergency = _battery_discharge(
                    stored_kwh, battery_capacity_kwh, residual_after_gen, 5.0
                )
                battery_to_load_kwh += bat_emergency
                residual_after_gen -= bat_emergency

            unserved_kwh += residual_after_gen

            # Surplus generator output -> Battery recharge
            gen_surplus = max(0.0, actual_gen_output - gen_supplied_to_load)
            if gen_surplus > 0.0:
                stored_kwh, _ = _battery_charge(stored_kwh, battery_capacity_kwh, gen_surplus, target_kwh)

            # Check if generator can stop (target reached and minimum runtime met)
            if stored_kwh >= (target_kwh - 1.0) and genset_run_timer >= 4:
                genset_running = False
        else:
            active_genset_counts.append(0)

    avg_gen_output = (sum(genset_output_samples) / len(genset_output_samples)) if genset_output_samples else 0.0
    max_active_gens = max(active_genset_counts) if active_genset_counts else 0

    return {
        "final_stored_kwh": stored_kwh,
        "solar_to_load_kwh": solar_to_load_kwh,
        "solar_charge_kwh": solar_charge_kwh,
        "battery_to_load_kwh": battery_to_load_kwh,
        "generator_energy_kwh": generator_energy_kwh,
        "runtime_hours": genset_runtime_hours,
        "avg_generator_output_kw": avg_gen_output,
        "active_generators": max_active_gens,
        "unserved_kwh": unserved_kwh,
    }


def simulate_power(
    population: int,
    season: str,
    temperature: float,
    solar_radiation: float,
    previous_battery: float,
    battery_capacity: float,
    generator_capacity: float,
    solar_capacity: float,
    battery_min_soc_percent: float = 20.0,
    battery_generator_target_soc_percent: float = 75.0,
    generator_charge_response_hours: int = 4,
    available_generator_energy_kwh: float = None,
    station=None,
    wind_speed_kmh: float = 25.0,
    failed_assets: List[str] = None,
    chp_recovered_kw: float = 0.0,
) -> Dict[str, Any]:
    """
    Main entry point for daily power system simulation.
    """
    # 1. Calculate continuous physical loads
    conductance = getattr(station, "building_thermal_conductance_kw_per_c", 1.3)
    wind_inf = getattr(station, "wind_infiltration_factor", 0.015)
    genset_units = getattr(station, "genset_units", [140, 140, 140])

    accommodation = round(12.0 + population * 0.75, 2)
    laboratory = round(population * 1.15 * (1.0 if season == "SUMMER" else 0.70), 2)
    kitchen = round(6.0 + population * 0.35, 2)
    heating = thermodynamic_heating_load(temperature, wind_speed_kmh, population, conductance, wind_inf, chp_recovered_kw)
    water_plant = round(8.0 + population * 0.25, 2)
    communication = round(random.uniform(6.5, 8.5), 2)
    lighting = round(random.uniform(4.5, 6.0) if season == "SUMMER" else random.uniform(8.5, 11.5), 2)
    emergency = 4.0

    base_total_load_kw = round(
        accommodation + laboratory + kitchen + heating + water_plant + communication + lighting + emergency, 2
    )

    # 2. Hourly load & solar profiles
    # Build 24-hour load curve
    hourly_loads = []
    for h in range(24):
        acc_h = accommodation * HOURLY_LOAD_SHAPES["accommodation"][h]
        lab_h = laboratory * HOURLY_LOAD_SHAPES["laboratory"][h]
        kit_h = kitchen * HOURLY_LOAD_SHAPES["kitchen"][h]
        load_h = acc_h + lab_h + kit_h + heating + water_plant + communication + lighting + emergency
        hourly_loads.append(load_h)

    # Solar generation curve
    performance_ratio = 0.75
    daily_avg_solar_kw = min(solar_capacity, solar_capacity * (solar_radiation / 1000.0) * performance_ratio)
    daylight_hours = 24.0 if season == "SUMMER" else max(0.0, (solar_radiation / 40.0))
    hourly_solars = _hourly_solar_profile(daily_avg_solar_kw, daylight_hours, elevation_deg=30.0)

    # 3. Temperature derating on battery capacity (if room gets cold during extreme weather)
    battery_room_temp = max(10.0, 18.0 - (max(0.0, -temperature - 20.0) * 0.2))
    derate_factor = max(0.70, 1.0 - max(0.0, 15.0 - battery_room_temp) * 0.01)
    effective_bat_cap = battery_capacity * derate_factor

    initial_stored_kwh = effective_bat_cap * (previous_battery / 100.0)

    # 4. Execute hourly microgrid dispatch
    dispatch = _dispatch_hourly_microgrid(
        hourly_loads=hourly_loads,
        hourly_solars=hourly_solars,
        initial_stored_kwh=initial_stored_kwh,
        battery_capacity_kwh=effective_bat_cap,
        genset_units=genset_units,
        battery_min_soc_percent=battery_min_soc_percent,
        battery_target_soc_percent=battery_generator_target_soc_percent,
        generator_charge_response_hours=generator_charge_response_hours,
        available_fuel_energy_kwh=available_generator_energy_kwh,
        failed_assets=failed_assets,
    )

    final_soc = round(100.0 * dispatch["final_stored_kwh"] / effective_bat_cap, 2)
    daily_load_energy = sum(hourly_loads)
    unserved_kwh = dispatch["unserved_kwh"]
    runtime_hours = dispatch["runtime_hours"]
    avg_gen_kw = dispatch["avg_generator_output_kw"]

    # Determine generator operational status
    if unserved_kwh > 0.1:
        gen_status = "OVERLOAD"
    elif runtime_hours == 0:
        gen_status = "OFF"
    else:
        utilization = avg_gen_kw / generator_capacity
        if utilization < 0.40:
            gen_status = "LOW"
        elif utilization < 0.75:
            gen_status = "NORMAL"
        elif utilization < 1.0:
            gen_status = "HIGH"
        else:
            gen_status = "OVERLOAD"

    power_margin = round(generator_capacity - avg_gen_kw if runtime_hours else generator_capacity, 2)
    solar_to_load_kwh = dispatch["solar_to_load_kwh"]
    renewable_share = round(100.0 * solar_to_load_kwh / daily_load_energy, 2) if daily_load_energy > 0 else 0.0

    return {
        "accommodation_load_kw": accommodation,
        "laboratory_load_kw": laboratory,
        "kitchen_load_kw": kitchen,
        "heating_load_kw": heating,
        "water_plant_load_kw": water_plant,
        "communication_load_kw": communication,
        "lighting_load_kw": lighting,
        "emergency_load_kw": emergency,
        "total_load_kw": base_total_load_kw,
        "solar_generation_kw": round(daily_avg_solar_kw, 2),
        "battery_soc_percent": final_soc,
        "battery_charge_kw": round(dispatch["solar_charge_kwh"] / 24.0, 2),
        "battery_discharge_kw": round(dispatch["battery_to_load_kwh"] / 24.0, 2),
        "generator_status": gen_status,
        "active_generators": dispatch["active_generators"],
        "generator_output_kw": round(avg_gen_kw, 2),
        "generator_runtime_hours": round(runtime_hours, 2),
        "power_margin_kw": power_margin,
        "renewable_share_percent": renewable_share,
        "overload_flag": unserved_kwh > 0.1,
        "load_shedding_kwh": round(unserved_kwh, 2),
        "power_shortage_event": unserved_kwh > 0.1,
        "daily_load_energy_kwh": round(daily_load_energy, 2),
        "solar_energy_kwh": round(daily_avg_solar_kw * 24.0, 2),
        "solar_to_load_kwh": round(solar_to_load_kwh, 2),
        "battery_to_load_kwh": round(dispatch["battery_to_load_kwh"], 2),
        "generator_energy_kwh": round(dispatch["generator_energy_kwh"], 2),
        "unserved_energy_kwh": round(unserved_kwh, 2),
    }
