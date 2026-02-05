package com.javier.security_backend.controller;

import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.javier.security_backend.dto.DetectionEventDTO;
import com.javier.security_backend.model.DetectionEvent;
import com.javier.security_backend.model.Frame;
import com.javier.security_backend.service.DetectionEventService;
import com.javier.security_backend.service.FrameService;

import jakarta.validation.Valid;

@RestController
@CrossOrigin(origins = "*") // Configure properly in production
public class DetectionEventController {
    
    private static final Logger log = LoggerFactory.getLogger(DetectionEventController.class);
    
    private final DetectionEventService service;
    private final FrameService frameService;
    
    public DetectionEventController(DetectionEventService service, FrameService frameService) {
        this.service = service;
        this.frameService = frameService;
    }
    
    /**
     * Health check endpoint
     */
    @GetMapping("/")
    public ResponseEntity<Map<String, String>> health() {
        Map<String, String> response = new HashMap<>();
        response.put("status", "UP");
        response.put("message", "Security Backend API is running");
        response.put("endpoints", "/api/events");
        return ResponseEntity.ok(response);
    }
    
    /**
     * Endpoint for edge module to POST detection events with optional frame image
     */
    @PostMapping("/api/events")
    public ResponseEntity<Map<String, Object>> createEvent(
            @Valid @RequestBody(required = false) DetectionEventDTO dto,
            @RequestParam(value = "frameImage", required = false) MultipartFile frameImage) {
        
        try {
            // Handle multipart form data or JSON
            if (dto == null && frameImage == null) {
                throw new IllegalArgumentException("Either detection event or frame image must be provided");
            }
            
            DetectionEvent savedEvent = null;
            Frame savedFrame = null;
            
            // Save detection event
            if (dto != null) {
                log.info("Received detection event: {}", dto);
                savedEvent = service.saveEvent(dto);
            }
            
            // Save frame image if provided
            if (frameImage != null && !frameImage.isEmpty()) {
                log.info("Saving frame image: {} bytes", frameImage.getSize());
                Integer frameNumber = dto != null ? dto.getFrameId() : null;
                savedFrame = frameService.saveFrame(
                    frameImage.getBytes(),
                    frameImage.getContentType(),
                    frameNumber
                );
                
                // Link frame to detection event
                if (savedEvent != null) {
                    savedEvent.setFrameData(savedFrame);
                }
            }
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "Event received successfully");
            if (savedEvent != null) response.put("eventId", savedEvent.getId());
            if (savedFrame != null) response.put("frameId", savedFrame.getId());
            
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
            
        } catch (Exception e) {
            log.error("Error saving event: {}", e.getMessage(), e);
            
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("message", "Error saving event: " + e.getMessage());
            
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }
    
    /**
     * Get all events (for frontend)
     */
    @GetMapping("/api/events")
    public ResponseEntity<List<DetectionEvent>> getAllEvents() {
        return ResponseEntity.ok(service.getAllEvents());
    }
    
    /**
     * Get unprocessed events (for frontend polling or face recognition queue)
     */
    @GetMapping("/api/events/unprocessed")
    public ResponseEntity<List<DetectionEvent>> getUnprocessedEvents() {
        return ResponseEntity.ok(service.getUnprocessedEvents());
    }
    
    /**
     * Get events by type (Person or Dog)
     */
    @GetMapping("/api/events/type/{entityType}")
    public ResponseEntity<List<DetectionEvent>> getEventsByType(@PathVariable String entityType) {
        return ResponseEntity.ok(service.getEventsByType(entityType));
    }
    
    /**
     * Get single event by ID
     */
    @GetMapping("/api/events/{id}")
    public ResponseEntity<DetectionEvent> getEventById(@PathVariable Long id) {
        return service.getEventById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * Mark event as processed (after face recognition or frontend acknowledgment)
     */
    @PatchMapping("/api/events/{id}/process")
    public ResponseEntity<Map<String, String>> markAsProcessed(@PathVariable Long id) {
        service.markAsProcessed(id);
        
        Map<String, String> response = new HashMap<>();
        response.put("message", "Event marked as processed");
        
        return ResponseEntity.ok(response);
    }
}