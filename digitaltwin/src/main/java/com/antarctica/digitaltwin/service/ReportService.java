package com.antarctica.digitaltwin.service;

import com.antarctica.digitaltwin.model.Fuel;
import com.antarctica.digitaltwin.model.Inventory;
import com.antarctica.digitaltwin.model.Power;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Service
public class ReportService {

    @Autowired
    private InventoryService inventoryService;

    @Autowired
    private FuelService fuelService;

    @Autowired
    private PowerService powerService;

    public Map<String, Object> getSupplyReport() {
        List<Inventory> items = inventoryService.getAllInventory();

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("total_items", items.size());
        summary.put("low_stock_items", items.stream().filter(i -> "WARNING".equals(i.getStatus())).count());

        return buildReport("SUPPLY", items, summary);
    }

    public Map<String, Object> getFuelReport() {
        Fuel fuel = fuelService.getFuel();

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("fuel_stock_liters", fuel.getFuelStockLiters());
        summary.put("days_left", fuel.getDaysLeft());
        summary.put("fuel_status", fuel.getFuelStatus());

        return buildReport("FUEL", List.of(fuel), summary);
    }

    public Map<String, Object> getStationReport() {
        Power power = powerService.getPower();

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("power_status", power.getPowerStatus());
        summary.put("battery_soc_percent", power.getBatterySocPercent());

        return buildReport("STATION", List.of(power), summary);
    }

    private Map<String, Object> buildReport(String type, Object items, Map<String, Object> summary) {
        Map<String, Object> report = new LinkedHashMap<>();
        report.put("report_type", type);
        report.put("generated_at", LocalDateTime.now());
        report.put("station", "Antarctica Research Station");
        report.put("items", items);
        report.put("summary", summary);
        return report;
    }
}