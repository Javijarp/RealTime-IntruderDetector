package com.javier.security_backend.handler;

import java.util.concurrent.CopyOnWriteArraySet;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.BinaryMessage;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.AbstractWebSocketHandler;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.javier.security_backend.service.VideoStreamService;

@Component
public class VideoStreamHandler extends AbstractWebSocketHandler {

    private static final Logger log = LoggerFactory.getLogger(VideoStreamHandler.class);
    private static final ObjectMapper objectMapper = new ObjectMapper();

    private final CopyOnWriteArraySet<WebSocketSession> sessions = new CopyOnWriteArraySet<>();
    private final VideoStreamService videoStreamService;

    public VideoStreamHandler(VideoStreamService videoStreamService) {
        this.videoStreamService = videoStreamService;
    }

    @Override
    public void afterConnectionEstablished(WebSocketSession session) throws Exception {
        log.info("WebSocket connection established: {}", session.getId());
        sessions.add(session);
        videoStreamService.trackSession(session);

        // Send connection confirmation
        session.sendMessage(new TextMessage("{\"type\": \"connected\", \"message\": \"Connected to video stream\"}"));
    }

    @Override
    public void handleTextMessage(WebSocketSession session, TextMessage message) throws Exception {
        String payload = message.getPayload();
        log.debug("Received message: {}", payload);

        try {
            // Parse incoming message
            var json = objectMapper.readTree(payload);
            String type = json.get("type").asText();

            switch (type) {
                case "subscribe":
                    String streamId = json.has("streamId") ? json.get("streamId").asText() : "default";
                    videoStreamService.subscribe(streamId, session);
                    log.info("Client subscribed to stream: {}", streamId);
                    break;

                case "unsubscribe":
                    videoStreamService.unsubscribe(session);
                    log.info("Client unsubscribed from stream");
                    break;

                case "ping":
                    session.sendMessage(new TextMessage("{\"type\": \"pong\"}"));
                    break;

                default:
                    log.warn("Unknown message type: {}", type);
            }
        } catch (Exception e) {
            log.error("Error handling text message: {}", e.getMessage(), e);
            session.sendMessage(new TextMessage("{\"type\": \"error\", \"message\": \"" + e.getMessage() + "\"}"));
        }
    }

    @Override
    public void handleBinaryMessage(WebSocketSession session, BinaryMessage message) throws Exception {
        // Handle binary frame data from clients
        log.debug("Received binary message of size: {}", message.getPayloadLength());
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) throws Exception {
        log.error("WebSocket transport error for session {}: {}", session.getId(), exception.getMessage(), exception);
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus closeStatus) throws Exception {
        log.info("WebSocket connection closed: {} with status: {}", session.getId(), closeStatus);
        sessions.remove(session);
        videoStreamService.untrackSession(session);
        videoStreamService.unsubscribe(session);
    }
}
