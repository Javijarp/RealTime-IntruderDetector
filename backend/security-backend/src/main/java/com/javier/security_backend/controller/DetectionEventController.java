package com.javier.security_backend.controller;

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
import org.springframework.web.bind.annotation.RestController;

import com.javier.security_backend.dto.DetectionEventDTO;
import com.javier.security_backend.model.DetectionEvent;
import com.javier.security_backend.service.DetectionEventService;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/events")
@CrossOrigin(origins = "*") // Configure properly in production
public class DetectionEventController {
    
    private static final Logger log = LoggerFactory.getLogger(DetectionEventController.class);
    
    private final DetectionEventService service;
    
    public DetectionEventController(DetectionEventService service) {
        this.service = service;
    }
    
    /**
     * Endpoint for edge module to POST detection events
     */
    @PostMapping
    public ResponseEntity<Map<String, Object>> createEvent(@Valid @RequestBody DetectionEventDTO dto) {
        log.info("Received detection event: {}", dto);
        
        try {
            service.saveEvent(dto);
            
            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "Event received successfully");
            
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
    @GetMapping
    public ResponseEntity<List<DetectionEvent>> getAllEvents() {
        return ResponseEntity.ok(service.getAllEvents());
    }
    
    /**
     * Get unprocessed events (for frontend polling or face recognition queue)
     */
    @GetMapping("/unprocessed")
    public ResponseEntity<List<DetectionEvent>> getUnprocessedEvents() {
        return ResponseEntity.ok(service.getUnprocessedEvents());
    }
    
    /**
     * Get events by type (Person or Dog)
     */
    @GetMapping("/type/{entityType}")
    public ResponseEntity<List<DetectionEvent>> getEventsByType(@PathVariable String entityType) {
        return ResponseEntity.ok(service.getEventsByType(entityType));
    }
    
    /**
     * Get single event by ID
     */
    @GetMapping("/{id}")
    public ResponseEntity<DetectionEvent> getEventById(@PathVariable Long id) {
        return service.getEventById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * Mark event as processed (after face recognition or frontend acknowledgment)
     */
    @PatchMapping("/{id}/processed")
    public ResponseEntity<Map<String, String>> markAsProcessed(@PathVariable Long id) {
        service.markAsProcessed(id);
        
        Map<String, String> response = new HashMap<>();
        response.put("message", "Event marked as processed");
        
        return ResponseEntity.ok(response);
    }
}