package com.antarctica.digitaltwin.service;

import com.antarctica.digitaltwin.model.Power;
import com.antarctica.digitaltwin.repository.PowerRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class PowerService {

    @Autowired
    private PowerRepository powerRepository;

    public Power getPower() {
        List<Power> all = powerRepository.findAll();
        return all.isEmpty() ? getDummyPower() : all.get(0);
    }

    private Power getDummyPower() {
        return new Power(null, 420, 78, "ON", 250, 120, "NORMAL", LocalDateTime.now());
    }
}