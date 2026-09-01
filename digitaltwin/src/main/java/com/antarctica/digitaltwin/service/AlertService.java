package com.antarctica.digitaltwin.service;

import com.antarctica.digitaltwin.model.Alert;
import com.antarctica.digitaltwin.repository.AlertRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class AlertService {

    @Autowired
    private AlertRepository alertRepository;

    public List<Alert> getAlerts() {
        List<Alert> all = alertRepository.findAll();
        return all.isEmpty() ? getDummyAlerts() : all;
    }

    private List<Alert> getDummyAlerts() {
        return List.of(
                new Alert("A001", "FUEL", "Fuel stock is below expected level", "CRITICAL", LocalDateTime.now(),
                        "ACTIVE"),
                new Alert("A002", "WEATHER", "Strong winds expected", "WARNING", LocalDateTime.now(), "ACTIVE"),
                new Alert("A003", "POWER", "Battery level dropping faster than usual", "WARNING", LocalDateTime.now(),
                        "ACTIVE"));
    }
}