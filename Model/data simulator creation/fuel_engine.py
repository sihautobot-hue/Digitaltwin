"""
fuel_engine.py
--------------
Fuel dynamics, multi-genset specific fuel consumption, CHP thermal recovery,
and realistic multi-leg Antarctic maritime logistics.

Antarctica Digital Twin | SIH Project
"""

import math
import random
from typing import Dict, Any, Tuple, List

from station_config import is_shipping_season, SHIPPING_WINDOW_MONTHS


def specific_fuel_consumption(generator_output_kw: float, generator_capacity_kw: float) -> float:
    """
    Calculate specific fuel consumption (Liters per kWh) as a function of generator load factor.
    Modern turbocharged Antarctic marine diesel genset curve.
    """
    if generator_output_kw <= 0.0 or generator_capacity_kw <= 0.0:
        return 0.0
    load_fraction = generator_output_kw / generator_capacity_kw
    if load_fraction < 0.30:
        return 0.36
    elif load_fraction < 0.50:
        return 0.31
    elif load_fraction < 0.75:
        return 0.27
    elif load_fraction <= 1.00:
        return 0.28
    else:
        # Overload rich combustion
        return 0.33


def daily_fuel_consumption(
    generator_output_kw: float,
    generator_runtime_hours: float,
    generator_capacity_kw: float,
    active_generators: int = 1,
) -> Tuple[float, float, float]:
    """
    Compute daily fuel consumed (Liters), average specific fuel rate (L/kWh),
    and recovered CHP thermal waste heat (kW thermal).
    """
    if generator_runtime_hours <= 0.0 or generator_output_kw <= 0.0:
        return 0.0, 0.0, 0.0

    rate = specific_fuel_consumption(generator_output_kw, generator_capacity_kw)
    base_fuel_liters = generator_output_kw * generator_runtime_hours * rate

    # Cold startup penalty (1.5 L per active engine)
    startup_fuel = active_generators * 1.5 if generator_runtime_hours > 0 else 0.0
    total_fuel_liters = round(base_fuel_liters + startup_fuel, 2)

    # Diesel heating value: ~9.8 kWh thermal per liter
    # Total fuel thermal input (kW)
    fuel_energy_rate_kw = (total_fuel_liters * 9.8) / max(1.0, generator_runtime_hours)
    # Waste heat available = Input energy - Electric Output
    waste_heat_kw = max(0.0, fuel_energy_rate_kw - generator_output_kw)
    # Recovered CHP heat with 45% jacket + exhaust heat exchanger efficiency
    chp_recovered_kw = waste_heat_kw * 0.45

    return total_fuel_liters, rate, round(chp_recovered_kw, 2)


def available_fuel_energy_kwh(fuel_liters: float, planning_fuel_rate_l_per_kwh: float = 0.30) -> float:
    """Convert available fuel stock into maximum deliverable electric kWh."""
    return max(0.0, fuel_liters) / planning_fuel_rate_l_per_kwh


def initialize_fuel_logistics(station) -> Dict[str, Any]:
    """Create persistent state for maritime resupply voyages."""
    station_id = getattr(station, "station_id", "STATION")
    return {
        "next_shipment_number": 1,
        "shipments": [],
        "station_id": station_id,
        "last_resupply_day": -365,
    }


def _access_factor(station) -> float:
    """Ice access difficulty factor based on latitude and location."""
    if not station:
        return 1.0
    # Bharati (Larsemann Hills ~69.4S) has slightly earlier sea ice breakup than Maitri (~70.8S)
    return 1.0 + max(0.0, abs(station.latitude) - 69.0) * 0.05


def _delay_probability(weather: Dict[str, Any], season: str, station) -> float:
    """Compute Southern Ocean storm delay probability for transiting icebreakers."""
    weather_type = weather.get("weather_type", "NORMAL")
    base = {
        "HIGH_WIND": 0.15,
        "HEAVY_SNOW": 0.25,
        "WHITEOUT": 0.50,
        "BLIZZARD": 0.75,
    }.get(weather_type, 0.0)
    severity = max(0.0, float(weather.get("weather_severity", 0)) - 40.0) / 200.0
    winter_ice = 0.30 if season == "WINTER" else 0.0
    return min(0.85, (base + severity + winter_ice) * _access_factor(station))


def _schedule_fuel_shipment(
    state: Dict[str, Any],
    day_index: int,
    current_date,
    station,
    tank_capacity: float,
    stock: float,
    daily_use: float,
) -> bool:
    """
    Schedule annual expedition fuel resupply vessel during valid shipping seasons.
    Strictly prohibits ship departures/arrivals during winter sea-ice freeze.
    """
    active = [s for s in state["shipments"] if s["status"] in {"Planned", "En Route", "Delayed"}]
    if active:
        return False

    month = current_date.month if hasattr(current_date, "month") else 1
    # Resupply vessels are planned in Indian/Cape Town spring (October/November) to arrive in summer (Dec-Feb)
    # Reorder trigger: stock below 60% capacity OR annual expedition cycle (every ~300-365 days in summer)
    is_annual_resupply_window = (month in [11, 12, 1]) and (day_index - state.get("last_resupply_day", -365) >= 280)
    reorder_level = tank_capacity * 0.55

    if not (stock <= reorder_level or is_annual_resupply_window):
        return False

    # Lead time across multi-leg route (Goa -> Mumbai -> Cape Town -> Antarctica) ~ 45 to 75 days
    lead_days = int(round(random.randint(45, 75) * _access_factor(station)))
    departure = day_index + 5
    arrival = departure + lead_days

    # Order quantity: fill up to 92% of tank capacity
    quantity = min(tank_capacity * 0.70, max(tank_capacity * 0.30, tank_capacity * 0.92 - stock))
    number = state["next_shipment_number"]
    state["next_shipment_number"] += 1

    state["shipments"].append({
        "shipment_id": f"FUEL-{state['station_id']}-{number:03d}",
        "shipment_type": "POLAR_DIESEL",
        "route": "Goa-Mumbai-CapeTown-Antarctica",
        "departure_day": departure,
        "arrival_day": arrival,
        "quantity": round(quantity, 2),
        "status": "Planned",
        "delay_days": 0,
    })
    return True


