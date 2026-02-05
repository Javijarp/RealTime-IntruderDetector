package com.unibe.model;

import java.time.LocalDateTime;

public class DetectionEvent {
    private Long id;
    private String entityType; // "Person" or "Dog"
    private Double confidence;
    private Integer frameId;
    private LocalDateTime timestamp;

    public DetectionEvent(Long id, String entityType, Double confidence, Integer frameId, LocalDateTime timestamp) {
        this.id = id;
        this.entityType = entityType;
        this.confidence = confidence;
        this.frameId = frameId;
        this.timestamp = timestamp;
    }

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getEntityType() {
        return entityType;
    }

    public void setEntityType(String entityType) {
        this.entityType = entityType;
    }

    public Double getConfidence() {
        return confidence;
    }

    public void setConfidence(Double confidence) {
        this.confidence = confidence;
    }

    public Integer getFrameId() {
        return frameId;
    }

    public void setFrameId(Integer frameId) {
        this.frameId = frameId;
    }

    public LocalDateTime getTimestamp() {
        return timestamp;
    }

    public void setTimestamp(LocalDateTime timestamp) {
        this.timestamp = timestamp;
    }
}