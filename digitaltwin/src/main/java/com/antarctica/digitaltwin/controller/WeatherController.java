package com.antarctica.digitaltwin.controller;

import com.antarctica.digitaltwin.model.Weather;
import com.antarctica.digitaltwin.service.WeatherService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/weather")
public class WeatherController {

    @Autowired
    private WeatherService weatherService;

    @GetMapping
    public Weather getWeather() {
        return weatherService.getWeather();
    }
}