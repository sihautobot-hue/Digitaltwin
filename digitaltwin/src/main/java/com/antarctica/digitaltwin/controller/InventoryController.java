package com.antarctica.digitaltwin.controller;

import com.antarctica.digitaltwin.dto.InventoryUpdateRequest;
import com.antarctica.digitaltwin.model.Inventory;
import com.antarctica.digitaltwin.service.InventoryService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/inventory")
public class InventoryController {

    @Autowired
    private InventoryService inventoryService;

    @GetMapping
    public List<Inventory> getAllInventory() {
        return inventoryService.getAllInventory();
    }

    @GetMapping("/{item}")
    public Inventory getInventoryByItem(@PathVariable String item) {
        return inventoryService.getInventoryByItem(item);
    }

    @PostMapping("/update")
    public Inventory updateInventory(@Valid @RequestBody InventoryUpdateRequest request) {
        return inventoryService.updateInventory(request);
    }
}