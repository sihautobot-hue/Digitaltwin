package com.antarctica.digitaltwin.repository;

import com.antarctica.digitaltwin.model.SyncStatus;
import org.springframework.data.mongodb.repository.MongoRepository;

public interface SyncRepository extends MongoRepository<SyncStatus, String> {
}