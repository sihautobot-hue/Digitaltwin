"""
risk_engine.py
--------------
Explainable multi-criteria operational risk engine for Antarctic research stations.
Evaluates microgrid health, fuel runway, consumable stocks, asset wear,
life support water, communications, and structural occupancy risks.

Antarctica Digital Twin | SIH Project
"""

from typing import Dict, Any, Tuple


def _cap(value: float) -> float:
    """Clamp score into [0.0, 100.0]."""
    return round(min(100.0, max(0.0, float(value))), 2)


def power_risk(power: Dict[str, Any], reliability: Dict[str, Any] = None) -> Tuple[float, str]:
    """Evaluate power generation, battery reserve, and microgrid loading risks."""
    score, reasons = 0.0, []
    soc = power.get("battery_soc_percent", power.get("battery_soc", 100.0))

    if soc < 20.0:
        score += 38.0
        reasons.append("battery below emergency reserve (<20%)")
    elif soc < 35.0:
        score += 20.0
        reasons.append("low battery reserve (<35%)")

    runtime = power.get("generator_runtime_hours", 0.0)
    if runtime > 20.0:
        score += 15.0
        reasons.append("near-continuous generator runtime (>20h)")

    status = power.get("generator_status", "OFF")
    if status == "HIGH":
        score += 15.0
        reasons.append("high generator loading")
    elif status == "OVERLOAD":
        score += 35.0
        reasons.append("generator overload condition")

    unserved = power.get("unserved_energy_kwh", power.get("load_shedding_kwh", 0.0))
    if unserved > 0.1:
        score += min(50.0, 25.0 + (unserved / 15.0))
        reasons.append("active electrical load shedding")

    if reliability:
        if reliability.get("generator_1_status") in {"FAILED", "MAINTENANCE"}:
            score += 18.0
            reasons.append("primary genset offline/maintenance")

    return _cap(score), "; ".join(reasons) or "power supply within operating envelope"


def fuel_risk(fuel: Dict[str, Any]) -> Tuple[float, str]:
    """Evaluate fuel runway, delivery delays, and tank exhaustion risks."""
    score, reasons = 0.0, []
    days = fuel.get("fuel_days_remaining", 999.0)

    if fuel.get("fuel_shortage_event") or days <= 0.0:
        score += 65.0
        reasons.append("fuel stock exhausted")
    elif days < 14.0:
        score += 45.0
        reasons.append(f"critical fuel runway ({days:.1f} days remaining)")
    elif days < 35.0:
        score += 22.0
        reasons.append(f"low fuel reserve ({days:.1f} days remaining)")

    if fuel.get("fuel_shipments_pending", 0) > 0:
        score += 6.0
        reasons.append("fuel shipment pending")

    if fuel.get("fuel_shipment_status") == "Delayed" or fuel.get("fuel_shipment_delayed_today"):
        score += 18.0
        reasons.append("resupply vessel delayed at sea")

    eta = fuel.get("fuel_eta_days", -1)
    if eta > 60:
        score += 10.0
        reasons.append("long delivery ETA (>60 days)")

    return _cap(score), "; ".join(reasons) or "fuel reserve adequate"


def inventory_risk(inventory: Dict[str, Any]) -> Tuple[float, str]:
    """Evaluate spare parts and critical consumable availability risks."""
    score, reasons = 0.0, []
    shortages = inventory.get("inventory_shortage_items", 0)
    critical = inventory.get("critical_items", 0)
    low = inventory.get("low_items", 0)

    if shortages > 0:
        score += min(60.0, shortages * 18.0)
        reasons.append("active consumable shortages")
    if critical > 0:
        score += min(28.0, critical * 7.0)
        reasons.append(f"{critical} critical inventory item(s) below threshold")
    if low > 0:
        score += min(16.0, low * 2.0)
        reasons.append(f"{low} low inventory item(s)")
    if inventory.get("expired_quantity", 0.0) > 0.0:
        score += 8.0
        reasons.append("expired stock discarded")
    if inventory.get("delayed_shipments", 0) > 0:
        score += 10.0
        reasons.append("cargo shipments delayed")

    return _cap(score), "; ".join(reasons) or "inventory stock adequate"


def weather_risk(weather: Dict[str, Any]) -> Tuple[float, str]:
    """Evaluate meteorological severity, blizzard conditions, and wind hazards."""
    severity = weather.get("weather_severity", 0.0)
    score = severity * 0.55
    reasons = []

    w_type = weather.get("weather_type", "NORMAL")
    if w_type in {"BLIZZARD", "WHITEOUT"}:
        score += 25.0
        reasons.append(f"extreme {w_type.lower()} storm")
    if weather.get("visibility_m", 9999) < 500:
        score += 10.0
        reasons.append("low visibility (<500m)")
    if weather.get("wind_speed_kmh", 0) > 75.0:
        score += 12.0
        reasons.append("severe wind gust hazard")

    return _cap(score), "; ".join(reasons) or "weather within operating envelope"


