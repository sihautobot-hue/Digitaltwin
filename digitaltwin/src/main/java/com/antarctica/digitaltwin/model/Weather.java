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
@Document(collection = "weather")
public class Weather {

    @Id
    private String id;

    private double temperatureCelsius;
    private double windSpeedKmh;
    private int humidityPercent;
    private double visibilityKm;
    private double pressureHpa;
    private String weatherCondition;
    private String weatherStatus;
    private LocalDateTime lastUpdated;
}