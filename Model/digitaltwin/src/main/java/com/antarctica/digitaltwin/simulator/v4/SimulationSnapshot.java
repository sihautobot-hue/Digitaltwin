package com.antarctica.digitaltwin.simulator.v4;

import java.time.LocalDate;
import java.util.List;

/** A daily operational snapshot. Values are outcomes of state transitions only. */
public record SimulationSnapshot(LocalDate date, String stationId, double temperatureC, double windSpeedKmh,
    double solarGenerationKw, double windGenerationKw, double totalLoadKw, double generatorOutputKw,
    double generatorRuntimeHours, double fuelStockLitres, double fuelConsumedLitres, double batterySocPercent,
    int totalPopulation, String mission, double foodDays, double medicalKits, double criticalSpares,
    double generatorHealthPercent, double equipmentHealthPercent, boolean storm, boolean generatorFailed,
    List<String> events) { }
