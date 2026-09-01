package com.antarctica.digitaltwin.controller;

import com.antarctica.digitaltwin.model.Prediction;
import com.antarctica.digitaltwin.service.PredictionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/prediction")
public class PredictionController {

    @Autowired
    private PredictionService predictionService;

    @GetMapping
    public Prediction getPrediction() {
        return predictionService.getPrediction();
    }
}