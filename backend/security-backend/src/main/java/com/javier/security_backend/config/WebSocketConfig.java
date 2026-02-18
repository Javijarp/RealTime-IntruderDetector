package com.javier.security_backend.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

import com.javier.security_backend.handler.AlertHandler;
import com.javier.security_backend.handler.VideoStreamHandler;

@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {

    private final VideoStreamHandler videoStreamHandler;
    private final AlertHandler alertHandler;

    public WebSocketConfig(VideoStreamHandler videoStreamHandler, AlertHandler alertHandler) {
        this.videoStreamHandler = videoStreamHandler;
        this.alertHandler = alertHandler;
    }

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(videoStreamHandler, "/ws/stream")
                .setAllowedOriginPatterns("*"); // Allow all origins for Docker environment

        registry.addHandler(alertHandler, "/ws/alerts")
                .setAllowedOriginPatterns("*"); // Allow all origins for Docker environment
    }
}
