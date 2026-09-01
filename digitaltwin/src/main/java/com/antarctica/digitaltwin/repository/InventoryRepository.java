package com.antarctica.digitaltwin.repository;

import com.antarctica.digitaltwin.model.Inventory;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.Optional;

public interface InventoryRepository extends MongoRepository<Inventory, String> {
    Optional<Inventory> findByItemIgnoreCase(String item);
}