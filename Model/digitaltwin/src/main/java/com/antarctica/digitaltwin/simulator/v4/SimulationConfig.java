package com.antarctica.digitaltwin.simulator.v4;

/** Physical and operational parameters for a station instance. */
public final class SimulationConfig {
    public final double fuelTankLitres = 180_000;
    public final double batteryCapacityKwh = 600;
    public final double solarCapacityKw = 180;
    public final double windCapacityKw = 70;
    public final double generatorCapacityKw = 420;
    public final int generatorCount = 3;
    public final int winterPopulation = 24;
    public final int summerPopulation = 68;
    public final int maintenanceIntervalRuntimeHours = 500;
}
