package com.antarctica.digitaltwin.service;

import com.antarctica.digitaltwin.model.Prediction;
import com.antarctica.digitaltwin.repository.PredictionRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class PredictionService {

    @Autowired
    private PredictionRepository predictionRepository;

    // This is where Sunny and Krish's AI model output will eventually land,
    // via REST call or JSON file read — see notes below.
    public Prediction getPrediction() {
        List<Prediction> all = predictionRepository.findAll();
        return all.isEmpty() ? getDummyPrediction() : all.get(0);
    }

    private Prediction getDummyPrediction() {
        Prediction prediction = new Prediction();
        prediction.setInventory(new Prediction.InventoryPrediction(12, 300, "MEDIUM"));
        prediction.setFuel(new Prediction.FuelPrediction(18, "HIGH", 5000, "Refuel within 5 days"));
        prediction.setPower(new Prediction.PowerPrediction("LOW", 450));
        return prediction;
    }
}