def _advance_shipments(
    state: Dict[str, Any],
    day_index: int,
    current_date,
    weather: Dict[str, Any],
    season: str,
    station,
) -> Tuple[float, bool, List[int]]:
    """Advance maritime shipments and receive fuel during navigable windows."""
    received = 0.0
    delayed_today = False
    delivery_days = []

    for shipment in state["shipments"]:
        if shipment["status"] == "Planned" and day_index >= shipment["departure_day"]:
            shipment["status"] = "En Route"

        if shipment["status"] not in {"En Route", "Delayed"}:
            continue

        # Weather delay at sea
        if random.random() < _delay_probability(weather, season, station):
            shipment["arrival_day"] += 1
            shipment["delay_days"] += 1
            shipment["status"] = "Delayed"
            delayed_today = True
            continue

        # Arrival condition: must reach arrival day AND sea ice must allow vessel docking
        if day_index >= shipment["arrival_day"]:
            if is_shipping_season(current_date):
                shipment["status"] = "Arrived"
                received += shipment["quantity"]
                delivery_days.append(day_index - shipment["departure_day"])
                state["last_resupply_day"] = day_index
            else:
                # Vessel arrives outside shipping window: forced to wait off pack-ice edge
                shipment["status"] = "Delayed"
                shipment["arrival_day"] += 1
                shipment["delay_days"] += 1
                delayed_today = True
        elif shipment["status"] == "Delayed":
            shipment["status"] = "En Route"

    return round(received, 2), delayed_today, delivery_days


def fuel_days_remaining(stock: float, daily_use: float) -> float:
    """Calculate reserve endurance in days."""
    return 999.0 if daily_use <= 0.01 else round(stock / daily_use, 1)


def fuel_status(days: float) -> str:
    """Categorical fuel reserve health."""
    if days > 60.0:
        return "GOOD"
    elif days > 30.0:
        return "LOW"
    elif days > 14.0:
        return "CRITICAL"
    else:
        return "EMERGENCY"


def simulate_fuel(
    previous_stock: float,
    tank_capacity: float,
    generator_output_kw: float,
    generator_runtime_hours: float,
    generator_capacity_kw: float,
    weather_severity: float = None,
    logistics_state: Dict[str, Any] = None,
    day_index: int = 0,
    weather: Dict[str, Any] = None,
    station=None,
    active_generators: int = 1,
    current_date=None,
) -> Dict[str, Any]:
    """
    Main entry point for daily fuel consumption and logistics simulation.
    """
    consumed, fuel_rate, chp_heat_kw = daily_fuel_consumption(
        generator_output_kw, generator_runtime_hours, generator_capacity_kw, active_generators
    )

    stock = max(0.0, previous_stock - consumed)
    weather = weather or {"weather_severity": weather_severity or 0, "weather_type": "NORMAL", "season": "SUMMER"}
    season = weather.get("season", "SUMMER")
    state = logistics_state if logistics_state is not None else {"next_shipment_number": 1, "shipments": [], "station_id": "UNKNOWN"}

    # Track current date or synthesize from day_index
    if current_date is None:
        from datetime import datetime, timedelta
        current_date = datetime(2025, 1, 1) + timedelta(days=day_index)

    received, delayed_today, delivery_days = _advance_shipments(state, day_index, current_date, weather, season, station)
    stock = min(tank_capacity, stock + received)

    created = _schedule_fuel_shipment(state, day_index, current_date, station, tank_capacity, stock, consumed)

    pending = [s for s in state["shipments"] if s["status"] in {"Planned", "En Route", "Delayed"}]
    status = pending[0]["status"] if pending else ("Arrived" if received > 0 else "NONE")
    eta = min((max(0, s["arrival_day"] - day_index) for s in pending), default=-1)
    days = fuel_days_remaining(stock, consumed)

    return {
        "fuel_stock_liters": round(stock, 2),
        "fuel_consumed_today_liters": consumed,
        "fuel_days_remaining": days,
        "fuel_status": fuel_status(days),
        "fuel_efficiency_l_per_kwh": round(fuel_rate, 4),
        "generator_runtime_hours": round(generator_runtime_hours, 2),
        "refuel_event": received > 0,
        "refuel_quantity_liters": round(received, 2),
        "fuel_shipment_status": status,
        "fuel_shipments_pending": len(pending),
        "fuel_eta_days": eta,
        "fuel_received_today_liters": round(received, 2),
        "fuel_shortage_event": stock <= 0.0,
        "fuel_shipment_created_today": created,
        "fuel_shipment_delayed_today": delayed_today,
        "fuel_delivery_days": delivery_days[0] if delivery_days else -1,
        "chp_waste_heat_kw": chp_heat_kw,
    }
