"""
generate.py
-----------
Antarctica Digital Twin Master Simulation Pipeline (Version 2).

Provides:
1. High-speed 20-year (7,300 days) historical dataset generation for ML training.
2. Stateful `AntarcticDigitalTwin` class for live step-by-step Digital Twin operations
   (5 minutes = 1 simulated day).

Antarctica Digital Twin | SIH Project
"""

import os
import random
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

# ==========================================================
# IMPORT CONFIGURATION & ENGINES
# ==========================================================

from station_config import (
    STATIONS,
    MAITRI,
    BHARATI,
    SIMULATION_START,
    SIMULATION_DAYS,
    RANDOM_SEED,
)

from population_engine import (
    initialize_population,
    simulate_population,
)

from weather_engine import (
    generate_weather_stateful,
)

from power_engine import (
    simulate_power,
)

from fuel_engine import (
    simulate_fuel,
    initialize_fuel_logistics,
    available_fuel_energy_kwh,
)

from water_engine import (
    simulate_water,
)

from inventory_engine import (
    initialize_inventory,
    simulate_inventory_day,
    update_inventory_state,
)

from connectivity_engine import (
    simulate_connectivity,
    initialize_connectivity,
)

from reliability_engine import (
    initialize_reliability,
    advance_reliability,
)

from risk_engine import (
    evaluate_station,
)


