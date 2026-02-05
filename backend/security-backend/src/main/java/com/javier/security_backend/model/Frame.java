package com.javier.security_backend.model;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OneToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "frames")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Frame {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "frame_number", nullable = false)
    private Integer frameNumber;
    
    @Column(name = "image_path", nullable = false)
    private String imagePath; // Path to stored frame image
    
    @Column(name = "timestamp", nullable = false)
    private Instant timestamp;
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
    
    @OneToOne
    @JoinColumn(name = "detection_event_id")
    private DetectionEvent detectionEvent;
    
    @OneToMany(mappedBy = "frame", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private List<Face> faces = new ArrayList<>();
    
    @PrePersist
    protected void onCreate() {
        createdAt = Instant.now();
    }
}
