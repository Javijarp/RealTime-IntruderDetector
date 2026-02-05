package com.javier.security_backend.repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.javier.security_backend.model.DetectionEvent;

@Repository
public interface DetectionEventRepository extends JpaRepository<DetectionEvent, Long> {
    
    // Find by event_id (from edge module)
    Optional<DetectionEvent> findByEventId(Long eventId);
    
    // Find by frame_id (to detect duplicates)
    List<DetectionEvent> findByFrameId(Integer frameId);
    
    // Find events within time range
    List<DetectionEvent> findByTimestampBetween(Instant start, Instant end);
    
    // Find unprocessed events
    List<DetectionEvent> findByProcessedFalse();
    
    // Find by entity type
    List<DetectionEvent> findByEntityType(String entityType);
}