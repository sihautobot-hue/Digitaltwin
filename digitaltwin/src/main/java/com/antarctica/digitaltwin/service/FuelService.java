package com.antarctica.digitaltwin.service;

import com.antarctica.digitaltwin.dto.FuelUpdateRequest;
import com.antarctica.digitaltwin.model.Fuel;
import com.antarctica.digitaltwin.repository.FuelRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class FuelService {

    @Autowired
    private FuelRepository fuelRepository;

    public Fuel getFuel() {
        List<Fuel> all = fuelRepository.findAll();
        Fuel fuel = all.isEmpty() ? getDummyFuel() : all.get(0);
        fuel.setDaysLeft(calculateDaysLeft(fuel.getFuelStockLiters(), fuel.getDailyConsumptionLiters()));
        return fuel;
    }

    public Fuel updateFuel(FuelUpdateRequest request) {
        List<Fuel> all = fuelRepository.findAll();
        Fuel fuel = all.isEmpty() ? new Fuel() : all.get(0);

        fuel.setFuelStockLiters(request.getFuelStockLiters());
        fuel.setDailyConsumptionLiters(request.getDailyConsumptionLiters());
        fuel.setGeneratorUsageHours(request.getGeneratorUsageHours());
        fuel.setLastUpdated(LocalDateTime.now());
        fuel.setMinimumStockLiters(fuel.getMinimumStockLiters() == 0 ? 3000 : fuel.getMinimumStockLiters());
        fuel.setFuelStatus(fuel.getFuelStockLiters() <= fuel.getMinimumStockLiters() ? "WARNING" : "NORMAL");

        Fuel saved = fuelRepository.save(fuel);
        saved.setDaysLeft(calculateDaysLeft(saved.getFuelStockLiters(), saved.getDailyConsumptionLiters()));
        return saved;
    }

    // days_left = fuel_stock_liters / daily_consumption_liters
    // Guarded against divide-by-zero: if consumption is 0, we can't estimate days
    // left
    private double calculateDaysLeft(double stock, double dailyConsumption) {
        if (dailyConsumption <= 0) {
            return -1; // sentinel value meaning "cannot be calculated"
        }
        return stock / dailyConsumption;
    }

    private Fuel getDummyFuel() {
        return new Fuel(null, 12000, 650, 10, 3000, "NORMAL", LocalDateTime.now(), 0);
    }
}