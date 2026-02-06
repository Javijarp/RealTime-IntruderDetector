package com.javier.security_backend.controller;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.javier.security_backend.dto.FrameDTO;
import com.javier.security_backend.model.Face;
import com.javier.security_backend.model.Frame;
import com.javier.security_backend.service.FrameService;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/frames")
public class FrameController {

    private static final Logger log = LoggerFactory.getLogger(FrameController.class);

    private final FrameService frameService;

    public FrameController(FrameService frameService) {
        this.frameService = frameService;
    }

    /**
     * Save a frame with detected faces
     * POST /api/frames
     */
    @PostMapping
    public ResponseEntity<Map<String, Object>> saveFrame(@Valid @RequestBody FrameDTO dto) {
        log.info("Received frame {}", dto.getFrameNumber());

        try {
            // The new saveFrame method takes byte[], String, Integer
            // For backward compatibility with FrameDTO, we'll just extract what we need
            Frame savedFrame = frameService.saveFrame(
                    dto.getImageData(),
                    dto.getImageType(),
                    dto.getFrameNumber());

            Map<String, Object> response = new HashMap<>();
            response.put("success", true);
            response.put("message", "Frame saved successfully");
            response.put("frameId", savedFrame.getId());

            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (Exception e) {
            log.error("Error saving frame: {}", e.getMessage(), e);

            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("success", false);
            errorResponse.put("message", "Error saving frame: " + e.getMessage());

            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(errorResponse);
        }
    }

    /**
     * Get all frames
     * GET /api/frames
     */
    @GetMapping
    public ResponseEntity<List<Frame>> getAllFrames() {
        return ResponseEntity.ok(frameService.getAllFrames());
    }

    /**
     * Get frame by ID with associated faces
     * GET /api/frames/{id}
     */
    @GetMapping("/{id}")
    public ResponseEntity<Frame> getFrameById(@PathVariable Long id) {
        return frameService.getFrameById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }

    /**
     * Get frames by detection event
     * GET /api/frames/event/{eventId}
     */
    @GetMapping("/event/{eventId}")
    public ResponseEntity<List<Frame>> getFramesByEvent(@PathVariable Long eventId) {
        return ResponseEntity.ok(frameService.getFramesByDetectionEvent(eventId));
    }

    /**
     * Get faces in a specific frame
     * GET /api/frames/{frameId}/faces
     */
    @GetMapping("/{frameId}/faces")
    public ResponseEntity<List<Face>> getFacesInFrame(@PathVariable Long frameId) {
        return ResponseEntity.ok(frameService.getFacesByFrame(frameId));
    }

    /**
     * Get all faces with specific gender
     * GET /api/frames/faces/gender/{gender}
     */
    @GetMapping("/faces/gender/{gender}")
    public ResponseEntity<List<Face>> getFacesByGender(@PathVariable String gender) {
        return ResponseEntity.ok(frameService.getFacesByGender(gender));
    }

    /**
     * Get all faces with specific emotion
     * GET /api/frames/faces/emotion/{emotion}
     */
    @GetMapping("/faces/emotion/{emotion}")
    public ResponseEntity<List<Face>> getFacesByEmotion(@PathVariable String emotion) {
        return ResponseEntity.ok(frameService.getFacesByEmotion(emotion));
    }
}
