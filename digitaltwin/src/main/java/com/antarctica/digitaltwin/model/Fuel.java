package com.antarctica.digitaltwin.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.Transient;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "fuel")
public class Fuel {

    @Id
    private String id;

    private double fuelStockLiters;
    private double dailyConsumptionLiters;
    private double generatorUsageHours;
    private double minimumStockLiters;
    private String fuelStatus;
    private LocalDateTime lastUpdated;

    // Calculated on the fly, never saved to MongoDB
    @Transient
    private double daysLeft;
}