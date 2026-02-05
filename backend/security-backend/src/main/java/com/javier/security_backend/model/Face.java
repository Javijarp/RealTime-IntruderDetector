package com.javier.security_backend.model;

import java.time.Instant;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Entity
@Table(name = "faces")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class Face {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "face_image_path", nullable = false)
    private String faceImagePath; // Path to cropped face image
    
    @Column(name = "confidence", nullable = false)
    private Double confidence; // Face detection confidence
    
    @Column(name = "bounding_box", nullable = true)
    private String boundingBox; // JSON: {"x": 100, "y": 50, "width": 80, "height": 100}
    
    @Column(name = "age", nullable = true)
    private Integer age; // Estimated age
    
    @Column(name = "gender", nullable = true)
    private String gender; // Male, Female, Unknown
    
    @Column(name = "emotion", nullable = true)
    private String emotion; // Happy, Sad, Angry, Neutral, etc.
    
    @Column(name = "face_encoding", nullable = true, columnDefinition = "TEXT")
    private String faceEncoding; // Base64-encoded face embedding/vector
    
    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;
    
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "frame_id", nullable = false)
    private Frame frame;
    
    @PrePersist
    protected void onCreate() {
        createdAt = Instant.now();
    }
}
