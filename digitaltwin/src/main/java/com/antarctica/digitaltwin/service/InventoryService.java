package com.antarctica.digitaltwin.service;

import com.antarctica.digitaltwin.dto.InventoryUpdateRequest;
import com.antarctica.digitaltwin.exception.ResourceNotFoundException;
import com.antarctica.digitaltwin.model.Inventory;
import com.antarctica.digitaltwin.repository.InventoryRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class InventoryService {

    @Autowired
    private InventoryRepository inventoryRepository;

    public List<Inventory> getAllInventory() {
        List<Inventory> data = inventoryRepository.findAll();
        return data.isEmpty() ? getDummyInventory() : data;
    }

    public Inventory getInventoryByItem(String item) {
        return inventoryRepository.findByItemIgnoreCase(item)
                .or(() -> getDummyInventory().stream()
                        .filter(inv -> inv.getItem().equalsIgnoreCase(item))
                        .findFirst())
                .orElseThrow(() -> new ResourceNotFoundException("Inventory item not found"));
    }

    public Inventory updateInventory(InventoryUpdateRequest request) {
        Inventory inventory = inventoryRepository.findByItemIgnoreCase(request.getItem())
                .orElseThrow(() -> new ResourceNotFoundException("Inventory item not found"));

        inventory.setQuantity(request.getQuantity());
        inventory.setLastUpdated(LocalDateTime.now());

        // Simple status recalculation based on minimum stock
        inventory.setStatus(inventory.getQuantity() <= inventory.getMinimumStock() ? "WARNING" : "NORMAL");

        return inventoryRepository.save(inventory);
    }

    // Fallback data — used only when MongoDB has no records yet
    private List<Inventory> getDummyInventory() {
        return List.of(
                new Inventory(null, "Rice", "Food", 250, "kg", 12, 100, "NORMAL", LocalDateTime.now()),
                new Inventory(null, "Wheat", "Food", 180, "kg", 8, 80, "NORMAL", LocalDateTime.now()),
                new Inventory(null, "Dal", "Food", 90, "kg", 5, 50, "WARNING", LocalDateTime.now()),
                new Inventory(null, "Medical Kit", "Medical", 15, "units", 1, 10, "NORMAL", LocalDateTime.now()),
                new Inventory(null, "Drinking Water", "Supplies", 500, "liters", 40, 200, "NORMAL",
                        LocalDateTime.now()));
    }
}