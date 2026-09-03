package com.antarctica.digitaltwin.simulator.v4;

import java.time.LocalDate;
import java.util.*;

/** Complete, serialisable state required to deterministically continue a run. */
public class StationState {
    public String stationId;
    public LocalDate date;
    public long seed;
    public long dayIndex;
    public double fuelStockLitres, batterySocPercent = 70, batteryHealthPercent = 100;
    /** Cumulative runtime is retained for reporting; the interval counter drives maintenance. */
    public double generatorHealthPercent = 100, generatorRuntimeHours, generatorRuntimeSinceMaintenanceHours;
    public boolean generatorFailed;
    public int crew, scientists;
    public double temperatureC = -18, windSpeedKmh = 18, windDirectionDeg = 160, humidityPercent = 68,
            pressureHpa = 980, snowfallCm, snowDepthCm = 20, solarRadiationWm2, cloudCoverPercent = 45,
            visibilityM = 10_000, stormDaysRemaining;
    public String mission = "NONE";
    public int missionDaysRemaining;
    public double cargoBacklogKg;
    public int shipmentEtaDays = -1;
    public Map<String, Double> inventory = new LinkedHashMap<>();
    public Map<String, Double> equipmentHealth = new LinkedHashMap<>();
    public List<String> events = new ArrayList<>();

    public StationState() { }
    public static StationState initial(String stationId, LocalDate start, long seed, SimulationConfig c) {
        StationState s = new StationState(); s.stationId=stationId; s.date=start; s.seed=seed;
        s.fuelStockLitres=c.fuelTankLitres*.74; s.crew=c.winterPopulation; s.scientists=4;
        s.inventory.put("food_days", 240d); s.inventory.put("medical_kits", 55d); s.inventory.put("critical_spares", 35d);
        s.inventory.put("research_consumables", 180d); s.equipmentHealth.put("water_plant",98d);
        s.equipmentHealth.put("communications",97d); s.equipmentHealth.put("vehicles",95d);
        return s;
    }
}
