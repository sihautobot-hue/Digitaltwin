package com.antarctica.digitaltwin.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.PositiveOrZero;
import lombok.Data;

@Data
public class InventoryUpdateRequest {

    @NotBlank(message = "Item cannot be empty")
    private String item;

    @PositiveOrZero(message = "Quantity cannot be negative")
    private int quantity;
}