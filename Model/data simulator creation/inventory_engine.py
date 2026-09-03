"""
inventory_engine.py
-------------------
FEFO multi-batch inventory simulation, purchase order pipelines,
weather delay tracking, and station consumable allocation.

Antarctica Digital Twin | SIH Project
"""

import copy
import random
from typing import Dict, Any, List, Tuple

from inventory_catalog import INVENTORY_ITEMS
from inventory_rules import calculate_consumption, calculate_days_remaining, inventory_health, inventory_status
from station_config import is_shipping_season

ACTIVE_ORDER_STATUSES = {"Planned", "En Route", "Delayed"}


def initialize_inventory(station: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Initialize inventory state with multi-batch FEFO tracking."""
    inventory = []
    station_name = station.get("station_name", "Station")
    station_id = station.get("station_id", "STATION")

    for source in INVENTORY_ITEMS:
        record = copy.deepcopy(source)
        record["station_name"] = station_name
        record["station_id"] = station_id
        record["batches"] = [{
            "batch_id": f"{record['item']}-INITIAL",
            "quantity": float(record["quantity"]),
            "arrival_day": 0,
            "expiry_day": int(record["expiry_days"]),
        }]
        record["orders"] = []
        record["next_order_number"] = 1
        inventory.append(record)
    return inventory


def _delay_probability(weather: Dict[str, Any], season: str) -> float:
    """Delay probability for cargo shipments across the Southern Ocean."""
    weather_type = weather.get("weather_type", "NORMAL")
    base = {
        "HIGH_WIND": 0.12,
        "HEAVY_SNOW": 0.25,
        "WHITEOUT": 0.50,
        "BLIZZARD": 0.72,
    }.get(weather_type, 0.0)
    severity = max(0.0, weather.get("weather_severity", 0.0) - 40.0) / 200.0
    winter_ice = 0.25 if season == "WINTER" else 0.0
    return min(0.85, base + severity + winter_ice)


def _discard_expired(batches: List[Dict[str, Any]], day_index: int) -> Tuple[List[Dict[str, Any]], float]:
    """Discard batches whose expiration date has passed."""
    valid, expired = [], 0.0
    for batch in batches:
        if batch["expiry_day"] <= day_index:
            expired += batch["quantity"]
        else:
            valid.append(batch)
    return valid, round(expired, 2)


def _consume_fefo(batches: List[Dict[str, Any]], demand: float) -> Tuple[List[Dict[str, Any]], float, float]:
    """Consume stock following First-Expired, First-Out (FEFO) principle."""
    remaining = demand
    for batch in sorted(batches, key=lambda b: (b["expiry_day"], b["arrival_day"], b["batch_id"])):
        used = min(batch["quantity"], remaining)
        batch["quantity"] = round(batch["quantity"] - used, 2)
        remaining -= used
        if remaining <= 0.0:
            break
    surviving = [b for b in batches if b["quantity"] > 0.0]
    actual_consumed = round(demand - remaining, 2)
    unmet_demand = round(max(0.0, remaining), 2)
    return surviving, actual_consumed, unmet_demand


def _advance_orders(
    item: Dict[str, Any],
    day_index: int,
    current_date,
    weather: Dict[str, Any],
    season: str,
) -> float:
    """Advance active cargo purchase orders."""
    received = 0.0
    for order in item["orders"]:
        if order["status"] == "Planned" and day_index > order["order_day"]:
            order["status"] = "En Route"

        if order["status"] not in {"En Route", "Delayed"}:
            continue

        if random.random() < _delay_probability(weather, season):
            order["arrival_day"] += 1
            order["delay_days"] += 1
            order["status"] = "Delayed"
            continue

        # Arrival condition: day reached and shipping season open
        if day_index >= order["arrival_day"]:
            if is_shipping_season(current_date):
                order["status"] = "Arrived"
                received += order["quantity"]
                item["batches"].append({
                    "batch_id": f"{order['order_id']}-BATCH",
                    "quantity": order["quantity"],
                    "arrival_day": day_index,
                    "expiry_day": day_index + item["expiry_days"],
                })
            else:
                # Wait off ice edge until summer opening
                order["status"] = "Delayed"
                order["arrival_day"] += 1
                order["delay_days"] += 1
        elif order["status"] == "Delayed":
            order["status"] = "En Route"

    return round(received, 2)


def _schedule_order(
    item: Dict[str, Any],
    day_index: int,
    daily_use: float,
    station: Dict[str, Any],
) -> bool:
    """Schedule replacement order if stock breached reorder point."""
    if any(order["status"] in ACTIVE_ORDER_STATUSES for order in item["orders"]):
        return False

    safety_buffer = station.get("inventory_safety_buffer_percent", 0.60) if isinstance(station, dict) else getattr(station, "inventory_safety_buffer_percent", 0.60)
    safety_days = max(30.0, item["lead_time"] * safety_buffer)
    reorder_point = max(item["minimum"], daily_use * (item["lead_time"] + safety_days))
    available = sum(b["quantity"] for b in item["batches"])

    if available > reorder_point:
        return False

    quantity = max(0.0, item["capacity"] - available)
    number = item["next_order_number"]
    item["next_order_number"] += 1

    item["orders"].append({
        "order_id": f"INV-{item['station_id']}-{item['item']}-{number:03d}",
        "item": item["item"],
        "quantity": round(quantity, 2),
        "order_day": day_index,
        "arrival_day": day_index + item["lead_time"],
        "status": "Planned",
        "delay_days": 0,
    })
    return True


def simulate_inventory_day(
    inventory: List[Dict[str, Any]],
    station,
    weather: Dict[str, Any],
    population: int,
    day_index: int = 0,
    current_date=None,
    reliability_spares_needed: List[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Main entry point for daily inventory simulation across all station catalog items.
    """
    season = weather.get("season", "SUMMER")
    station_dict = station if isinstance(station, dict) else {
        "station_name": getattr(station, "station_name", "Station"),
        "station_id": getattr(station, "station_id", "STATION"),
        "inventory_safety_buffer_percent": getattr(station, "inventory_safety_buffer_percent", 0.60),
    }

    if current_date is None:
        from datetime import datetime, timedelta
        current_date = datetime(2025, 1, 1) + timedelta(days=day_index)

    updated = []
    pending_orders = 0
    delayed_orders = 0
    shortage_items = 0
    orders_created = 0
    total_received = 0.0
    total_expired = 0.0
    etas = []

    for original in inventory:
        item = copy.deepcopy(original)
        item["batches"], expired = _discard_expired(item["batches"], day_index)
        received = _advance_orders(item, day_index, current_date, weather, season)
        demand = calculate_consumption(item, population, weather, season, reliability_spares_needed)
        item["batches"], consumed, unmet = _consume_fefo(item["batches"], demand)
        available = round(sum(b["quantity"] for b in item["batches"]), 2)

        created = _schedule_order(item, day_index, max(demand, 0.01), station_dict)
        orders_created += int(created)

        pending = [o for o in item["orders"] if o["status"] in ACTIVE_ORDER_STATUSES]
        eta = min((max(0, o["arrival_day"] - day_index) for o in pending), default=-1)

        if pending:
            pending_orders += len(pending)
            etas.append(eta)

        delayed_orders += sum(o["status"] == "Delayed" for o in pending)
        shortage_items += int(unmet > 0.0)
        total_received += received
        total_expired += expired

        item.update({
            "quantity": available,
            "daily_consumption": demand,
            "actual_consumption": consumed,
            "unmet_demand": unmet,
            "days_remaining": calculate_days_remaining(available, demand),
            "status": inventory_status(available, item["minimum"], item["critical"]),
            "shipment_status": pending[0]["status"] if pending else ("Arrived" if received > 0 else "NONE"),
            "expiry_days": min((max(0, b["expiry_day"] - day_index) for b in item["batches"]), default=0),
            "inventory_orders_pending": len(pending),
            "inventory_eta_days": eta,
            "inventory_batch_count": len(item["batches"]),
            "expired_quantity": expired,
            "received_today": received,
            "inventory_order_created_today": created,
        })
        updated.append(item)

    summary = inventory_health(updated)
    summary.update({
        "inventory_orders_pending": pending_orders,
        "inventory_eta_days": min(etas) if etas else -1,
        "inventory_batch_count": sum(len(i["batches"]) for i in updated),
        "expired_quantity": round(total_expired, 2),
        "received_today": round(total_received, 2),
        "inventory_shortage_items": shortage_items,
        "inventory_orders_created_today": orders_created,
    })

    return updated, summary


def update_inventory_state(inventory: List[Dict[str, Any]], updated_inventory: List[Dict[str, Any]]) -> None:
    """In-place update of persistent inventory list."""
    inventory.clear()
    inventory.extend(updated_inventory)
