package com.antarctica.digitaltwin.controller;

import com.antarctica.digitaltwin.model.Alert;
import com.antarctica.digitaltwin.service.AlertService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/alerts")
public class AlertController {

    @Autowired
    private AlertService alertService;

    @GetMapping
    public List<Alert> getAlerts() {
        return alertService.getAlerts();
    }
}