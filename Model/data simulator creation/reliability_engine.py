"""
reliability_engine.py
---------------------
Asset health, mechanical wear, preventive maintenance scheduling,
and stochastic equipment failure dynamics for Antarctic research stations.

Antarctica Digital Twin | SIH Project
"""

import math
import random
from typing import Dict, Any, Tuple

# ==========================================================
# EQUIPMENT SPECIFICATIONS
# Format: (design_life_hours, service_interval_hours, weibull_shape_beta, required_spares)
# ==========================================================

EQUIPMENT_SPECS = {
    "generator_1": {
        "life_hours": 12000.0,
        "service_interval": 720.0,    # Service every 30 operating days
        "beta": 2.2,                  # Wear-out phase hazard curve
        "spares": ["Engine Oil", "Fuel Filters", "Generator Spare Parts"],
        "criticality": "HIGH",
    },
    "generator_2": {
        "life_hours": 12000.0,
        "service_interval": 720.0,
        "beta": 2.2,
        "spares": ["Engine Oil", "Fuel Filters", "Generator Spare Parts"],
        "criticality": "HIGH",
    },
    "generator_3": {
        "life_hours": 12000.0,
        "service_interval": 720.0,
        "beta": 2.2,
        "spares": ["Engine Oil", "Fuel Filters", "Generator Spare Parts"],
        "criticality": "HIGH",
    },
    "battery_inverter": {
        "life_hours": 35000.0,
        "service_interval": 4320.0,   # 180 days
        "beta": 1.6,
        "spares": ["Electrical Cables"],
        "criticality": "HIGH",
    },
    "solar_inverter": {
        "life_hours": 30000.0,
        "service_interval": 4320.0,
        "beta": 1.5,
        "spares": ["Electrical Cables"],
        "criticality": "MEDIUM",
    },
    "water_plant": {
        "life_hours": 16000.0,
        "service_interval": 1440.0,   # 60 days
        "beta": 1.8,
        "spares": ["Water Filters", "Bearings"],
        "criticality": "HIGH",
    },
    "communication_vsat": {
        "life_hours": 20000.0,
        "service_interval": 2160.0,   # 90 days
        "beta": 1.4,
        "spares": ["Electrical Cables"],
        "criticality": "MEDIUM",
    },
    "heating_boiler": {
        "life_hours": 24000.0,
        "service_interval": 1440.0,
        "beta": 1.7,
        "spares": ["Bearings", "Bolts"],
        "criticality": "HIGH",
    },
}


def initialize_reliability() -> Dict[str, Any]:
    """Initialize state tracking for all station physical assets."""
    state = {}
    for name, spec in EQUIPMENT_SPECS.items():
        state[name] = {
            "operating_hours": 0.0,
            "hours_since_service": 0.0,
            "maintenance_due_hours": spec["service_interval"],
            "wear_index": 0.0,            # 0.0 (new) to 1.0 (end of design life)
            "status": "OPERATIONAL",       # OPERATIONAL | MAINTENANCE | DEGRADED | FAILED
            "repair_days_remaining": 0,
            "total_failures": 0,
            "total_maintenance_events": 0,
            "deferred_maintenance_days": 0,
            "uptime_days": 0,
            "downtime_days": 0,
        }
    return state


def _weibull_failure_probability(hours: float, life_hours: float, beta: float, dt_hours: float = 24.0) -> float:
    """Calculate Weibull conditional failure probability over time increment dt."""
    if hours <= 0:
        return 0.0
    eta = life_hours
    # Hazard rate h(t) = (beta / eta) * (t / eta)^(beta - 1)
    hazard = (beta / eta) * ((hours / eta) ** (beta - 1.0))
    prob = 1.0 - math.exp(-hazard * dt_hours)
    return max(0.0, min(0.40, prob))


