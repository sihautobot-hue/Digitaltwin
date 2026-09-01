package com.antarctica.digitaltwin.controller;

import com.antarctica.digitaltwin.dto.FuelUpdateRequest;
import com.antarctica.digitaltwin.model.Fuel;
import com.antarctica.digitaltwin.service.FuelService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/fuel")
public class FuelController {

    @Autowired
    private FuelService fuelService;

    @GetMapping
    public Fuel getFuel() {
        return fuelService.getFuel();
    }

    @PostMapping("/update")
    public Fuel updateFuel(@Valid @RequestBody FuelUpdateRequest request) {
        return fuelService.updateFuel(request);
    }
}