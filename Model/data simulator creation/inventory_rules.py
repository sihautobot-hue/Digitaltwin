"""
inventory_rules.py
------------------
Consumption rules, weather scaling, research multipliers,
and inventory health scoring for Antarctic station consumables.

Antarctica Digital Twin | SIH Project
"""

import random
from typing import Dict, Any, List


def weather_multiplier(weather: Dict[str, Any]) -> float:
    """Multiplier for food and medical consumption during severe weather confinement."""
    scenario = weather.get("weather_type", "NORMAL")
    if scenario == "BLIZZARD":
        return 1.25
    elif scenario == "WHITEOUT":
        return 1.15
    elif scenario == "HEAVY_SNOW":
        return 1.10
    elif scenario == "HIGH_WIND":
        return 1.05
    return 1.00


def research_multiplier(season: str) -> float:
    """Scientific laboratory consumable burn rate multiplier."""
    return 1.30 if season == "SUMMER" else 0.75


def calculate_consumption(
    item: Dict[str, Any],
    population: int,
    weather: Dict[str, Any],
    season: str,
    reliability_spares_needed: List[str] = None,
) -> float:
    """
    Calculate daily consumed quantity for an inventory item.
    """
    category = item.get("category", "")
    item_name = item.get("item", "")
    base_per_person = item.get("daily_per_person", 0.0)

    weather_factor = weather_multiplier(weather)
    research_factor = research_multiplier(season)

    consumption = base_per_person * population

    if category == "Laboratory":
        consumption *= research_factor
    elif category in {"Food", "Medical"}:
        consumption *= weather_factor
    elif category == "Power":
        severity = weather.get("weather_severity", 0.0)
        if severity > 60.0:
            consumption += random.uniform(0.2, 0.8)
    elif category == "Maintenance":
        consumption += random.uniform(0.0, 0.25)

    # If this item was specifically consumed by a preventive maintenance event today
    if reliability_spares_needed and item_name in reliability_spares_needed:
        if item_name in {"Engine Oil", "Lubricants"}:
            consumption += random.uniform(15.0, 30.0)
        elif item_name in {"Fuel Filters", "Water Filters"}:
            consumption += 1.0
        elif item_name in {"Generator Spare Parts", "Bearings", "Bolts"}:
            consumption += 1.0

    return round(max(0.0, consumption), 2)


def calculate_days_remaining(quantity: float, daily_use: float) -> float:
    """Calculate consumable runway in days."""
    if daily_use <= 0.001:
        return 999.0
    return round(quantity / daily_use, 1)


def inventory_status(quantity: float, minimum: float, critical: float) -> str:
    """Determine operational inventory alert tier."""
    if quantity <= 0.0:
        return "OUT_OF_STOCK"
    elif quantity <= critical:
        return "CRITICAL"
    elif quantity <= minimum:
        return "LOW"
    return "OK"


def inventory_health(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate aggregated inventory health score and summary metrics."""
    score = 100.0
    critical_count = 0
    low_count = 0
    delayed_count = 0
    expired_count = 0

    for item in items:
        status = item.get("status", "OK")
        if status == "LOW":
            score -= 2.0
            low_count += 1
        elif status == "CRITICAL":
            score -= 5.0
            critical_count += 1
        elif status == "OUT_OF_STOCK":
            score -= 10.0
            critical_count += 1

        if item.get("shipment_status") == "DELAYED":
            score -= 2.0
            delayed_count += 1

        if item.get("expired_quantity", 0.0) > 0.0:
            score -= 3.0
            expired_count += 1

    return {
        "inventory_health_score": round(max(0.0, score), 2),
        "critical_items": critical_count,
        "low_items": low_count,
        "delayed_shipments": delayed_count,
        "expired_items": expired_count,
    }
