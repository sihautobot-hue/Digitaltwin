package com.antarctica.digitaltwin.repository;

import com.antarctica.digitaltwin.model.Prediction;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface PredictionRepository extends MongoRepository<Prediction, String> {
}