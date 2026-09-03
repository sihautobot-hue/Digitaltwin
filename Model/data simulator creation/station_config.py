"""
station_config.py
-----------------
Static configuration for Indian Antarctic Research Stations (Maitri & Bharati).
Contains physical specifications, microgrid parameters, thermal envelopes,
and geographical climate profiles.

Antarctica Digital Twin | SIH Project
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict

# ==========================================================
# SIMULATION TIMELINE
# ==========================================================

SIMULATION_START = "2024-12-24"
SIMULATION_DAYS = 7300
RANDOM_SEED = 216

# ==========================================================
# SEASONS & LOGISTICS WINDOWS
# ==========================================================

SUMMER_MONTHS = [11, 12, 1, 2]
WINTER_MONTHS = [3, 4, 5, 6, 7, 8, 9, 10]

# Antarctic sea-ice navigable window for resupply vessels (Nov 1 to March 31)
SHIPPING_WINDOW_MONTHS = [11, 12, 1, 2, 3]
SEA_ICE_LOCKOUT_MONTHS = [4, 5, 6, 7, 8, 9, 10]


def get_season(date) -> str:
    """Return 'SUMMER' or 'WINTER' based on Antarctic calendar month."""
    month = date.month if hasattr(date, "month") else int(date)
    return "SUMMER" if month in SUMMER_MONTHS else "WINTER"


def is_shipping_season(date) -> bool:
    """Return True if maritime navigation through Southern Ocean sea ice is possible."""
    month = date.month if hasattr(date, "month") else int(date)
    return month in SHIPPING_WINDOW_MONTHS


# ==========================================================
# Station Configuration Dataclass
# ==========================================================

@dataclass
class StationConfig:
    station_id: str
    station_name: str
    latitude: float
    longitude: float
    elevation_m: int
    max_population: int
    fuel_capacity_liters: int
    initial_fuel_liters: int
    daily_fuel_warning: int
    generator_capacity_kw: int
    battery_capacity_kwh: int
    initial_battery_soc: int
    solar_capacity_kw: int
    water_storage_liters: int
    daily_water_capacity: int
    internet_type: str
    inventory_categories: list

    # Climate Classification
    # MARITIME_COASTAL: Larsemann Hills (Bharati) - high humidity, coastal blizzards, ocean dampening
    # INLAND_OASIS: Schirmacher Oasis (Maitri) - katabatic gravity winds, low humidity, extreme cold
    climate_type: str = "MARITIME_COASTAL"

    # Microgrid Modular Genset Specs
    # List of individual generator unit capacities in kW (e.g. [140, 140, 140] for 420 kW)
    genset_units: List[int] = field(default_factory=lambda: [140, 140, 140])
    generator_min_load_percent: float = 30.0
    generator_min_runtime_hours: int = 4
    generator_startup_fuel_liters: float = 1.5

    # Battery Chemistry & Thermal Dynamics
    battery_min_soc_percent: float = 20.0
    battery_generator_target_soc_percent: float = 75.0
    battery_optimal_temp_c: float = 20.0
    battery_temp_derate_per_c: float = 0.005  # -0.5% capacity per deg C below 15C
    generator_charge_response_hours: int = 4

    # Building Thermal Envelope & Combined Heat and Power (CHP)
    # UA is overall heat loss coefficient (kW/deg C difference from 18 deg C indoor setpoint)
    building_thermal_conductance_kw_per_c: float = 1.3
    wind_infiltration_factor: float = 0.015  # kW heat loss per km/h of wind
    chp_heat_recovery_efficiency: float = 0.45  # 45% of generator waste heat recovered for heating/snowmelt

    # Logistics and Risk Thresholds
    inventory_safety_buffer_percent: float = 0.60
    risk_weights: dict = field(default_factory=lambda: {
        "power": 0.25, "fuel": 0.20, "inventory": 0.15,
        "weather": 0.10, "water": 0.10, "connectivity": 0.10,
        "occupancy": 0.10,
    })
    risk_level_thresholds: dict = field(default_factory=lambda: {
        "medium": 30, "high": 60, "critical": 80,
    })


# ==========================================================
# MAITRI (Established 1989, Schirmacher Oasis)
# Inland Rocky Oasis, Katabatic Wind Exposure, Extreme Winter Cold
# ==========================================================

MAITRI = StationConfig(
    station_id="MAITRI",
    station_name="Maitri",
    latitude=-70.76,
    longitude=11.73,
    elevation_m=117,
    max_population=47,
    fuel_capacity_liters=300000,
    initial_fuel_liters=270000,
    daily_fuel_warning=45000,
    generator_capacity_kw=350,
    battery_capacity_kwh=900,
    initial_battery_soc=95,
    solar_capacity_kw=25,
    water_storage_liters=120000,
    daily_water_capacity=5000,
    internet_type="VSAT",
    climate_type="INLAND_OASIS",
    genset_units=[115, 115, 120],  # 3 x ~115 kW gensets = 350 kW total
    building_thermal_conductance_kw_per_c=1.65,  # Older insulated structure
    wind_infiltration_factor=0.018,
    inventory_categories=[
        "Food",
        "Medical",
        "Scientific",
        "Mechanical",
        "Electrical",
        "Emergency"
    ]
)

# ==========================================================
# BHARATI (Commissioned 2012, Larsemann Hills)
# Modern Energy-Efficient Modular Station, Maritime Coastal Climate
# ==========================================================

BHARATI = StationConfig(
    station_id="BHARATI",
    station_name="Bharati",
    latitude=-69.40,
    longitude=76.19,
    elevation_m=35,
    max_population=47,
    fuel_capacity_liters=320000,
    initial_fuel_liters=285000,
    daily_fuel_warning=50000,
    generator_capacity_kw=420,
    battery_capacity_kwh=1100,
    initial_battery_soc=96,
    solar_capacity_kw=40,
    water_storage_liters=150000,
    daily_water_capacity=7000,
    internet_type="VSAT",
    climate_type="MARITIME_COASTAL",
    genset_units=[140, 140, 140],  # 3 x 140 kW gensets = 420 kW total
    building_thermal_conductance_kw_per_c=1.15,  # Highly insulated modern modular envelope
    wind_infiltration_factor=0.012,
    inventory_categories=[
        "Food",
        "Medical",
        "Scientific",
        "Mechanical",
        "Electrical",
        "Emergency"
    ]
)

# ==========================================================
# STATION REGISTRY
# ==========================================================

STATIONS = [
    MAITRI,
    BHARATI
]
