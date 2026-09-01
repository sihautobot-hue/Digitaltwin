package com.antarctica.digitaltwin.controller;

import com.antarctica.digitaltwin.model.Power;
import com.antarctica.digitaltwin.service.PowerService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/power")
public class PowerController {

    @Autowired
    private PowerService powerService;

    @GetMapping
    public Power getPower() {
        return powerService.getPower();
    }
}