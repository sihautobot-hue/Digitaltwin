package com.antarctica.digitaltwin.controller;

import com.antarctica.digitaltwin.dto.SyncRequest;
import com.antarctica.digitaltwin.model.SyncStatus;
import com.antarctica.digitaltwin.service.SyncService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/sync")
public class SyncController {

    @Autowired
    private SyncService syncService;

    @GetMapping("/status")
    public SyncStatus getSyncStatus() {
        return syncService.getSyncStatus();
    }

    @PostMapping
    public Map<String, Object> performSync(@Valid @RequestBody SyncRequest request) {
        return syncService.performSync(request);
    }
}