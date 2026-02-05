package com.javier.security_backend.model;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "detection_events")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class DetectionEvent {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "event_id", unique = true, nullable = false)
    private Long eventId;
    
    @Column(name = "entity_type", nullable = false)
    private String entityType;
    
    @Column(name = "confidence", nullable = false)
    private Double confidence;
    
    @Column(name = "frame_id", nullable = false)
    private Integer frameId;
    
    @Column(name = "timestamp", nullable = false)
    private Instant timestamp;
    
    @Column(name = "processed", nullable = false)
    private Boolean processed = false;
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
    
    @PrePersist
    protected void onCreate() {
        createdAt = Instant.now();
    }
}
