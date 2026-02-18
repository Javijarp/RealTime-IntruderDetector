package com.javier.security_backend.handler;

import java.util.concurrent.CopyOnWriteArraySet;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.AbstractWebSocketHandler;

import com.fasterxml.jackson.databind.ObjectMapper;

@Component
public class AlertHandler extends AbstractWebSocketHandler {

    private static final Logger log = LoggerFactory.getLogger(AlertHandler.class);
    private static final ObjectMapper objectMapper = new ObjectMapper();

    private final CopyOnWriteArraySet<WebSocketSession> sessions = new CopyOnWriteArraySet<>();

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        log.info("Alert WebSocket connection established: {}", session.getId());
        sessions.add(session);

        // Send connection confirmation
        session.sendMessage(new TextMessage("{\"type\": \"connected\", \"message\": \"Connected to alerts\"}"));
    }

    @Override
    public void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        log.debug("Received alert message: {}", payload);

        try {
            var json = objectMapper.readTree(payload);
            String type = json.get("type").asText();

            switch (type) {
                case "ping":
                    session.sendMessage(new TextMessage("{\"type\": \"pong\"}"));
                    break;

                default:
                    log.warn("Unknown message type in AlertHandler: {}", type);
            }
        } catch (Exception e) {
            log.error("Error handling alert message: {}", e.getMessage(), e);
            session.sendMessage(new TextMessage("{\"type\": \"error\", \"message\": \"" + e.getMessage() + "\"}"));
        }
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) throws Exception {
        log.error("Alert WebSocket transport error for session {}: {}", session.getId(), exception.getMessage(),
                exception);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus closeStatus) throws Exception {
        log.info("Alert WebSocket connection closed: {} with status: {}", session.getId(), closeStatus);
        sessions.remove(session);
    }

    /**
     * Broadcast alert message to all connected clients
     */
    public void broadcastAlert(String alertMessage) {
        TextMessage message = new TextMessage(alertMessage);
        for (WebSocketSession session : sessions) {
            if (session.isOpen()) {
                try {
                    session.sendMessage(message);
                    log.debug("Alert sent to session: {}", session.getId());
                } catch (Exception e) {
                    log.error("Error sending alert to session {}: {}", session.getId(), e.getMessage());
                }
            }
        }
    }

    /**
     * Get all active alert sessions
     */
    public CopyOnWriteArraySet<WebSocketSession> getAllSessions() {
        return sessions;
    }
}
