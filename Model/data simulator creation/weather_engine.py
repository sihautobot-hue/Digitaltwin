"""
weather_engine.py
-----------------
Physics-based Antarctic microclimate simulation engine.
Models differentiated coastal (Bharati) and inland oasis (Maitri) climates,
Weibull wind distributions, katabatic wind surges, astronomical solar geometry,
and continuous snowpack dynamics.

Antarctica Digital Twin | SIH Project
"""

import math
import random
from typing import Dict, Any, Tuple

from station_config import get_season

# ==========================================================
# SYNOPTIC WEATHER TRANSITIONS
# ==========================================================

SUMMER_PROBABILITIES = {
    "CLEAR": 0.40,
    "NORMAL": 0.35,
    "HIGH_WIND": 0.12,
    "HEAVY_SNOW": 0.08,
    "WHITEOUT": 0.03,
    "BLIZZARD": 0.02,
}

WINTER_PROBABILITIES = {
    "CLEAR": 0.10,
    "NORMAL": 0.32,
    "HIGH_WIND": 0.22,
    "HEAVY_SNOW": 0.14,
    "WHITEOUT": 0.11,
    "BLIZZARD": 0.11,
}

# Base environmental envelopes per weather regime
WEATHER_REGIMES = {
    "CLEAR": {
        "temp_delta": (-4.0, 2.0),
        "wind_base": 12.0,
        "wind_scale": 8.0,
        "humidity_base": 60.0,
        "pressure_base": 1005.0,
        "snow_rate": (0.0, 0.0),
        "visibility_m": (8000, 15000),
        "cloud_factor": 0.95,
    },
    "NORMAL": {
        "temp_delta": (-8.0, -1.0),
        "wind_base": 22.0,
        "wind_scale": 12.0,
        "humidity_base": 72.0,
        "pressure_base": 995.0,
        "snow_rate": (0.0, 2.0),
        "visibility_m": (4000, 9000),
        "cloud_factor": 0.70,
    },
    "HIGH_WIND": {
        "temp_delta": (-12.0, -3.0),
        "wind_base": 55.0,
        "wind_scale": 20.0,
        "humidity_base": 75.0,
        "pressure_base": 982.0,
        "snow_rate": (0.0, 4.0),
        "visibility_m": (1500, 4500),
        "cloud_factor": 0.50,
    },
    "HEAVY_SNOW": {
        "temp_delta": (-16.0, -6.0),
        "wind_base": 38.0,
        "wind_scale": 14.0,
        "humidity_base": 88.0,
        "pressure_base": 976.0,
        "snow_rate": (8.0, 22.0),
        "visibility_m": (400, 1800),
        "cloud_factor": 0.25,
    },
    "WHITEOUT": {
        "temp_delta": (-22.0, -10.0),
        "wind_base": 58.0,
        "wind_scale": 22.0,
        "humidity_base": 92.0,
        "pressure_base": 970.0,
        "snow_rate": (8.0, 20.0),
        "visibility_m": (20, 150),
        "cloud_factor": 0.08,
    },
    "BLIZZARD": {
        "temp_delta": (-28.0, -14.0),
        "wind_base": 90.0,
        "wind_scale": 32.0,
        "humidity_base": 95.0,
        "pressure_base": 962.0,
        "snow_rate": (18.0, 45.0),
        "visibility_m": (10, 80),
        "cloud_factor": 0.03,
    },
}


def _weibull_wind(base_speed: float, scale: float, katabatic_bonus: float = 0.0) -> float:
    """Generate physically realistic wind speed using Weibull distribution."""
    # Shape parameter k ~ 2.0 (standard wind profile), scale parameter c ~ base_speed
    u = random.random()
    wind = (base_speed + katabatic_bonus) * ((-math.log(max(1e-6, 1.0 - u))) ** (1.0 / 2.0))
    # Add gustiness
    return round(max(3.0, wind), 2)


def calculate_severity(temperature: float, wind: float, snowfall: float, visibility: float) -> float:
    """Compute Antarctic Weather Severity Index (0 to 100)."""
    wind_score = min(100.0, wind * 0.9)
    snow_score = min(100.0, snowfall * 3.5)
    visibility_score = max(0.0, min(100.0, 100.0 - (visibility / 100.0)))
    temp_score = max(0.0, min(100.0, (abs(temperature) - 5.0) * 2.2))
    severity = (
        wind_score * 0.35 +
        snow_score * 0.30 +
        visibility_score * 0.20 +
        temp_score * 0.15
    )
    return round(max(0.0, min(100.0, severity)), 2)


