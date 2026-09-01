package com.antarctica.digitaltwin.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.PositiveOrZero;
import lombok.Data;

@Data
public class SyncRequest {

    @NotBlank(message = "Device ID cannot be empty")
    private String deviceId;

    @PositiveOrZero(message = "Records cannot be negative")
    private int records;
}