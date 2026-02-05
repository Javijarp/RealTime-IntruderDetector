package com.javier.security_backend.dto;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class DetectionEventDTO {
    
    @NotNull(message = "Event ID is required")
    private Long eventId;
    
    @NotBlank(message = "Entity type is required")
    @Pattern(regexp = "Person|Dog", message = "Entity type must be 'Person' or 'Dog'")
    private String entityType;
    
    @NotNull(message = "Confidence is required")
    @DecimalMin(value = "0.0", message = "Confidence must be at least 0.0")
    @DecimalMax(value = "1.0", message = "Confidence must be at most 1.0")
    private Double confidence;
    
    @NotNull(message = "Frame ID is required")
    @Min(value = 0, message = "Frame ID must be non-negative")
    private Integer frameId;
    
    @NotNull(message = "Timestamp is required")
    private String timestamp; // ISO-8601 format from edge module
}