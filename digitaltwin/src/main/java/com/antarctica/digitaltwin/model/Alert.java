package com.antarctica.digitaltwin.model;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Document(collection = "alerts")
public class Alert {

    @Id
    private String id; // e.g. "A001" — we assign this ourselves, Mongo won't overwrite it

    private String type;
    private String message;
    private String severity;
    private LocalDateTime timestamp;
    private String status;
}