package com.javier.security_backend.dto;

import jakarta.validation.constraints.DecimalMax;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class FaceDTO {
    
    @NotBlank(message = "Face image path is required")
    private String faceImagePath;
    
    @NotNull(message = "Confidence is required")
    @DecimalMin(value = "0.0", message = "Confidence must be at least 0.0")
    @DecimalMax(value = "1.0", message = "Confidence must be at most 1.0")
    private Double confidence;
    
    private String boundingBox; // JSON object as string
    
    @Min(value = 0, message = "Age must be non-negative")
    @Max(value = 150, message = "Age must be realistic")
    private Integer age;
    
    private String gender; // Male, Female, Unknown
    
    private String emotion; // Happy, Sad, Angry, Neutral, Surprised, etc.
    
    private String faceEncoding; // Base64-encoded face embedding
}
