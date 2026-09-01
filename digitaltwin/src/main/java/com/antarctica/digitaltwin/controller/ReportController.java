package com.antarctica.digitaltwin.controller;

import com.antarctica.digitaltwin.service.ReportService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/report")
public class ReportController {

    @Autowired
    private ReportService reportService;

    @GetMapping("/supply")
    public Map<String, Object> getSupplyReport() {
        return reportService.getSupplyReport();
    }

    @GetMapping("/fuel")
    public Map<String, Object> getFuelReport() {
        return reportService.getFuelReport();
    }

    @GetMapping("/station")
    public Map<String, Object> getStationReport() {
        return reportService.getStationReport();
    }
}