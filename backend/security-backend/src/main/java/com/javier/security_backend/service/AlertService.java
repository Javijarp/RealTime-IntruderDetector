package com.javier.security_backend.service;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.javier.security_backend.handler.AlertHandler;
import com.javier.security_backend.model.DetectionEvent;
import com.javier.security_backend.model.Frame;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Service
public class AlertService {

    private static final Logger log = LoggerFactory.getLogger(AlertService.class);
    private static final ObjectMapper objectMapper = new ObjectMapper();

    // Time threshold for "no entities" state (seconds)
    private static final long NO_ENTITY_THRESHOLD_SECONDS = 30;

    private Instant lastDetectionTime = null;
    private boolean inNoEntityState = true; // Start in no-entity state

    // ═══════════════════════════════════════════════════════════════
    // RECURSIVE ALERT STATE TRACKING - Linked List of States
    // ═══════════════════════════════════════════════════════════════

    private AlertState currentState;

    private final AlertHandler alertHandler;

    public AlertService(AlertHandler alertHandler) {
        this.alertHandler = alertHandler;
        // Initialize with starting state
        this.currentState = new AlertState("SYSTEM_READY", Instant.now(), null, null);
    }

    // ═══════════════════════════════════════════════════════════════
    // INNER CLASS: AlertState - Linked List Node for State History
    // ═══════════════════════════════════════════════════════════════

    /**
     * Represents a single state in the alert state history chain.
     * Forms a linked list structure for recursive traversal.
     */
    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class AlertState {
        private String state;
        private Instant timestamp;
        private DetectionEvent triggerEvent;
        private AlertState previousState; // Link to previous state (for recursion)

        public AlertState(String state, Instant timestamp, DetectionEvent event) {
            this.state = state;
            this.timestamp = timestamp;
            this.triggerEvent = event;
            this.previousState = null;
        }
    }

    /**
     * Process a detection event and trigger alert if conditions are met
     * Conditions: First entity after period of no entities
     */
    public void processDetection(DetectionEvent event, Frame frameData) {
        Instant now = Instant.now();

        // Check if we were in "no entity" state
        if (inNoEntityState || lastDetectionTime == null ||
                ChronoUnit.SECONDS.between(lastDetectionTime, now) > NO_ENTITY_THRESHOLD_SECONDS) {

            // This is the first entity after no entities - TRIGGER ALERT!
            log.info("🚨 ALERT: First {} detected after period of no entities!", event.getEntityType());

            // Create new state and link to history
            transitionToState("ALERT_TRIGGERED", event);

            broadcastAlert(event, frameData);
            inNoEntityState = false;
        } else {
            // Still in detection state - update state if needed
            transitionToState("ENTITY_DETECTED", event);
        }

        // Update last detection time
        lastDetectionTime = now;
    }

    /**
     * Transition to a new alert state, maintaining history chain
     * 
     * @param stateName    New state name
     * @param triggerEvent Event that triggered the transition
     */
    private void transitionToState(String stateName, DetectionEvent triggerEvent) {
        AlertState newState = new AlertState(stateName, Instant.now(), triggerEvent);
        newState.setPreviousState(currentState); // Link to previous state
        currentState = newState;

        log.debug("State transition: {} -> {}",
                currentState.getPreviousState() != null ? currentState.getPreviousState().getState() : "null",
                stateName);
    }

