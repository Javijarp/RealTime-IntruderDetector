package com.javier.security_backend.service;

import com.javier.security_backend.model.DetectionEvent;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

/**
 * Service for sending WebSocket notifications to connected clients.
 * This service is used by EventProcessingService to notify clients about new
 * detection events.
 */
@Service
@Slf4j
public class WebSocketNotificationService {

    /**
     * Notifies connected clients about a new detection event via WebSocket.
     * 
     * @param event The detection event to notify about
     */
    public void notifyNewEvent(DetectionEvent event) {
        // TODO: Implement actual WebSocket notification logic
        // For now, just log the notification
        log.info("WebSocket notification: New event detected - Type: {}, Confidence: {}, ID: {}",
                event.getEntityType(),
                event.getConfidence(),
                event.getId());
    }
}