def astronomical_solar(date, latitude_deg: float, cloud_factor: float = 1.0, snow_depth_cm: float = 0.0) -> Tuple[float, float, float]:
    """
    Calculate top-of-atmosphere and surface direct/diffuse solar irradiance
    using spherical solar geometry.
    """
    lat_rad = math.radians(latitude_deg)
    yday = date.timetuple().tm_yday if hasattr(date, "timetuple") else 1
    # Solar declination angle
    declination = math.radians(23.44) * math.sin(2.0 * math.pi * (yday - 81) / 365.25)
    cos_hour_angle = -math.tan(lat_rad) * math.tan(declination)

    if cos_hour_angle >= 1.0:
        # Polar night (continuous darkness)
        daylight_hours = 0.0
        elevation = 0.0
    elif cos_hour_angle <= -1.0:
        # Polar day (continuous 24h daylight / midnight sun)
        daylight_hours = 24.0
        sin_elev = math.sin(lat_rad) * math.sin(declination) + math.cos(lat_rad) * math.cos(declination)
        elevation = math.degrees(math.asin(max(0.0, sin_elev)))
    else:
        daylight_hours = 2.0 * math.degrees(math.acos(cos_hour_angle)) / 15.0
        sin_elev = math.sin(lat_rad) * math.sin(declination) + math.cos(lat_rad) * math.cos(declination)
        elevation = math.degrees(math.asin(max(0.0, sin_elev)))

    if daylight_hours <= 0.0 or elevation <= 0.0:
        return 0.0, 0.0, 0.0

    # Solar constant: 1361 W/m^2
    solar_constant = 1361.0
    # Atmospheric air mass optical attenuation
    air_mass = 1.0 / max(0.1, math.sin(math.radians(elevation)))
    atm_transmittance = 0.70 ** (air_mass ** 0.678)
    # Albedo reflection enhancement from surrounding snow
    albedo_gain = 1.0 + min(0.20, snow_depth_cm / 200.0)

    daily_avg_irradiance = (
        solar_constant *
        math.sin(math.radians(elevation)) *
        (daylight_hours / 24.0) *
        atm_transmittance *
        cloud_factor *
        albedo_gain
    )
    return (
        round(max(0.0, daily_avg_irradiance), 2),
        round(daylight_hours, 2),
        round(elevation, 2),
    )


