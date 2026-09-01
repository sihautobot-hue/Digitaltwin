package com.antarctica.digitaltwin.service;

import com.antarctica.digitaltwin.model.Weather;
import com.antarctica.digitaltwin.repository.WeatherRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class WeatherService {

    @Autowired
    private WeatherRepository weatherRepository;

    public Weather getWeather() {
        List<Weather> all = weatherRepository.findAll();
        return all.isEmpty() ? getDummyWeather() : all.get(0);
    }

    private Weather getDummyWeather() {
        return new Weather(null, -18, 42, 71, 3, 990, "Snow", "WARNING", LocalDateTime.now());
    }
}