package com.antarctica.digitaltwin.repository;

import com.antarctica.digitaltwin.model.Weather;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface WeatherRepository extends MongoRepository<Weather, String> {
}