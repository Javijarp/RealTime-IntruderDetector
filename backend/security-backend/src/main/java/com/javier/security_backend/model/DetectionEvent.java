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
import jakarta.persistence.ManyToOne;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OneToOne;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.ToString;

@Entity
@Table(name = "detection_events")
@Data
@NoArgsConstructor
@AllArgsConstructor
@ToString(exclude = { "parentEvent", "childEvents" }) // Prevent circular reference in toString
public class DetectionEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "event_id", nullable = false)
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

    @OneToOne(cascade = CascadeType.ALL, optional = true)
    @JoinColumn(name = "frame_data_id", referencedColumnName = "id")
    private Frame frameData;

    // ═══════════════════════════════════════════════════════════════
    // RECURSIVE HIERARCHY SUPPORT - Parent-Child Relationships
    // ═══════════════════════════════════════════════════════════════

    /**
     * Parent event in hierarchy (e.g., main detection that spawned sub-events)
     */
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "parent_event_id")
    private DetectionEvent parentEvent;

    /**
     * Child events (e.g., sub-detections like face features, tracking updates)
     */
    @OneToMany(mappedBy = "parentEvent", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<DetectionEvent> childEvents = new ArrayList<>();

    @PrePersist
    protected void onCreate() {
        createdAt = Instant.now();
    }

    // ═══════════════════════════════════════════════════════════════
    // RECURSIVE METHODS - Tree Traversal and Aggregation
    // ═══════════════════════════════════════════════════════════════

    /**
     * Add a child event to this event
     * 
     * @param child Child detection event
     */
    public void addChild(DetectionEvent child) {
        if (child != null) {
            childEvents.add(child);
            child.setParentEvent(this);
        }
    }

    /**
     * Remove a child event from this event
     * 
     * @param child Child detection event to remove
     */
    public void removeChild(DetectionEvent child) {
        if (child != null) {
            childEvents.remove(child);
            child.setParentEvent(null);
        }
    }

    /**
     * Recursively collect all descendant events in the tree
     * 
     * Time Complexity: O(n) where n = total events in tree
     * Space Complexity: O(h) where h = height of tree (call stack)
     * 
     * @return List of all descendant events
     */
    public List<DetectionEvent> getAllDescendants() {
        List<DetectionEvent> descendants = new ArrayList<>();
        collectDescendants(this, descendants);
        return descendants;
    }

    /**
     * Helper method for recursive descendant collection
     */
    private void collectDescendants(DetectionEvent event, List<DetectionEvent> accumulator) {
        if (event == null || event.getChildEvents() == null) {
            return; // BASE CASE
        }

        for (DetectionEvent child : event.getChildEvents()) {
            accumulator.add(child);
            collectDescendants(child, accumulator); // RECURSIVE CALL
        }
    }

    /**
     * Calculate total confidence score across entire event tree
     * 
     * @return Sum of all confidence scores in tree (this event + descendants)
     */
    public double getTotalTreeConfidence() {
        return calculateTreeConfidence(this);
    }

    /**
     * Helper method for recursive confidence calculation
     */
    private double calculateTreeConfidence(DetectionEvent event) {
        if (event == null) {
            return 0.0; // BASE CASE
        }

        double total = event.getConfidence();

        if (event.getChildEvents() != null) {
            for (DetectionEvent child : event.getChildEvents()) {
                total += calculateTreeConfidence(child); // RECURSIVE CALL
            }
        }

        return total;
    }

    /**
     * Calculate average confidence across entire event tree
     * 
     * @return Average confidence score
     */
    public double getAverageTreeConfidence() {
        int count = countTreeNodes(this);
        return count > 0 ? getTotalTreeConfidence() / count : 0.0;
    }

    /**
     * Count total nodes in event tree (this event + all descendants)
     * 
     * @return Total number of events in tree
     */
    public int getTreeSize() {
        return countTreeNodes(this);
    }

    /**
     * Helper method for recursive node counting
     */
    private int countTreeNodes(DetectionEvent event) {
        if (event == null) {
            return 0; // BASE CASE
        }

        int count = 1; // Count this node

        if (event.getChildEvents() != null) {
            for (DetectionEvent child : event.getChildEvents()) {
                count += countTreeNodes(child); // RECURSIVE CALL
            }
        }

        return count;
    }

    /**
     * Get the maximum depth of the event tree
     * 
     * @return Tree depth (1 for leaf node, > 1 for nodes with children)
     */
    public int getTreeDepth() {
        return calculateTreeDepth(this);
    }

    /**
     * Helper method for recursive depth calculation
     */
    private int calculateTreeDepth(DetectionEvent event) {
        if (event == null || event.getChildEvents() == null || event.getChildEvents().isEmpty()) {
            return 1; // BASE CASE: leaf node
        }

        int maxChildDepth = 0;
        for (DetectionEvent child : event.getChildEvents()) {
            int childDepth = calculateTreeDepth(child); // RECURSIVE CALL
            maxChildDepth = Math.max(maxChildDepth, childDepth);
        }

        return 1 + maxChildDepth;
    }

    /**
     * Check if this event is a root (has no parent)
     * 
     * @return true if root event
     */
    public boolean isRoot() {
        return parentEvent == null;
    }

    /**
     * Check if this event is a leaf (has no children)
     * 
     * @return true if leaf event
     */
    public boolean isLeaf() {
        return childEvents == null || childEvents.isEmpty();
    }

    /**
     * Get the root event of this tree (traverse up to top)
     * 
     * @return Root detection event
     */
    public DetectionEvent getRoot() {
        DetectionEvent current = this;
        while (current.getParentEvent() != null) {
            current = current.getParentEvent();
        }
        return current;
    }
}
