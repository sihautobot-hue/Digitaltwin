package com.antarctica.digitaltwin.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "predictions")
public class Prediction {

    @Id
    private String id;

    private InventoryPrediction inventory;
    private FuelPrediction fuel;
    private PowerPrediction power;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class InventoryPrediction {
        private int daysLeft;
        private int reorderQuantity;
        private String risk;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class FuelPrediction {
        private int fuelDaysLeft;
        private String fuelRisk;
        private int recommendedShipment;
        private String recommendation;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class PowerPrediction {
        private String powerRisk;
        private int predictedLoad;
    }
}