package com.antarctica.digitaltwin.repository;

import com.antarctica.digitaltwin.model.Power;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface PowerRepository extends MongoRepository<Power, String> {
}