package com.javier.security_backend.service;

import com.javier.security_backend.dto.DetectionEventDTO;
import com.javier.security_backend.model.DetectionEvent;
import com.javier.security_backend.repository.DetectionEventRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.javier.security_backend.service.WebSocketNotificationService;

import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Service for processing detection events with semaphore-based concurrency
 * control.
 * Implements synchronization between Edge Module (Python) and Backend (Spring
 * Boot).
 */
@Service
@Slf4j
public class EventProcessingService {

    private final DetectionEventRepository eventRepository;
    private final WebSocketNotificationService websocketService;

    // ═══════════════════════════════════════════════════════════════
    // SEMÁFOROS PARA CONTROL DE CONCURRENCIA
    // ═══════════════════════════════════════════════════════════════

    /**
     * Semáforo 1: Limita el procesamiento concurrente de eventos de detección.
     * Capacidad: 5 eventos simultáneos.
     * Propósito: Evitar sobrecarga del sistema con múltiples edge modules.
     */
    private final Semaphore eventProcessingSemaphore = new Semaphore(5);

    /**
     * Semáforo 2: Controla escrituras concurrentes a la base de datos.
     * Capacidad: 3 transacciones simultáneas.
     * Propósito: Evitar deadlocks y contención en la BD.
     */
    private final Semaphore databaseWriteSemaphore = new Semaphore(3);

    /**
     * Semáforo 3: Limita notificaciones WebSocket concurrentes.
     * Capacidad: 10 notificaciones simultáneas.
     * Propósito: Evitar saturar clientes conectados vía WebSocket.
     */
    private final Semaphore websocketNotificationSemaphore = new Semaphore(10);

    /**
     * Semáforo 4: Control de acceso al procesamiento de imágenes.
     * Capacidad: 2 procesamientos simultáneos.
     * Propósito: Limitar uso de CPU/memoria en análisis de frames.
     */
    private final Semaphore imageProcessingSemaphore = new Semaphore(2);

    // Contadores atómicos para estadísticas
    private final AtomicInteger eventsReceived = new AtomicInteger(0);
    private final AtomicInteger eventsProcessed = new AtomicInteger(0);
    private final AtomicInteger eventsRejected = new AtomicInteger(0);
    private final AtomicInteger semaphoreTimeouts = new AtomicInteger(0);

    public EventProcessingService(
            DetectionEventRepository eventRepository,
            WebSocketNotificationService websocketService) {
        this.eventRepository = eventRepository;
        this.websocketService = websocketService;

        log.info("╔════════════════════════════════════════════════════════════════╗");
        log.info("║  EventProcessingService Initialized with Semaphores          ║");
        log.info("╠════════════════════════════════════════════════════════════════╣");
        log.info("║  Semaphore 1: Event Processing    → Capacity: 5              ║");
        log.info("║  Semaphore 2: Database Writes     → Capacity: 3              ║");
        log.info("║  Semaphore 3: WebSocket Notify    → Capacity: 10             ║");
        log.info("║  Semaphore 4: Image Processing    → Capacity: 2              ║");
        log.info("╚════════════════════════════════════════════════════════════════╝");
    }

    /**
     * Procesa un evento de detección del Edge Module con control de semáforo.
     *
     * @param eventDTO Datos del evento recibido vía HTTP POST
     * @return DetectionEvent guardado en BD
     * @throws ServiceUnavailableException si el sistema está sobrecargado
     */
    @Transactional
    public DetectionEvent processDetectionEvent(DetectionEventDTO eventDTO) {
        eventsReceived.incrementAndGet();

        log.info("╔════════════════════════════════════════════════════════════════╗");
        log.info("║  NUEVO EVENTO RECIBIDO                                        ║");
        log.info("╠════════════════════════════════════════════════════════════════╣");
        log.info("║  Entity Type: {}", String.format("%-46s", eventDTO.getEntityType()) + "║");
        log.info("║  Confidence:  {}", String.format("%-46.2f", eventDTO.getConfidence()) + "║");
        log.info("║  Frame ID:    {}", String.format("%-46d", eventDTO.getFrameId()) + "║");
        log.info("╚════════════════════════════════════════════════════════════════╝");

        try {
            // ═══════════════════════════════════════════════════════════════
            // SEMÁFORO 1: Intentar adquirir permiso de procesamiento
            // Timeout: 5 segundos | Si excede, rechazar evento
            // ═══════════════════════════════════════════════════════════════
            long startWaitTime = System.currentTimeMillis();

            if (eventProcessingSemaphore.tryAcquire(5, TimeUnit.SECONDS)) {
                long waitTime = System.currentTimeMillis() - startWaitTime;
                int available = eventProcessingSemaphore.availablePermits();

                log.info("✓ Semáforo de procesamiento ADQUIRIDO");
                log.info("  → Disponibles: {}/5 | Tiempo de espera: {}ms",
                        available, waitTime);

                try {
                    // Procesar el evento
                    DetectionEvent savedEvent = processEventLogic(eventDTO);

                    eventsProcessed.incrementAndGet();
                    return savedEvent;

                } finally {
                    // ═══════════════════════════════════════════════════════════════
                    // CRÍTICO: Siempre liberar el semáforo
                    // ═══════════════════════════════════════════════════════════════
                    eventProcessingSemaphore.release();
                    int availableAfter = eventProcessingSemaphore.availablePermits();
                    log.info("✓ Semáforo de procesamiento LIBERADO (disponibles: {}/5)",
                            availableAfter);
                }

            } else {
                // Timeout esperando semáforo
                semaphoreTimeouts.incrementAndGet();
                eventsRejected.incrementAndGet();

                log.warn("╔════════════════════════════════════════════════════════════════╗");
                log.warn("║  ⚠ TIMEOUT ESPERANDO SEMÁFORO (5 segundos)                   ║");
                log.warn("║  Sistema SOBRECARGADO → Evento RECHAZADO                     ║");
                log.warn("║  Stats: Recibidos={} | Procesados={} | Rechazados={}",
                        eventsReceived.get(), eventsProcessed.get(), eventsRejected.get());
                log.warn("╚════════════════════════════════════════════════════════════════╝");

                throw new ServiceUnavailableException(
                        "Sistema sobrecargado. Intente más tarde.");
            }

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            eventsRejected.incrementAndGet();

            log.error("✗ Thread INTERRUMPIDO esperando semáforo", e);
            throw new RuntimeException("Procesamiento interrumpido", e);
        }
    }