def advance_reliability(
    state: Dict[str, Any],
    power_telemetry: Dict[str, Any],
    water_telemetry: Dict[str, Any],
    connectivity_telemetry: Dict[str, Any],
    inventory_available_map: Dict[str, float] = None,
) -> Dict[str, Any]:
    """
    Advance asset health, service countdowns, and stochastic breakdowns.

    Parameters
    ----------
    state : Dict of asset states.
    power_telemetry : Output from power_engine.
    water_telemetry : Output from water_engine.
    connectivity_telemetry : Output from connectivity_engine.
    inventory_available_map : Current on-hand quantities of spare parts.
    """
    inventory_map = inventory_available_map or {}
    active_gensets = power_telemetry.get("active_generators", 1)
    gen_hours = power_telemetry.get("generator_runtime_hours", 0.0)

    # Runtime assignment per asset for the day
    runtime_map = {
        "generator_1": gen_hours if active_gensets >= 1 else 0.0,
        "generator_2": gen_hours if active_gensets >= 2 else 0.0,
        "generator_3": gen_hours if active_gensets >= 3 else 0.0,
        "battery_inverter": 24.0 if power_telemetry.get("battery_discharge_kw", 0.0) > 0.1 else 8.0,
        "solar_inverter": 24.0 if power_telemetry.get("solar_generation_kw", 0.0) > 0.1 else 0.0,
        "water_plant": 24.0 if water_telemetry.get("daily_water_production_liters", 0.0) > 0.1 else 0.0,
        "communication_vsat": 24.0 if connectivity_telemetry.get("connectivity_status") != "OFFLINE" else 0.0,
        "heating_boiler": 24.0 if power_telemetry.get("heating_load_kw", 0.0) > 0.1 else 0.0,
    }

    maintenance_events_today = 0
    equipment_failures_today = 0
    failed_critical_assets = []
    spares_consumed = []

    for name, item in state.items():
        spec = EQUIPMENT_SPECS[name]
        hours_today = runtime_map.get(name, 0.0)

        # Handle active repairs or service
        if item["repair_days_remaining"] > 0:
            item["repair_days_remaining"] -= 1
            item["downtime_days"] += 1
            if item["repair_days_remaining"] == 0:
                item["status"] = "OPERATIONAL"
                item["hours_since_service"] = 0.0
                item["maintenance_due_hours"] = spec["service_interval"]
            else:
                item["status"] = "MAINTENANCE" if item["status"] != "FAILED" else "FAILED"
            continue

        # Asset is running
        item["uptime_days"] += 1
        item["operating_hours"] += hours_today
        item["hours_since_service"] += hours_today
        item["maintenance_due_hours"] -= hours_today
        item["wear_index"] = min(1.0, round(item["operating_hours"] / spec["life_hours"], 4))

        # Check if preventive maintenance interval reached
        if item["maintenance_due_hours"] <= 0:
            # Check spare parts availability
            has_spares = all(inventory_map.get(spare, 100) > 0 for spare in spec["spares"])
            if has_spares:
                item["status"] = "MAINTENANCE"
                item["repair_days_remaining"] = 1  # 1-day routine service
                item["total_maintenance_events"] += 1
                maintenance_events_today += 1
                item["deferred_maintenance_days"] = 0
                for s in spec["spares"]:
                    spares_consumed.append(s)
                continue
            else:
                # Deferred maintenance multiplies risk of failure
                item["deferred_maintenance_days"] += 1
                item["status"] = "DEGRADED"

        # Check stochastic failure probability via Weibull model
        fail_prob = _weibull_failure_probability(
            item["operating_hours"],
            spec["life_hours"],
            spec["beta"],
            hours_today
        )
        # Deferred maintenance or high wear escalates failure probability
        if item["deferred_maintenance_days"] > 0:
            fail_prob *= (1.0 + item["deferred_maintenance_days"] * 0.05)
        if item["wear_index"] > 0.85:
            fail_prob *= 2.0

        if random.random() < fail_prob:
            item["status"] = "FAILED"
            item["repair_days_remaining"] = random.randint(2, 5)  # 2 to 5 days unscheduled repair
            item["total_failures"] += 1
            equipment_failures_today += 1
            if spec["criticality"] == "HIGH":
                failed_critical_assets.append(name)
        else:
            if item["deferred_maintenance_days"] == 0:
                item["status"] = "OPERATIONAL"

    # Overall asset availability across all components
    total_days = max(1, sum(v["uptime_days"] + v["downtime_days"] for v in state.values()))
    availability_pct = round(sum(v["uptime_days"] for v in state.values()) / total_days * 100.0, 2)

    # Primary generator status for backward compatibility
    gen1_status = state["generator_1"]["status"]
    gen_maintenance_status = "OK" if gen1_status == "OPERATIONAL" else gen1_status

    return {
        "generator_maintenance_status": gen_maintenance_status,
        "maintenance_events_today": maintenance_events_today,
        "equipment_failures_today": equipment_failures_today,
        "generator_operating_hours": round(state["generator_1"]["operating_hours"], 2),
        "battery_cycle_count": round(state["battery_inverter"]["operating_hours"] / 24.0, 2),
        "equipment_availability_percent": availability_pct,
        "failed_critical_assets": failed_critical_assets,
        "spares_consumed_today": spares_consumed,
        "generator_1_status": state["generator_1"]["status"],
        "generator_2_status": state["generator_2"]["status"],
        "generator_3_status": state["generator_3"]["status"],
        "battery_inverter_status": state["battery_inverter"]["status"],
        "solar_inverter_status": state["solar_inverter"]["status"],
        "water_plant_status": state["water_plant"]["status"],
        "heating_boiler_status": state["heating_boiler"]["status"],
        "communication_vsat_status": state["communication_vsat"]["status"],
    }
