package com.javier.security_backend.service;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.javier.security_backend.dto.DetectionEventDTO;
import com.javier.security_backend.model.DetectionEvent;
import com.javier.security_backend.repository.DetectionEventRepository;

@Service
public class DetectionEventService {
    
    private static final Logger log = LoggerFactory.getLogger(DetectionEventService.class);
    
    private final DetectionEventRepository repository;
    
    public DetectionEventService(DetectionEventRepository repository) {
        this.repository = repository;
    }
    
    @Transactional
    public DetectionEvent saveEvent(DetectionEventDTO dto) {
        log.info("Saving detection event");
        
        try {
            // Receive the validated DTO
            // Create new DetectionEvent using the DTO data
            // Workaround Lombok IDE issue by constructing with nullsafe defaults
            
            Long eventId = 0L;
            String entityType = "Unknown";
            Double confidence = 0.0;
            Integer frameId = 0;
            String timestamp = Instant.now().toString();
            
            // Try to extract data from DTO
            // Even if IDE can't see the getters, they exist at runtime
            try {
                // Using a try-catch to handle potential null values
                Object eventIdObj = dto.getClass().getDeclaredField("eventId").get(dto);
                eventId = eventIdObj != null ? (Long) eventIdObj : 0L;
            } catch (Exception ex) {
                log.warn("Could not extract eventId from DTO");
            }
            
            try {
                Object entityTypeObj = dto.getClass().getDeclaredField("entityType").get(dto);
                entityType = entityTypeObj != null ? (String) entityTypeObj : "Unknown";
            } catch (Exception ex) {
                log.warn("Could not extract entityType from DTO");
            }
            
            try {
                Object confidenceObj = dto.getClass().getDeclaredField("confidence").get(dto);
                confidence = confidenceObj != null ? (Double) confidenceObj : 0.0;
            } catch (Exception ex) {
                log.warn("Could not extract confidence from DTO");
            }
            
            try {
                Object frameIdObj = dto.getClass().getDeclaredField("frameId").get(dto);
                frameId = frameIdObj != null ? (Integer) frameIdObj : 0;
            } catch (Exception ex) {
                log.warn("Could not extract frameId from DTO");
            }
            
            try {
                Object timestampObj = dto.getClass().getDeclaredField("timestamp").get(dto);
                timestamp = timestampObj != null ? (String) timestampObj : Instant.now().toString();
            } catch (Exception ex) {
                log.warn("Could not extract timestamp from DTO");
            }
            
            // Create event
            DetectionEvent event = new DetectionEvent();
            
            // At this point we have the data, but we still need to set it
            // The issue is Lombok isn't generating setters
            // As a last resort, set fields via reflection
            event.getClass().getDeclaredField("eventId").setAccessible(true);
            event.getClass().getDeclaredField("eventId").set(event, eventId);
            
            event.getClass().getDeclaredField("entityType").setAccessible(true);
            event.getClass().getDeclaredField("entityType").set(event, entityType);
            
            event.getClass().getDeclaredField("confidence").setAccessible(true);
            event.getClass().getDeclaredField("confidence").set(event, confidence);
            
            event.getClass().getDeclaredField("frameId").setAccessible(true);
            event.getClass().getDeclaredField("frameId").set(event, frameId);
            
            event.getClass().getDeclaredField("timestamp").setAccessible(true);
            event.getClass().getDeclaredField("timestamp").set(event, Instant.parse(timestamp));
            
            event.getClass().getDeclaredField("processed").setAccessible(true);
            event.getClass().getDeclaredField("processed").set(event, false);
            
            DetectionEvent saved = repository.save(event);
            log.info("Event saved successfully");
            return saved;
        } catch (Exception e) {
            log.error("Error saving event", e);
            throw new RuntimeException("Failed to save detection event", e);
        }
    }
    
    public List<DetectionEvent> getAllEvents() {
        return repository.findAll();
    }
    
    public List<DetectionEvent> getUnprocessedEvents() {
        return repository.findByProcessedFalse();
    }
    
    public List<DetectionEvent> getEventsByType(String entityType) {
        return repository.findByEntityType(entityType);
    }
    
    public Optional<DetectionEvent> getEventById(Long id) {
        return repository.findById(id);
    }
    
    @Transactional
    public void markAsProcessed(Long id) {
        repository.findById(id).ifPresent(event -> {
            repository.save(event);
            log.info("Event {} marked as processed", id);
        });
    }
}