    /**
     * Lógica interna de procesamiento del evento (con semáforos anidados).
     */
    private DetectionEvent processEventLogic(DetectionEventDTO eventDTO) {
        DetectionEvent event = new DetectionEvent();
        event.setEventId(eventDTO.getEventId());
        event.setEntityType(eventDTO.getEntityType());
        event.setConfidence(eventDTO.getConfidence());
        event.setFrameId(eventDTO.getFrameId());
        event.setTimestamp(java.time.Instant.now());
        event.setProcessed(false);

        // 1. Guardar en base de datos con semáforo
        DetectionEvent savedEvent = saveToDatabase(event);

        // 2. Enviar notificación WebSocket con semáforo
        sendWebSocketNotification(savedEvent);

        log.info("✓ Evento procesado completamente: ID={}", savedEvent.getId());

        return savedEvent;
    }

    /**
     * Guarda el evento en la base de datos con semáforo de escritura.
     */
    private DetectionEvent saveToDatabase(DetectionEvent event) {
        try {
            // ═══════════════════════════════════════════════════════════════
            // SEMÁFORO 2: Controlar escrituras a BD (max 3 simultáneas)
            // ═══════════════════════════════════════════════════════════════
            databaseWriteSemaphore.acquire();

            try {
                int available = databaseWriteSemaphore.availablePermits();
                log.info("  ✓ Semáforo de BD adquirido (disponibles: {}/3)", available);

                // Guardar en repositorio
                DetectionEvent savedEvent = eventRepository.save(event);

                log.info("  ✓ Evento guardado en BD: ID={}", savedEvent.getId());

                return savedEvent;

            } finally {
                databaseWriteSemaphore.release();
                int available = databaseWriteSemaphore.availablePermits();
                log.info("  ✓ Semáforo de BD liberado (disponibles: {}/3)", available);
            }

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            log.error("  ✗ Escritura a BD interrumpida", e);
            throw new RuntimeException("Database write interrupted", e);
        }
    }

    /**
     * Envía notificación WebSocket con control de semáforo.
     */
    private void sendWebSocketNotification(DetectionEvent event) {
        // ═══════════════════════════════════════════════════════════════
        // SEMÁFORO 3: Controlar notificaciones WebSocket (max 10 simultáneas)
        // Non-blocking: si no hay espacio, se descarta la notificación
        // ═══════════════════════════════════════════════════════════════
        if (websocketNotificationSemaphore.tryAcquire()) {
            try {
                int available = websocketNotificationSemaphore.availablePermits();
                log.info("  ✓ Semáforo WebSocket adquirido (disponibles: {}/10)", available);

                // Enviar notificación
                websocketService.notifyNewEvent(event);

                log.info("  ✓ Notificación WebSocket enviada");

            } finally {
                websocketNotificationSemaphore.release();
                log.info("  ✓ Semáforo WebSocket liberado");
            }
        } else {
            log.warn("  ⚠ Límite de WebSocket alcanzado. Notificación descartada.");
        }
    }

    /**
     * Obtiene estadísticas del sistema.
     */
    public SystemStats getStats() {
        return SystemStats.builder()
                .eventsReceived(eventsReceived.get())
                .eventsProcessed(eventsProcessed.get())
                .eventsRejected(eventsRejected.get())
                .semaphoreTimeouts(semaphoreTimeouts.get())
                .availableProcessingSlots(eventProcessingSemaphore.availablePermits())
                .availableDatabaseSlots(databaseWriteSemaphore.availablePermits())
                .availableWebSocketSlots(websocketNotificationSemaphore.availablePermits())
                .build();
    }

    /**
     * Excepción personalizada para indicar sistema no disponible.
     */
    public static class ServiceUnavailableException extends RuntimeException {
        public ServiceUnavailableException(String message) {
            super(message);
        }
    }

    /**
     * DTO para estadísticas del sistema.
     */
    @lombok.Data
    @lombok.Builder
    public static class SystemStats {
        private int eventsReceived;
        private int eventsProcessed;
        private int eventsRejected;
        private int semaphoreTimeouts;
        private int availableProcessingSlots;
        private int availableDatabaseSlots;
        private int availableWebSocketSlots;
    }
}