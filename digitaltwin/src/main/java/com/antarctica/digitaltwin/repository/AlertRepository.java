package com.antarctica.digitaltwin.repository;

import com.antarctica.digitaltwin.model.Alert;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface AlertRepository extends MongoRepository<Alert, String> {
}