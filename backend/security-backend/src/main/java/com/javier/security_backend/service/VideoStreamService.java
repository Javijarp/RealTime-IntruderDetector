package com.javier.security_backend.service;

import java.io.IOException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArraySet;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

@Service
public class VideoStreamService {

    private static final Logger log = LoggerFactory.getLogger(VideoStreamService.class);

    private final ConcurrentHashMap<String, CopyOnWriteArraySet<WebSocketSession>> streamSubscribers = new ConcurrentHashMap<>();
    private final CopyOnWriteArraySet<WebSocketSession> allSessions = new CopyOnWriteArraySet<>();

    public void trackSession(WebSocketSession session) {
        allSessions.add(session);
        log.debug("Tracking session: {}", session.getId());
    }

    public void untrackSession(WebSocketSession session) {
        allSessions.remove(session);
        log.debug("Untracking session: {}", session.getId());
    }

    public void subscribe(String streamId, WebSocketSession session) {
        streamSubscribers.computeIfAbsent(streamId, k -> new CopyOnWriteArraySet<>())
                .add(session);
        log.info("Client {} subscribed to stream '{}'", session.getId(), streamId);
    }

    public void unsubscribe(WebSocketSession session) {
        streamSubscribers.forEach((streamId, subscribers) -> {
            if (subscribers.remove(session)) {
                log.info("Client {} unsubscribed from stream '{}'", session.getId(), streamId);
            }
        });
    }

    public void broadcastFrame(String streamId, byte[] frameData, String contentType) {
        CopyOnWriteArraySet<WebSocketSession> subscribers = streamSubscribers.get(streamId);

        if (subscribers == null || subscribers.isEmpty()) {
            log.debug("No active subscribers for stream: {}", streamId);
            return;
        }

        String base64Frame = java.util.Base64.getEncoder().encodeToString(frameData);
        String json = String.format(
                "{\"type\": \"frame\", \"streamId\": \"%s\", \"data\": \"%s\", \"contentType\": \"%s\"}",
                streamId, base64Frame, contentType);

        subscribers.forEach(session -> {
            try {
                if (session.isOpen()) {
                    session.sendMessage(new TextMessage(json));
                }
            } catch (IOException e) {
                log.error("Error broadcasting frame to session {}: {}", session.getId(), e.getMessage());
                subscribers.remove(session);
            }
        });

        log.debug("Broadcasted frame to {} subscribers on stream '{}'", subscribers.size(), streamId);
    }

    public int getSubscriberCount(String streamId) {
        CopyOnWriteArraySet<WebSocketSession> subscribers = streamSubscribers.get(streamId);
        return subscribers != null ? (int) subscribers.stream().filter(WebSocketSession::isOpen).count() : 0;
    }

    public int getTotalSubscribers() {
        return streamSubscribers.values().stream()
                .mapToInt(s -> (int) s.stream().filter(WebSocketSession::isOpen).count())
                .sum();
    }

    public int getActiveSessions() {
        return (int) allSessions.stream().filter(WebSocketSession::isOpen).count();
    }

    public CopyOnWriteArraySet<WebSocketSession> getAllSessions() {
        return allSessions;
    }
}
