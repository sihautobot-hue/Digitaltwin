package com.antarctica.digitaltwin.dto;

import jakarta.validation.constraints.PositiveOrZero;
import lombok.Data;

@Data
public class FuelUpdateRequest {

    @PositiveOrZero(message = "Fuel stock cannot be negative")
    private double fuelStockLiters;

    @PositiveOrZero(message = "Daily consumption cannot be negative")
    private double dailyConsumptionLiters;

    @PositiveOrZero(message = "Generator usage hours cannot be negative")
    private double generatorUsageHours;
}