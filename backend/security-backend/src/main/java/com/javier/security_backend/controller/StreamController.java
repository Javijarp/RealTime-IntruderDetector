package com.javier.security_backend.controller;

import java.util.HashMap;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.multipart.MultipartFile;

import com.javier.security_backend.service.VideoStreamService;

@RestController
@RequestMapping("/api/stream")
public class StreamController {

    private static final Logger log = LoggerFactory.getLogger(StreamController.class);

    private final VideoStreamService videoStreamService;

    public StreamController(VideoStreamService videoStreamService) {
        this.videoStreamService = videoStreamService;
    }

    /**
     * Health check for stream service
     */
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        Map<String, Object> response = new HashMap<>();
        response.put("status", "UP");
        response.put("service", "Video Stream Service");
        response.put("totalSubscribers", videoStreamService.getTotalSubscribers());
        return ResponseEntity.ok(response);
    }

    /**
     * Push a frame to a specific stream
     * Used by edge module or other frame sources
     */
    @PostMapping("/{streamId}/frame")
    public ResponseEntity<Map<String, String>> pushFrame(
            @PathVariable String streamId,
            @RequestParam("frame") MultipartFile frameFile,
            @RequestParam(value = "contentType", defaultValue = "image/jpeg") String contentType) {

        try {
            log.debug("Received frame for stream: {} (size: {} bytes)", streamId, frameFile.getSize());

            byte[] frameData = frameFile.getBytes();
            videoStreamService.broadcastFrame(streamId, frameData, contentType);

            Map<String, String> response = new HashMap<>();
            response.put("status", "success");
            response.put("message", "Frame broadcast to " + videoStreamService.getSubscriberCount(streamId) + " subscribers");

            return ResponseEntity.ok(response);
        } catch (Exception e) {
            log.error("Error pushing frame to stream {}: {}", streamId, e.getMessage(), e);

            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("status", "error");
            errorResponse.put("message", "Failed to push frame: " + e.getMessage());

            return ResponseEntity.status(500).body(errorResponse);
        }
    }

    /**
     * Get stream statistics
     */
    @GetMapping("/{streamId}/stats")
    public ResponseEntity<Map<String, Object>> getStreamStats(@PathVariable String streamId) {
        Map<String, Object> response = new HashMap<>();
        response.put("streamId", streamId);
        response.put("subscribers", videoStreamService.getSubscriberCount(streamId));
        response.put("totalSubscribers", videoStreamService.getTotalSubscribers());

        return ResponseEntity.ok(response);
    }
}