class AntarcticDigitalTwin:
    """
    Stateful Digital Twin Simulation Engine for an Antarctic Research Station.
    Maintains continuous physics, asset health, and multi-system coupling.
    """

    def __init__(self, station=BHARATI, start_date: str = SIMULATION_START, seed: int = RANDOM_SEED):
        random.seed(seed)
        self.station = station
        self.current_date = datetime.strptime(start_date, "%Y-%m-%d")
        self.day_index = 0

        # Persistent state containers
        self.population_state = initialize_population(station)
        self.battery_soc = station.initial_battery_soc
        self.fuel_liters = station.initial_fuel_liters
        self.fuel_logistics = initialize_fuel_logistics(station)
        self.water_liters = station.water_storage_liters
        self.connectivity_state = initialize_connectivity()
        self.reliability_state = initialize_reliability()
        self.inventory_state = initialize_inventory({
            "station_name": station.station_name,
            "station_id": station.station_id,
        })
        self.weather_state = None
        self.risk_state = {"offline_days": 0}

        # Cross-engine telemetry memory
        self.last_chp_heat_kw = 0.0
        self.last_failed_assets = []
        self.last_spares_needed = []

    def step(self) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Advance station physical reality by exactly 1 day.
        Returns (station_record_dict, list_of_inventory_item_dicts).
        """
        # 1. Weather
        weather = generate_weather_stateful(
            self.current_date,
            self.weather_state,
            self.station,
        )
        self.weather_state = weather.pop("_weather_state", None)

        # 2. Population
        population = simulate_population(
            self.population_state,
            self.current_date,
            self.station,
            weather,
        )
        total_pop = population["total_population"]

        # 3. Microgrid Power
        power = simulate_power(
            population=total_pop,
            season=weather["season"],
            temperature=weather["temperature_c"],
            solar_radiation=weather["solar_radiation_wm2"],
            previous_battery=self.battery_soc,
            battery_capacity=self.station.battery_capacity_kwh,
            generator_capacity=self.station.generator_capacity_kw,
            solar_capacity=self.station.solar_capacity_kw,
            battery_min_soc_percent=self.station.battery_min_soc_percent,
            battery_generator_target_soc_percent=self.station.battery_generator_target_soc_percent,
            generator_charge_response_hours=self.station.generator_charge_response_hours,
            available_generator_energy_kwh=available_fuel_energy_kwh(self.fuel_liters),
            station=self.station,
            wind_speed_kmh=weather.get("wind_speed_kmh", 25.0),
            failed_assets=self.last_failed_assets,
            chp_recovered_kw=self.last_chp_heat_kw,
        )
        self.battery_soc = power["battery_soc_percent"]

        # 4. Fuel & Maritime Logistics
        fuel = simulate_fuel(
            previous_stock=self.fuel_liters,
            tank_capacity=self.station.fuel_capacity_liters,
            generator_output_kw=power["generator_output_kw"],
            generator_runtime_hours=power["generator_runtime_hours"],
            generator_capacity_kw=self.station.generator_capacity_kw,
            weather_severity=weather["weather_severity"],
            logistics_state=self.fuel_logistics,
            day_index=self.day_index,
            weather=weather,
            station=self.station,
            active_generators=power["active_generators"],
            current_date=self.current_date,
        )
        self.fuel_liters = fuel["fuel_stock_liters"]
        self.last_chp_heat_kw = fuel.get("chp_waste_heat_kw", 0.0)

        # 5. Life Support Water
        water_plant_stat = self.reliability_state.get("water_plant", {}).get("status", "OPERATIONAL")
        water = simulate_water(
            previous_storage=self.water_liters,
            tank_capacity=self.station.water_storage_liters,
            population=total_pop,
            weather=weather,
            daily_capacity=self.station.daily_water_capacity,
            power_available=not power["power_shortage_event"],
            power_shortage_event=power["power_shortage_event"],
            chp_waste_heat_kw=self.last_chp_heat_kw,
            water_plant_status=water_plant_stat,
        )
        self.water_liters = water["water_storage_liters"]

        # 6. Satellite Connectivity
        vsat_stat = self.reliability_state.get("communication_vsat", {}).get("status", "OPERATIONAL")
        connectivity = simulate_connectivity(
            weather=weather,
            state=self.connectivity_state,
            vsat_hardware_status=vsat_stat,
        )

        # 7. Asset Reliability & Degradation
        # Map on-hand quantities of inventory for spare-parts check
        inv_map = {item["item"]: item["quantity"] for item in self.inventory_state}
        reliability = advance_reliability(
            state=self.reliability_state,
            power_telemetry=power,
            water_telemetry=water,
            connectivity_telemetry=connectivity,
            inventory_available_map=inv_map,
        )
        self.last_failed_assets = reliability.get("failed_critical_assets", [])
        self.last_spares_needed = reliability.get("spares_consumed_today", [])

        # 8. Supply Chain & FEFO Inventory
        updated_inv, inv_summary = simulate_inventory_day(
            inventory=self.inventory_state,
            station=self.station,
            weather=weather,
            population=total_pop,
            day_index=self.day_index,
            current_date=self.current_date,
            reliability_spares_needed=self.last_spares_needed,
        )
        update_inventory_state(self.inventory_state, updated_inv)

        # 9. Multi-System Operational Risk
        risk = evaluate_station(
            weather=weather,
            power=power,
            fuel=fuel,
            water=water,
            inventory=inv_summary,
            connectivity=connectivity,
            station=self.station,
            population=population,
            risk_state=self.risk_state,
            reliability=reliability,
        )

        # 10. Assemble Master Station Record
        station_record = {
            "date": self.current_date,
            "station_id": self.station.station_id,
            "station_name": self.station.station_name,
            **population,
            **weather,
            **power,
            **fuel,
            **water,
            **inv_summary,
            **connectivity,
            **risk,
        }

        # Item-level records
        item_records = []
        for item in updated_inv:
            item_records.append({
                "date": self.current_date,
                "station_id": self.station.station_id,
                "station_name": self.station.station_name,
                **item,
            })

        # Advance calendar
        self.current_date += timedelta(days=1)
        self.day_index += 1

        return station_record, item_records


def run_full_simulation(days: int = SIMULATION_DAYS, seed: int = RANDOM_SEED) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run the complete multi-year historical dataset generation pipeline.
    """
    print("=" * 65)
    print(f"  ANTARCTICA DIGITAL TWIN SIMULATOR V2 — BATCH GENERATION")
    print(f"  Simulating {days:,} days ({days/365.25:.1f} years) for {len(STATIONS)} stations")
    print(f"  Start Date: {SIMULATION_START}")
    print("=" * 65)

    start_time = time.time()
    random.seed(seed)

    all_station_records = []
    all_inventory_records = []

    for station in STATIONS:
        print(f"\n[Simulator] Initializing Digital Twin for {station.station_name} ({station.station_id})...")
        twin = AntarcticDigitalTwin(station=station, start_date=SIMULATION_START, seed=seed)

        for d in range(days):
            if (d + 1) % 500 == 0 or d == days - 1:
                print(f"  -> Simulating {station.station_name}: Day {d+1:,}/{days:,} ({twin.current_date.strftime('%Y-%m-%d')})", end="\r")

            st_rec, it_recs = twin.step()
            all_station_records.append(st_rec)
            all_inventory_records.extend(it_recs)

        print(f"\n  -> Completed {days:,} days for {station.station_name}.")

    print("\n[Simulator] Compiling output DataFrames...")
    station_df = pd.DataFrame(all_station_records)
    inventory_df = pd.DataFrame(all_inventory_records)

    # Sort
    station_df = station_df.sort_values(["date", "station_name"]).reset_index(drop=True)
    inventory_df = inventory_df.sort_values(["date", "station_name", "category", "item"]).reset_index(drop=True)

    elapsed = time.time() - start_time
    print(f"[Simulator] Generated {len(station_df):,} station records and {len(inventory_df):,} inventory records in {elapsed:.2f} seconds.")

    # Save to local directory and project data directory
    local_station_path = "station_summary.csv"
    local_inventory_path = "inventory_items.csv"

    project_data_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data"))
    os.makedirs(project_data_dir, exist_ok=True)
    project_station_path = os.path.join(project_data_dir, "station_summary.csv")
    project_inventory_path = os.path.join(project_data_dir, "inventory_items.csv")

    print(f"[Simulator] Saving dataset -> {local_station_path} & {project_station_path}")
    station_df.to_csv(local_station_path, index=False)
    station_df.to_csv(project_station_path, index=False)

    print(f"[Simulator] Saving dataset -> {local_inventory_path} & {project_inventory_path}")
    inventory_df.to_csv(local_inventory_path, index=False)
    inventory_df.to_csv(project_inventory_path, index=False)

    print("=" * 65)
    print("  SIMULATION COMPLETE — All datasets successfully written.")
    print("=" * 65)

    return station_df, inventory_df


if __name__ == "__main__":
    run_full_simulation(SIMULATION_DAYS)
