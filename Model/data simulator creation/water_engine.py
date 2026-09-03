"""
water_engine.py
---------------
Life support water systems, summer lake pumping, winter CHP snow-melting,
membrane filtration wear, dynamic water quality index, and freeze-up risk.

Antarctica Digital Twin | SIH Project
"""

import math
import random
from typing import Dict, Any

# Daily per-capita consumption allowances (Liters/day/person)
# Drinking: 3L, Cooking: 6L, Personal Hygiene/Shower: 24L, Laundry: 10L, Sanitation/Misc: 8L
DRINKING, COOKING, HYGIENE, LAUNDRY, MISC = 3.0, 6.0, 24.0, 10.0, 8.0


def person_water_use(population: int) -> float:
    """Domestic water consumption per person."""
    return population * (DRINKING + COOKING + HYGIENE + LAUNDRY + MISC)


def laboratory_water(population: int, season: str = "SUMMER") -> float:
    """Scientific laboratory water demand (higher in summer intensive research)."""
    rate = 7.5 if season == "SUMMER" else 3.5
    return population * rate


def total_water_demand(population: int, season: str = "SUMMER") -> float:
    """Total daily station fresh water demand in Liters."""
    return round(person_water_use(population) + laboratory_water(population, season), 2)


def snow_melting_output(
    weather: Dict[str, Any],
    plant_capacity_liters: float = 5000.0,
    power_shortage: bool = False,
    chp_waste_heat_kw: float = 0.0,
    plant_status: str = "OPERATIONAL",
) -> float:
    """
    Calculate daily fresh water production from snow melting and summer lake pumping.
    Winter snow melting is accelerated by generator CHP thermal waste heat.
    """
    if plant_status in {"FAILED", "MAINTENANCE"}:
        return round(plant_capacity_liters * 0.15, 2)  # Emergency reserve gravity melt

    season = weather.get("season", "SUMMER")
    temp = weather.get("temperature_c", -10.0)

    if season == "SUMMER" and temp > -5.0:
        # Summer mode: direct pumping from meltwater lakes / surface runoff
        # High availability and low thermal energy requirement
        summer_yield = plant_capacity_liters * random.uniform(0.85, 1.05)
        if power_shortage:
            summer_yield *= 0.50
        return round(min(plant_capacity_liters * 1.10, summer_yield), 2)

    # Winter mode: thermal snow melting
    # Requires heat: ~93 kWh thermal to melt and heat 1000 L of sub-zero snow to 10 C
    snow_depth = max(2.0, weather.get("snow_depth_cm", 10.0))
    snow_availability = min(1.0, 0.40 + (snow_depth / 25.0))

    # Thermal contribution from genset CHP recovery
    chp_boost = min(1.0, chp_waste_heat_kw / 80.0) if chp_waste_heat_kw > 0 else 0.20
    power_factor = 0.30 if power_shortage else 1.0

    winter_yield = plant_capacity_liters * snow_availability * (0.60 + 0.40 * chp_boost) * power_factor
    return round(max(500.0, min(plant_capacity_liters, winter_yield)), 2)


def calculate_water_quality(
    weather: Dict[str, Any],
    water_plant_status: str = "OPERATIONAL",
    days_since_filter_change: int = 30,
) -> float:
    """
    Dynamic water quality index (0 to 100).
    Degrades during blizzards (turbidity) and filter membrane fouling.
    """
    base_quality = 98.5

    # Blizzard turbidity penalty
    severity = weather.get("weather_severity", 0.0)
    turbidity_penalty = (severity / 100.0) * 3.5 if severity > 40.0 else 0.0

    # Filter wear penalty
    filter_penalty = min(6.0, (days_since_filter_change / 90.0) * 4.0)

    # Plant maintenance degradation
    status_penalty = 8.0 if water_plant_status == "DEGRADED" else (15.0 if water_plant_status == "MAINTENANCE" else 0.0)

    # Stochastic sensor noise
    noise = random.gauss(0.0, 0.4)

    quality = base_quality - turbidity_penalty - filter_penalty - status_penalty + noise
    return round(max(70.0, min(99.9, quality)), 2)


def simulate_water(
    previous_storage: float,
    tank_capacity: float,
    population: int,
    weather: Dict[str, Any],
    daily_capacity: float = None,
    power_available: bool = True,
    power_shortage_event: bool = False,
    chp_waste_heat_kw: float = 0.0,
    water_plant_status: str = "OPERATIONAL",
    days_since_filter_change: int = 30,
) -> Dict[str, Any]:
    """
    Main entry point for daily water supply and life support simulation.
    """
    season = weather.get("season", "SUMMER")
    demand = total_water_demand(population, season)
    plant_capacity = daily_capacity or 5000.0

    is_power_constrained = power_shortage_event or not power_available
    production = snow_melting_output(
        weather=weather,
        plant_capacity_liters=plant_capacity,
        power_shortage=is_power_constrained,
        chp_waste_heat_kw=chp_waste_heat_kw,
        plant_status=water_plant_status,
    )

    storage = max(0.0, min(tank_capacity, previous_storage - demand + production))
    days_remaining = 999.0 if demand <= 0.01 else round(storage / demand, 1)

    if days_remaining > 30.0:
        status = "GOOD"
    elif days_remaining > 15.0:
        status = "LOW"
    elif days_remaining > 7.0:
        status = "CRITICAL"
    else:
        status = "EMERGENCY"

    shortage = (demand > (previous_storage + production)) or (storage <= 0.0)
    quality = calculate_water_quality(weather, water_plant_status, days_since_filter_change)

    if is_power_constrained:
        snow_plant_status = "POWER_LIMITED"
    elif water_plant_status == "MAINTENANCE":
        snow_plant_status = "MAINTENANCE"
    elif water_plant_status == "FAILED":
        snow_plant_status = "OFFLINE"
    else:
        snow_plant_status = "RUNNING"

    return {
        "daily_water_consumption_liters": round(demand, 2),
        "daily_water_production_liters": round(production, 2),
        "water_storage_liters": round(storage, 2),
        "water_balance_liters": round(production - demand, 2),
        "water_days_remaining": days_remaining,
        "water_status": status,
        "water_quality_index": quality,
        "snow_melting_plant_status": snow_plant_status,
        "water_refill_event": False,
        "water_shortage_event": shortage,
        "water_emergency": days_remaining <= 7.0,
        "water_plant_utilisation_percent": round(min(100.0, (production / plant_capacity) * 100.0), 2),
    }
