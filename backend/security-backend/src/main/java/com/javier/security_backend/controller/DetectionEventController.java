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
        response.put("endpoints", "/events");
        return ResponseEntity.ok(response);
    }

    /**
     * Endpoint for edge module to POST detection events (JSON only)
     */
    @PostMapping(value = "/events", consumes = "application/json")
    public ResponseEntity<Map<String, Object>> createEventJson(@RequestBody @Valid DetectionEventDTO dto) {
        try {
            log.info("Received detection event (JSON): {}", dto);
            DetectionEvent savedEvent = service.saveEvent(dto);

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "Event received successfully");
            response.put("eventId", savedEvent.getId());

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
     * Endpoint for edge module to POST detection events with frame image
     * (multipart)
     */
    @PostMapping(value = "/events", consumes = "multipart/form-data")
    public ResponseEntity<Map<String, Object>> createEventMultipart(
            @RequestParam("eventId") Long eventId,
            @RequestParam("entityType") String entityType,
            @RequestParam("confidence") Double confidence,
            @RequestParam("frameId") Integer frameId,
            @RequestParam("timestamp") String timestamp,
            @RequestParam(value = "frameImage", required = false) MultipartFile frameImage) {

        try {
            // Build DTO from form parameters
            DetectionEventDTO dto = new DetectionEventDTO(eventId, entityType, confidence, frameId, timestamp);
            log.info("Received detection event (multipart): {}", dto);

            DetectionEvent savedEvent = service.saveEvent(dto);
            Frame savedFrame = null;

            // Save frame image if provided
            if (frameImage != null && !frameImage.isEmpty()) {
                log.info("Saving frame image: {} bytes", frameImage.getSize());
                savedFrame = frameService.saveFrame(
                        frameImage.getBytes(),
                        frameImage.getContentType(),
                        frameId);

                // Link frame to detection event
                savedEvent.setFrameData(savedFrame);
            }

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "Event received successfully");
            response.put("eventId", savedEvent.getId());
            if (savedFrame != null)
                response.put("frameId", savedFrame.getId());

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
    @GetMapping("/events")
    public ResponseEntity<List<DetectionEvent>> getAllEvents() {
        return ResponseEntity.ok(service.getAllEvents());
    }

    /**
     * Get unprocessed events (for frontend polling or face recognition queue)
     */
    @GetMapping("/events/unprocessed")
    public ResponseEntity<List<DetectionEvent>> getUnprocessedEvents() {
        return ResponseEntity.ok(service.getUnprocessedEvents());
    }

    /**
     * Get events by type (Person or Dog)
     */
    @GetMapping("/events/type/{entityType}")
    public ResponseEntity<List<DetectionEvent>> getEventsByType(@PathVariable String entityType) {
        return ResponseEntity.ok(service.getEventsByType(entityType));
    }

    /**
     * Get single event by ID
     */
    @GetMapping("/events/{id}")
    public ResponseEntity<DetectionEvent> getEventById(@PathVariable Long id) {
        return service.getEventById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Mark event as processed (after face recognition or frontend acknowledgment)
     */
    @PatchMapping("/events/{id}/process")
    public ResponseEntity<Map<String, String>> markAsProcessed(@PathVariable Long id) {
        service.markAsProcessed(id);

        Map<String, String> response = new HashMap<>();
        response.put("message", "Event marked as processed");

        return ResponseEntity.ok(response);
    }
}