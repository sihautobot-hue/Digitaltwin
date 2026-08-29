package com.antarctica.digitaltwin.repository;

import com.antarctica.digitaltwin.model.Fuel;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface FuelRepository extends MongoRepository<Fuel, String> {
}