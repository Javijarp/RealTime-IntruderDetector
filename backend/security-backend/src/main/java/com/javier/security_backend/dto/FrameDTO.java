package com.javier.security_backend.dto;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class FrameDTO {
    
    private Long id;
    
    @NotNull(message = "Frame number is required")
    @Min(value = 0, message = "Frame number must be non-negative")
    private Integer frameNumber;
    
    private byte[] imageData;
    
    private String imageType; // "jpeg", "png", etc.
    
    private String imagePath; // Legacy: Path to stored frame image
    
    @NotNull(message = "Timestamp is required")
    private Instant timestamp; // ISO-8601 format
    
    private Instant createdAt;
    
    private Long detectionEventId; // Link to detection event
    
    @Valid
    private List<FaceDTO> faces = new ArrayList<>();
}
