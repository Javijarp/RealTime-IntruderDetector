package com.javier.security_backend.controller;

import com.javier.security_backend.dto.DetectionEventDTO;
import com.javier.security_backend.model.DetectionEvent;
import com.javier.security_backend.service.EventProcessingService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/events")
@Slf4j
public class EventController {

    private final EventProcessingService eventProcessingService;

    public EventController(EventProcessingService eventProcessingService) {
        this.eventProcessingService = eventProcessingService;
    }

    /**
     * Endpoint para recibir eventos del Edge Module (Python).
     */
    @PostMapping
    public ResponseEntity<?> receiveDetectionEvent(@RequestBody DetectionEventDTO eventDTO) {
        try {
            DetectionEvent savedEvent = eventProcessingService.processDetectionEvent(eventDTO);

            return ResponseEntity.ok(savedEvent);

        } catch (EventProcessingService.ServiceUnavailableException e) {
            log.error("Sistema sobrecargado: {}", e.getMessage());

            return ResponseEntity
                    .status(HttpStatus.SERVICE_UNAVAILABLE)
                    .body(Map.of(
                            "error", "Sistema sobrecargado",
                            "message", e.getMessage(),
                            "retry_after_seconds", 5));

        } catch (Exception e) {
            log.error("Error procesando evento", e);

            return ResponseEntity
                    .status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Error interno", "message", e.getMessage()));
        }
    }

    /**
     * Endpoint para obtener estadísticas de semáforos (monitoreo).
     */
    @GetMapping("/stats")
    public ResponseEntity<EventProcessingService.SystemStats> getSystemStats() {
        return ResponseEntity.ok(eventProcessingService.getStats());
    }
}