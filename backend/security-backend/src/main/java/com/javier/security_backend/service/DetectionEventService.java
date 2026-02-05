package com.javier.security_backend.service;

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
        log.info("Saving detection event from frame");
        
        try {
            DetectionEvent event = new DetectionEvent();
            repository.save(event);
            log.info("Event saved successfully");
            return event;
        } catch (Exception e) {
            log.error("Error saving event", e);
            throw e;
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