def water_risk(water: Dict[str, Any]) -> Tuple[float, str]:
    """Evaluate domestic and laboratory water reserves and quality."""
    days = water.get("water_days_remaining", 999.0)
    quality = water.get("water_quality_index", 98.0)
    score = 0.0
    reasons = []

    if water.get("water_status") == "EMERGENCY" or days <= 7.0:
        score += 55.0
        reasons.append("critical water reserve (<7 days)")
    elif days < 15.0:
        score += 30.0
        reasons.append("low water storage (<15 days)")
    elif days < 30.0:
        score += 12.0
        reasons.append("moderate water reserve")

    if water.get("snow_melting_plant_status") == "POWER_LIMITED":
        score += 15.0
        reasons.append("snow melting power-limited")

    if quality < 85.0:
        score += 18.0
        reasons.append("water quality index degraded")

    return _cap(score), "; ".join(reasons) or "water storage and quality adequate"


def connectivity_risk(connectivity: Dict[str, Any], state: Dict[str, Any]) -> Tuple[float, str]:
    """Evaluate satellite communication link and data backlog risk."""
    status = connectivity.get("connectivity_status", "ONLINE")
    if status == "OFFLINE":
        state["offline_days"] = state.get("offline_days", 0) + 1
    else:
        state["offline_days"] = 0

    score = 55.0 if status == "OFFLINE" else (28.0 if status == "LIMITED" else (12.0 if status == "DEGRADED" else 0.0))
    buffer_mb = connectivity.get("buffered_data_mb", 0.0)
    score += min(20.0, buffer_mb / 150.0)

    if state.get("offline_days", 0) >= 3:
        score += 15.0

    reason = (
        "satellite link offline" if status == "OFFLINE" else
        ("communications degraded" if score > 0 else "communications online")
    )
    return _cap(score), reason


def occupancy_risk(population: Dict[str, Any], station=None) -> Tuple[float, str]:
    """Evaluate station physical occupancy and crowding risk."""
    occupancy = population.get("occupancy_percent", 0.0)
    score = 50.0 if occupancy > 100.0 else (22.0 if occupancy > 90.0 else 0.0)
    reason = (
        "station capacity exceeded (>100%)" if occupancy > 100.0 else
        ("high occupancy (>90%)" if score > 0 else "occupancy within design capacity")
    )
    return _cap(score), reason


def evaluate_station(
    weather: Dict[str, Any],
    power: Dict[str, Any],
    fuel: Dict[str, Any],
    water: Dict[str, Any],
    inventory: Dict[str, Any],
    connectivity: Dict[str, Any],
    station=None,
    population=None,
    risk_state: Dict[str, Any] = None,
    reliability: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Compute comprehensive multi-system operational risk score and explanations.
    """
    state = risk_state if risk_state is not None else {}
    pop_data = population or {}

    components = {
        "power": power_risk(power, reliability),
        "fuel": fuel_risk(fuel),
        "inventory": inventory_risk(inventory),
        "weather": weather_risk(weather),
        "water": water_risk(water),
        "connectivity": connectivity_risk(connectivity, state),
        "occupancy": occupancy_risk(pop_data, station),
    }

    weights = getattr(station, "risk_weights", None) or {
        "power": 0.25, "fuel": 0.20, "inventory": 0.15,
        "weather": 0.10, "water": 0.10, "connectivity": 0.10,
        "occupancy": 0.10,
    }

    total_score = _cap(sum(components[name][0] * weights.get(name, 0.14) for name in components))
    thresholds = getattr(station, "risk_level_thresholds", None) or {"medium": 30, "high": 60, "critical": 80}

    if total_score >= thresholds["critical"]:
        level = "CRITICAL"
    elif total_score >= thresholds["high"]:
        level = "HIGH"
    elif total_score >= thresholds["medium"]:
        level = "MEDIUM"
    else:
        level = "LOW"

    top_name, top_val = max(components.items(), key=lambda entry: entry[1][0])

    return {
        "power_risk": components["power"][0],
        "fuel_risk": components["fuel"][0],
        "inventory_risk": components["inventory"][0],
        "weather_risk": components["weather"][0],
        "water_risk": components["water"][0],
        "connectivity_risk": components["connectivity"][0],
        "occupancy_risk": components["occupancy"][0],
        "overall_risk_score": total_score,
        "overall_risk_level": level,
        "top_risk_factor": top_name,
        "top_risk_reason": top_val[1],
        "risk_score": total_score,
        "risk_level": level,
        "station_health": round(100.0 - total_score, 2),
        "risk_breakdown": {name: val[0] for name, val in components.items()},
    }
