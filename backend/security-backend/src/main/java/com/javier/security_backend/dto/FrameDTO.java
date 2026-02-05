package com.javier.security_backend.dto;

import java.util.ArrayList;
import java.util.List;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class FrameDTO {
    
    @NotNull(message = "Frame number is required")
    @Min(value = 0, message = "Frame number must be non-negative")
    private Integer frameNumber;
    
    @NotBlank(message = "Image path is required")
    private String imagePath;
    
    @NotNull(message = "Timestamp is required")
    private String timestamp; // ISO-8601 format
    
    private Long detectionEventId; // Link to detection event
    
    @Valid
    private List<FaceDTO> faces = new ArrayList<>();
}
