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
@Document(collection = "power")
public class Power {

    @Id
    private String id;

    private double currentLoadKw;
    private int batterySocPercent;
    private String generatorStatus;
    private double generatorOutputKw;
    private double solarGenerationKw;
    private String powerStatus;
    private LocalDateTime lastUpdated;
}