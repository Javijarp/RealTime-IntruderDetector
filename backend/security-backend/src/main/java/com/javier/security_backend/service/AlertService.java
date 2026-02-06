package com.javier.security_backend.service;

import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.Base64;
import java.util.HashMap;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.javier.security_backend.model.DetectionEvent;
import com.javier.security_backend.model.Frame;

@Service
public class AlertService {

    private static final Logger log = LoggerFactory.getLogger(AlertService.class);
    private static final ObjectMapper objectMapper = new ObjectMapper();

    // Time threshold for "no entities" state (seconds)
    private static final long NO_ENTITY_THRESHOLD_SECONDS = 30;

    private Instant lastDetectionTime = null;
    private boolean inNoEntityState = true; // Start in no-entity state

    private final VideoStreamService videoStreamService;

    public AlertService(VideoStreamService videoStreamService) {
        this.videoStreamService = videoStreamService;
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
            broadcastAlert(event, frameData);
            inNoEntityState = false;
        }

        // Update last detection time
        lastDetectionTime = now;
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
                inNoEntityState = true;
            }
        }
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
            TextMessage textMessage = new TextMessage(jsonMessage);

            // Broadcast to all connected WebSocket sessions
            for (WebSocketSession session : videoStreamService.getAllSessions()) {
                if (session.isOpen()) {
                    session.sendMessage(textMessage);
                    log.debug("Alert sent to session: {}", session.getId());
                }
            }

            log.info("Alert broadcast to {} clients", videoStreamService.getActiveSessions());

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
    }

    /**
     * Get current state info
     */
    public Map<String, Object> getState() {
        Map<String, Object> state = new HashMap<>();
        state.put("inNoEntityState", inNoEntityState);
        state.put("lastDetectionTime", lastDetectionTime != null ? lastDetectionTime.toString() : null);

        if (lastDetectionTime != null) {
            long secondsSince = ChronoUnit.SECONDS.between(lastDetectionTime, Instant.now());
            state.put("secondsSinceLastDetection", secondsSince);
        }

        return state;
    }
}
