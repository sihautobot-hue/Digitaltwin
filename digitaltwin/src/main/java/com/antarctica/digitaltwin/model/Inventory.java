package com.antarctica.digitaltwin.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "inventory")
public class Inventory {

    @Id
    private String id;

    private String item;
    private String category;
    private int quantity;
    private String unit;
    private int dailyConsumption;
    private int minimumStock;
    private String status;
    private LocalDateTime lastUpdated;
}