def generate_weather_stateful(date, previous_weather=None, station=None) -> Dict[str, Any]:
    """
    Advance multi-day weather dynamics conditioned on station microclimate.

    Parameters
    ----------
    date : datetime
    previous_weather : Dict of previous day's internal state or None.
    station : StationConfig object (provides climate_type and latitude).
    """
    season = get_season(date)
    is_summer = (season == "SUMMER")
    climate_type = getattr(station, "climate_type", "MARITIME_COASTAL") if station else "MARITIME_COASTAL"
    latitude = getattr(station, "latitude", -70.0) if station else -70.0

    previous = previous_weather if isinstance(previous_weather, dict) else None

    # Determine baseline seasonal temperatures per microclimate
    if climate_type == "INLAND_OASIS":
        # Maitri: Schirmacher Oasis - Katabatic winds, colder winter extremes
        base_temp = -2.0 if is_summer else -26.0
        katabatic_strength = 20.0 if not is_summer else 8.0
        humidity_offset = -12.0
    else:
        # Bharati: Larsemann Hills - Maritime dampening, higher humidity & snowfall
        base_temp = 1.5 if is_summer else -18.5
        katabatic_strength = 0.0
        humidity_offset = 6.0

    if previous is None:
        table = SUMMER_PROBABILITIES if is_summer else WINTER_PROBABILITIES
        weather_type = random.choices(list(table.keys()), weights=list(table.values()), k=1)[0]
        age = 1
        duration = random.randint(2, 5) if weather_type not in {"BLIZZARD", "WHITEOUT"} else random.randint(2, 7)
        regime = WEATHER_REGIMES[weather_type]

        temp = round(base_temp + random.uniform(*regime["temp_delta"]), 2)
        wind = _weibull_wind(regime["wind_base"], regime["wind_scale"], katabatic_strength)
        humidity = round(max(35.0, min(100.0, regime["humidity_base"] + humidity_offset + random.gauss(0, 4))), 2)
        pressure = round(regime["pressure_base"] + random.gauss(0, 6), 2)
        visibility = round(random.uniform(*regime["visibility_m"]), 2)
        snow_depth = 15.0 if climate_type == "MARITIME_COASTAL" else 5.0
    else:
        age = previous.get("age", 1) + 1
        duration = previous.get("duration", 3)
        weather_type = previous.get("weather_type", "NORMAL")
        snow_depth = previous.get("snow_depth_cm", 10.0)

        # Transition to next synoptic system if current duration elapsed
        if age >= duration:
            transitions = {
                "CLEAR": ["CLEAR", "NORMAL", "HIGH_WIND"],
                "NORMAL": ["NORMAL", "CLEAR", "HEAVY_SNOW", "HIGH_WIND"],
                "HIGH_WIND": ["HIGH_WIND", "NORMAL", "HEAVY_SNOW", "WHITEOUT"],
                "HEAVY_SNOW": ["HEAVY_SNOW", "HIGH_WIND", "WHITEOUT", "NORMAL"],
                "WHITEOUT": ["WHITEOUT", "HEAVY_SNOW", "BLIZZARD", "HIGH_WIND"],
                "BLIZZARD": ["BLIZZARD", "WHITEOUT", "HEAVY_SNOW"],
            }
            candidates = [c for c in transitions[weather_type] if c != weather_type]
            table = SUMMER_PROBABILITIES if is_summer else WINTER_PROBABILITIES
            weather_type = random.choices(candidates, weights=[table[c] for c in candidates], k=1)[0]
            age = 1
            duration = random.randint(2, 5) if weather_type not in {"BLIZZARD", "WHITEOUT"} else random.randint(2, 8)

        regime = WEATHER_REGIMES[weather_type]
        target_temp = base_temp + random.uniform(*regime["temp_delta"])

        # Autoregressive smoothing (AR-1) to avoid unnatural jumps
        prev_temp = previous.get("temperature_c", base_temp)
        temp = round(0.65 * prev_temp + 0.35 * target_temp + random.gauss(0, 0.8), 2)
        wind = _weibull_wind(regime["wind_base"], regime["wind_scale"], katabatic_strength)

        prev_hum = previous.get("humidity_percent", 70.0)
        target_hum = max(35.0, min(100.0, regime["humidity_base"] + humidity_offset))
        humidity = round(max(30.0, min(100.0, 0.60 * prev_hum + 0.40 * target_hum + random.gauss(0, 2.0))), 2)

        prev_pres = previous.get("pressure_hpa", 995.0)
        target_pres = regime["pressure_base"]
        pressure = round(0.55 * prev_pres + 0.45 * target_pres + random.gauss(0, 2.5), 2)

        visibility = round(random.uniform(*regime["visibility_m"]), 2)

    # Precipitation and snow accumulation / melting
    regime = WEATHER_REGIMES[weather_type]
    snowfall = round(random.uniform(*regime["snow_rate"]) * (1.25 if climate_type == "MARITIME_COASTAL" else 0.70), 2)

    # Snow ablation: sublimation + summer thermal melting
    melt_rate = max(0.0, (temp - 0.0) * 0.8) if is_summer else 0.05
    wind_ablation = wind * 0.005
    snow_depth = round(max(0.0, snow_depth + snowfall - melt_rate - wind_ablation), 2)

    cloud_factor = regime["cloud_factor"]
    solar_rad, daylight_hours, solar_elevation = astronomical_solar(
        date, latitude, cloud_factor, snow_depth
    )

    gust = round(wind + random.uniform(8.0, 32.0), 2)
    severity = calculate_severity(temp, wind, snowfall, visibility)

    internal_state = {
        "temperature_c": temp,
        "wind_speed_kmh": wind,
        "humidity_percent": humidity,
        "pressure_hpa": pressure,
        "visibility_m": visibility,
        "weather_type": weather_type,
        "age": age,
        "duration": duration,
        "snow_depth_cm": snow_depth,
    }

    return {
        "season": season,
        "weather_type": weather_type,
        "temperature_c": temp,
        "wind_speed_kmh": wind,
        "wind_gust_kmh": gust,
        "humidity_percent": humidity,
        "pressure_hpa": pressure,
        "snowfall_cm": snowfall,
        "snow_depth_cm": snow_depth,
        "visibility_m": visibility,
        "solar_radiation_wm2": solar_rad,
        "solar_daylight_hours": daylight_hours,
        "solar_elevation_deg": solar_elevation,
        "weather_severity": severity,
        "_weather_state": internal_state,
    }


def generate_weather(date, previous_weather=None) -> Dict[str, Any]:
    """Compatibility wrapper for original stateless API."""
    res = generate_weather_stateful(date, previous_weather)
    res.pop("_weather_state", None)
    return res