    /**
     * Check if we should transition to "no entity" state
     * Call this periodically or when checking state
     */
    public void checkNoEntityState() {
        if (lastDetectionTime != null) {
            Instant now = Instant.now();
            long secondsSinceLastDetection = ChronoUnit.SECONDS.between(lastDetectionTime, now);

            if (secondsSinceLastDetection > NO_ENTITY_THRESHOLD_SECONDS && !inNoEntityState) {
                log.info("📭 Entering no-entity state ({}s since last detection)", secondsSinceLastDetection);
                transitionToState("NO_ENTITIES", null);
                inNoEntityState = true;
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // RECURSIVE ALERT HISTORY METHODS
    // ═══════════════════════════════════════════════════════════════

    /**
     * Recursively traverse alert history and return all states
     * 
     * Time Complexity: O(n) where n = number of states
     * Space Complexity: O(n) for call stack
     * 
     * @return List of all historical states from newest to oldest
     */
    public List<AlertState> getAlertHistory() {
        List<AlertState> history = new ArrayList<>();
        traverseHistory(currentState, history);
        return history;
    }

    /**
     * Helper method for recursive history traversal
     */
    private void traverseHistory(AlertState state, List<AlertState> accumulator) {
        if (state == null) {
            return; // BASE CASE: reached the beginning
        }
        accumulator.add(state);
        traverseHistory(state.getPreviousState(), accumulator); // RECURSIVE CALL
    }

    /**
     * Find when system was last in a specific state
     * 
     * @param targetState State to search for
     * @return AlertState or null if not found
     */
    public AlertState findLastOccurrenceOfState(String targetState) {
        return searchStateRecursively(currentState, targetState);
    }

    /**
     * Helper method for recursive state search
     */
    private AlertState searchStateRecursively(AlertState current, String target) {
        if (current == null) {
            return null; // BASE CASE: not found
        }
        if (current.getState().equals(target)) {
            return current; // BASE CASE: found!
        }
        return searchStateRecursively(current.getPreviousState(), target); // RECURSIVE CALL
    }

    /**
     * Count total state transitions in history
     * 
     * @return Number of state transitions
     */
    public int countStateTransitions() {
        return countTransitionsRecursively(currentState, 0);
    }

    /**
     * Helper method for recursive transition counting
     */
    private int countTransitionsRecursively(AlertState state, int count) {
        if (state == null || state.getPreviousState() == null) {
            return count; // BASE CASE
        }
        return countTransitionsRecursively(state.getPreviousState(), count + 1); // RECURSIVE CALL
    }

    /**
     * Find all paths in event history that match a specific pattern
     * Uses backtracking algorithm
     * 
     * Example: Find sequences like ["NO_ENTITIES", "ENTITY_DETECTED",
     * "ALERT_TRIGGERED"]
     * 
     * @param pattern List of state names to match
     * @return List of all matching state sequences
     */
    public List<List<AlertState>> findAlertPatterns(List<String> pattern) {
        List<List<AlertState>> allPaths = new ArrayList<>();
        List<AlertState> currentPath = new ArrayList<>();

        findPatternRecursively(currentState, pattern, 0, currentPath, allPaths);

        return allPaths;
    }

    /**
     * Helper method for recursive pattern matching with backtracking
     */
    private void findPatternRecursively(
            AlertState current,
            List<String> pattern,
            int patternIndex,
            List<AlertState> currentPath,
            List<List<AlertState>> allPaths) {

        if (current == null) {
            return; // BASE CASE: reached end of history
        }

        // Check if current state matches pattern
        if (current.getState().equals(pattern.get(patternIndex))) {
            currentPath.add(current);

            // BASE CASE: complete pattern found!
            if (patternIndex == pattern.size() - 1) {
                allPaths.add(new ArrayList<>(currentPath)); // Save copy
            } else {
                // RECURSIVE CASE: continue searching for next pattern element
                findPatternRecursively(
                        current.getPreviousState(),
                        pattern,
                        patternIndex + 1,
                        currentPath,
                        allPaths);
            }

            // BACKTRACK: remove this state to explore other paths
            currentPath.remove(currentPath.size() - 1);
        }

        // Try searching from previous state (explore alternative paths)
        findPatternRecursively(
                current.getPreviousState(),
                pattern,
                patternIndex,
                currentPath,
                allPaths);
    }

    /**
     * Get time elapsed since a specific state
     * 
     * @param stateName State to find
     * @return Seconds since that state, or -1 if not found
     */
    public long getSecondsSinceState(String stateName) {
        AlertState state = findLastOccurrenceOfState(stateName);
        if (state == null) {
            return -1;
        }
        return ChronoUnit.SECONDS.between(state.getTimestamp(), Instant.now());
    }

    /**
     * Broadcast alert to all connected WebSocket clients
     */
    private void broadcastAlert(DetectionEvent event, Frame frameData) {
        try {
            Map<String, Object> alertMessage = new HashMap<>();
            alertMessage.put("type", "alert");
            alertMessage.put("eventId", event.getId());
            alertMessage.put("entityType", event.getEntityType());
            alertMessage.put("confidence", event.getConfidence());
            alertMessage.put("timestamp", event.getTimestamp().toString());
            alertMessage.put("message", "New " + event.getEntityType() + " detected!");

            // Include frame image if available
            if (frameData != null && frameData.getImageData() != null) {
                String base64Image = Base64.getEncoder().encodeToString(frameData.getImageData());
                alertMessage.put("imageData", base64Image);
                alertMessage.put("imageType", frameData.getImageType());
            }

            String jsonMessage = objectMapper.writeValueAsString(alertMessage);

            // Broadcast to all connected alert WebSocket sessions
            alertHandler.broadcastAlert(jsonMessage);

            log.info("Alert broadcast to {} clients", alertHandler.getAllSessions().size());

        } catch (Exception e) {
            log.error("Error broadcasting alert: {}", e.getMessage(), e);
        }
    }

    /**
     * Reset to initial state (useful for testing)
     */
    public void reset() {
        log.info("Resetting alert service state");
        lastDetectionTime = null;
        inNoEntityState = true;
        // Reset state history
        currentState = new AlertState("SYSTEM_READY", Instant.now(), null, null);
    }

    /**
     * Get current state info
     */
    public Map<String, Object> getState() {
        Map<String, Object> state = new HashMap<>();
        state.put("inNoEntityState", inNoEntityState);
        state.put("lastDetectionTime", lastDetectionTime != null ? lastDetectionTime.toString() : null);
        state.put("currentAlertState", currentState != null ? currentState.getState() : null);
        state.put("stateTransitionCount", countStateTransitions());

        if (lastDetectionTime != null) {
            long secondsSince = ChronoUnit.SECONDS.between(lastDetectionTime, Instant.now());
            state.put("secondsSinceLastDetection", secondsSince);
        }

        // Add recent state history (last 5 states)
        List<AlertState> history = getAlertHistory();
        List<Map<String, String>> recentHistory = new ArrayList<>();
        for (int i = 0; i < Math.min(5, history.size()); i++) {
            AlertState s = history.get(i);
            Map<String, String> stateInfo = new HashMap<>();
            stateInfo.put("state", s.getState());
            stateInfo.put("timestamp", s.getTimestamp().toString());
            recentHistory.add(stateInfo);
        }
        state.put("recentStateHistory", recentHistory);

        return state;
    }
}
