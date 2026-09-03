"""
population_engine.py
--------------------
Human dynamics engine modeling the annual Indian Antarctic Expedition (IAE),
summer scientific influx, winter-over core team lockdown,
trade specialization, and weather-gated emergency evacuations.

Antarctica Digital Twin | SIH Project
"""

import random
from datetime import datetime
from typing import Dict, Any

from station_config import get_season, SUMMER_MONTHS, WINTER_MONTHS


def initialize_population(station) -> Dict[str, Any]:
    """Initialize station population state for multi-year simulation."""
    station_name = getattr(station, "station_name", "Station")
    max_pop = getattr(station, "max_population", 47)
    return {
        "station_name": station_name,
        "total_population": random.randint(38, min(max_pop, 46)),
        "temporary_workers": 0,
        "temporary_days_left": 0,
        "days_until_ship": random.randint(30, 60),
        "days_until_rotation": 120,
    }


def staff_distribution(total: int, season: str) -> Dict[str, int]:
    """
    Distribute station complement across professional specialties.
    Ensures the sum of trades exactly equals total population without rounding mismatch.
    """
    if total <= 0:
        return {
            "scientists": 0, "engineers": 0, "technicians": 0,
            "logistics": 0, "medical": 0, "visitors": 0
        }

    # Proportions conditioned on seasonal mission profile
    if season == "SUMMER":
        # Heavy field science and summer maintenance projects
        ratios = {"scientists": 0.36, "engineers": 0.24, "technicians": 0.20, "logistics": 0.12, "medical": 0.05}
    else:
        # Winter lockdown: core life-support engineering, base maintenance, long-term monitoring
        ratios = {"scientists": 0.22, "engineers": 0.35, "technicians": 0.26, "logistics": 0.12, "medical": 0.05}

    scientists = max(1, int(round(total * ratios["scientists"])))
    engineers = max(1, int(round(total * ratios["engineers"])))
    technicians = max(1, int(round(total * ratios["technicians"])))
    logistics = max(1, int(round(total * ratios["logistics"])))
    medical = max(1, int(round(total * ratios["medical"])))

    allocated = scientists + engineers + technicians + logistics + medical
    visitors = max(0, total - allocated)

    # Rebalance if rounding slightly exceeded total
    while (scientists + engineers + technicians + logistics + medical + visitors) > total:
        if visitors > 0:
            visitors -= 1
        elif scientists > 2:
            scientists -= 1
        elif engineers > 2:
            engineers -= 1
        else:
            break

    return {
        "scientists": scientists,
        "engineers": engineers,
        "technicians": technicians,
        "logistics": logistics,
        "medical": medical,
        "visitors": visitors,
    }


def simulate_population(
    state: Dict[str, Any],
    date,
    station,
    weather: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Advance station population and personnel demographics for one day.
    """
    season = get_season(date)
    month = date.month if hasattr(date, "month") else 1
    max_cap = getattr(station, "max_population", 47)
    weather_severity = weather.get("weather_severity", 0.0) if weather else 0.0

    # 1. Annual Expedition Seasonality & Handover Cycles
    if month in [12, 1, 2]:
        # Peak summer expedition period (38 to 47 personnel)
        target_base = random.randint(38, max_cap)
        # Smooth gradual drift towards target
        current = state["total_population"]
        if current < target_base:
            state["total_population"] = min(max_cap, current + random.choice([0, 1, 2]))
        elif current > target_base:
            state["total_population"] = max(35, current - random.choice([0, 1]))

    elif month in [3, 4]:
        # Autumn de-induction & summer team departure
        target_winter = random.randint(19, 25)
        if state["total_population"] > target_winter:
            # Summer personnel leave in groups if weather permits
            if weather_severity < 45.0:
                state["total_population"] = max(target_winter, state["total_population"] - random.choice([0, 1, 2, 3]))

    elif month in [5, 6, 7, 8, 9]:
        # Polar winter lockdown: fixed core crew (18 to 26 personnel)
        # Isolated with zero flights or routine departures
        state["total_population"] = max(18, min(26, state["total_population"]))

    else:
        # October / November: Spring preparations for next incoming expedition
        target_spring = random.randint(22, 30)
        if state["total_population"] < target_spring and month == 11 and weather_severity < 40.0:
            state["total_population"] = min(max_cap, state["total_population"] + random.choice([0, 1, 2]))

    # 2. Emergency Medical Evacuation (rare, only in summer and during clear weather)
    if season == "SUMMER" and weather_severity < 35.0:
        if random.random() < 0.0015 and state["total_population"] > 15:
            state["total_population"] -= 1

    total = int(max(18, min(max_cap, state["total_population"])))
    state["total_population"] = total

    staff = staff_distribution(total, season)
    occupancy_pct = round((total / max_cap) * 100.0, 2)

    return {
        "station_name": getattr(station, "station_name", state.get("station_name", "Station")),
        "date": date,
        "season": season,
        "total_population": total,
        "occupancy_percent": occupancy_pct,
        **staff,
    }