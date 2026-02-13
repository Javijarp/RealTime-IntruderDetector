"""Main EdgeModule Class — Multi-threaded Detection System with Semaphores."""

import threading
import queue
import time
import json
try:
    from .config import Config
    from .models import DetectionEvent
    from .buffer import LocalBuffer
    from .shared import SharedFrame, log
    from .inference import run_yolo_inference
    from .drawing import draw_boxes
    from .network import simulated_http_post, send_stream_frame
except ImportError:
    from config import Config
    from models import DetectionEvent
    from buffer import LocalBuffer
    from shared import SharedFrame, log
    from inference import run_yolo_inference
    from drawing import draw_boxes
    from network import simulated_http_post, send_stream_frame

# Global shared frame (LIVE mode only)
_shared_frame = SharedFrame()


class EdgeModule:
    """Main orchestrator for 3-thread detection system with semaphore synchronization."""

    def __init__(self):
        """Initialize edge module with queues, buffers and semaphores."""
        self._frame_queue: queue.Queue[tuple] = queue.Queue(maxsize=5)
        self._event_queue: queue.Queue[DetectionEvent] = queue.Queue(maxsize=10)
        self._local_buffer = LocalBuffer()
        self._last_detection: dict[str, float] = {}
        self._frame_counter = 0
        self._running = False
        self._previous_detection_state: dict[str, bool] = {}
        
        self._latest_frame = None
        self._latest_frame_lock = threading.Lock()
        
        # ═══════════════════════════════════════════════════════════════
        # SEMÁFOROS IMPLEMENTADOS PARA SINCRONIZACIÓN
        # ═══════════════════════════════════════════════════════════════
        
        # Semáforo 1: Control del buffer de frames (Producer-Consumer)
        # Limita a 5 frames en el buffer para evitar sobrecarga de memoria
        self._frame_buffer_semaphore = threading.Semaphore(5)
        log("[INIT] ✓ Semáforo de buffer creado (capacidad: 5 frames)")
        
        # Semáforo 2: Control de procesamiento YOLO concurrente
        # Permite máximo 2 inferencias simultáneas para optimizar GPU/CPU
        self._yolo_processing_semaphore = threading.Semaphore(2)
        log("[INIT] ✓ Semáforo de procesamiento YOLO creado (capacidad: 2 simultáneos)")
        
        # Semáforo 3: Control de transmisión HTTP al backend
        # Limita a 3 requests HTTP concurrentes para no saturar el backend
        self._http_transmission_semaphore = threading.Semaphore(3)
        log("[INIT] ✓ Semáforo de transmisión HTTP creado (capacidad: 3 simultáneos)")
        
        # Semáforo 4: Control de streaming de video
        # Permite solo 1 stream activo para evitar duplicación
        self._video_streaming_semaphore = threading.Semaphore(1)
        log("[INIT] ✓ Semáforo de streaming creado (capacidad: 1 stream)")
        
        # Mutex para sección crítica de cooldown (evita race conditions)
        self._cooldown_lock = threading.Lock()
        
        # Contador de estadísticas para monitoreo
        self._stats_lock = threading.Lock()
        self._stats = {
            "frames_captured": 0,
            "frames_dropped": 0,
            "frames_processed": 0,
            "events_sent": 0,
            "events_buffered": 0,
            "semaphore_waits": 0,
            "semaphore_timeouts": 0
        }

    # ─── THREAD 1: CAPTURE con Control de Semáforo ─────────────────────────
    def _capture_thread(self) -> None:
        """Capture frames from camera (LIVE) or simulate them."""
        if Config.LIVE_MODE:
            self._capture_live()
        else:
            self._capture_simulated()

    def _capture_live(self) -> None:
        """Capture frames from real camera with semaphore-controlled buffer."""
        import cv2

        cap = None
        camera_idx = Config.CAMERA_INDEX
        log(f"[CAPTURA] Intentando abrir cámara en índice {camera_idx}…")
        cap = cv2.VideoCapture(camera_idx)
        
        if cap.isOpened():
            log(f"[CAPTURA] ✓ Cámara abierta exitosamente (índice {camera_idx})")
        else:
            log(f"[CAPTURA] ✗ Error al abrir cámara {camera_idx}. Intentando índice 0...")
            cap = cv2.VideoCapture(0)

        if cap is None or not cap.isOpened():
            log("[CAPTURA] ✗✗ FATAL: No se pudo abrir ninguna cámara.")
            self._running = False
            return

        log("[CAPTURA] Iniciando captura con control de semáforo...")
        frame_count = 0

        while self._running:
            self._frame_counter += 1
            ret, frame = cap.read()
            
            if not ret:
                log(f"[CAPTURA] ✗ Error leyendo frame {self._frame_counter}")
                time.sleep(0.1)
                continue

            with self._stats_lock:
                self._stats["frames_captured"] += 1

            # ═══════════════════════════════════════════════════════════════
            # SEMÁFORO 1: Intentar adquirir slot en el buffer
            # Si no hay espacio, el frame se descarta (backpressure)
            # ═══════════════════════════════════════════════════════════════
            if self._frame_buffer_semaphore.acquire(blocking=False):
                try:
                    # Intentar agregar frame a la cola
                    self._frame_queue.put_nowait((self._frame_counter, frame))
                    available = self._frame_buffer_semaphore._value
                    log(f"[CAPTURA] ✓ Frame {self._frame_counter} → buffer "
                        f"(slots disponibles: {available}/5)")
                    
                except queue.Full:
                    # Cola llena, liberar semáforo y descartar frame
                    self._frame_buffer_semaphore.release()
                    with self._stats_lock:
                        self._stats["frames_dropped"] += 1
                    log(f"[CAPTURA] ⚠ Cola llena. Frame {self._frame_counter} DESCARTADO")
            else:
                # No hay slots disponibles en el semáforo
                with self._stats_lock:
                    self._stats["frames_dropped"] += 1
                    self._stats["semaphore_timeouts"] += 1
                log(f"[CAPTURA] ⚠ Semáforo LLENO (0/5). "
                    f"Frame {self._frame_counter} DESCARTADO (backpressure activo)")

            # Limitar a ~30 FPS
            time.sleep(1.0 / 30.0)

        cap.release()
        log(f"[CAPTURA] Cámara liberada. Stats: {self._stats['frames_captured']} capturados, "
            f"{self._stats['frames_dropped']} descartados")

    def _capture_simulated(self) -> None:
        """Simulate camera capture at 30 FPS with semaphore control."""
        log("[CAPTURA] Modo SIMULADO activado (30 FPS)")
        
        while self._running:
            self._frame_counter += 1
            
            with self._stats_lock:
                self._stats["frames_captured"] += 1
            
            # Simular frame como None (modo simulado)
            if self._frame_buffer_semaphore.acquire(blocking=False):
                try:
                    self._frame_queue.put_nowait((self._frame_counter, None))
                    log(f"[CAPTURA] ✓ Frame simulado {self._frame_counter} → buffer")
                except queue.Full:
                    self._frame_buffer_semaphore.release()
                    with self._stats_lock:
                        self._stats["frames_dropped"] += 1
            else:
                with self._stats_lock:
                    self._stats["frames_dropped"] += 1
            
            time.sleep(1.0 / 30.0)
        
        log("[CAPTURA] Simulación terminada")

    # ─── THREAD 2: PROCESSING con Semáforo YOLO ────────────────────────────
    def _processing_thread(self) -> None:
        """Process frames with semaphore-controlled YOLO inference."""
        log("[PROCESO] Hilo iniciado con semáforo YOLO (max 2 simultáneos)")

        while self._running:
            try:
                # Obtener frame de la cola (timeout 0.1s)
                frame_id, frame = self._frame_queue.get(timeout=0.1)
                
                # ═══════════════════════════════════════════════════════════════
                # SEMÁFORO 1: Liberar slot del buffer al extraer frame
                # Esto permite que el thread de captura agregue más frames
                # ═══════════════════════════════════════════════════════════════
                self._frame_buffer_semaphore.release()
                available = self._frame_buffer_semaphore._value
                log(f"[PROCESO] Frame {frame_id} extraído. "
                    f"Buffer liberado (slots: {available}/5)")
                
            except queue.Empty:
                continue

            # ═══════════════════════════════════════════════════════════════
            # SEMÁFORO 2: Adquirir semáforo de procesamiento YOLO
            # Bloquea hasta que haya un slot disponible (max 2 simultáneos)
            # ═══════════════════════════════════════════════════════════════
            acquisition_start = time.perf_counter()
            self._yolo_processing_semaphore.acquire()  # BLOCKING
            wait_time = (time.perf_counter() - acquisition_start) * 1000
            
            with self._stats_lock:
                if wait_time > 1:  # Si esperó más de 1ms
                    self._stats["semaphore_waits"] += 1
            
            available = self._yolo_processing_semaphore._value
            log(f"[PROCESO] ✓ Frame {frame_id} - Semáforo YOLO adquirido "
                f"(disponibles: {available}/2, esperó: {wait_time:.1f}ms)")

            try:
                # Guardar frame más reciente
                if frame is not None:
                    with self._latest_frame_lock:
                        self._latest_frame = frame.copy()

                # Realizar inferencia YOLO
                process_start = time.perf_counter()
                detections = run_yolo_inference(frame_id, frame)
                inference_time = (time.perf_counter() - process_start) * 1000

                with self._stats_lock:
                    self._stats["frames_processed"] += 1

                log(f"[PROCESO] Frame {frame_id} - YOLO completado en {inference_time:.1f}ms "
                    f"({len(detections)} detecciones)")

                # Actualizar shared frame para display (LIVE mode)
                if Config.LIVE_MODE and frame is not None:
                    _shared_frame.write(frame, detections)

                # Procesar detecciones con tracking de estado
                has_detections = len(detections) > 0
                had_detections_before = any(self._previous_detection_state.values())
                
                if not detections:
                    if had_detections_before:
                        log(f"[PROCESO] Frame {frame_id}: "
                            "Transición CON → SIN detección")
                    self._previous_detection_state.clear()
                    continue

                # Detectar transición SIN → CON detección (trigger evento)
                if not had_detections_before:
                    log(f"[PROCESO] Frame {frame_id}: "
                        "⚠ TRANSICIÓN SIN → CON DETECCIÓN (generando evento)")
                    self._process_detections(frame_id, detections, process_start)
                    for det in detections:
                        self._previous_detection_state[det["class"]] = True
                
            finally:
                # ═══════════════════════════════════════════════════════════════
                # CRÍTICO: Siempre liberar el semáforo YOLO
                # ═══════════════════════════════════════════════════════════════
                self._yolo_processing_semaphore.release()
                available = self._yolo_processing_semaphore._value
                log(f"[PROCESO] Frame {frame_id} - Semáforo YOLO liberado "
                    f"(disponibles: {available}/2)")

        log(f"[PROCESO] Hilo terminado. "
            f"Procesados: {self._stats['frames_processed']} frames")

    def _process_detections(
        self, frame_id: int, detections: list[dict], process_start: float
    ) -> None:
        """Create detection event on state transition (no detection → detection)."""
        now = time.perf_counter()
        
        for det in detections:
            entity_type = det["class"]
            confidence = det["confidence"]
            
            # Verificar cooldown usando mutex
            with self._cooldown_lock:
                last_time = self._last_detection.get(entity_type, 0)
                if (now - last_time) < Config.COOLDOWN_S:
                    continue
                self._last_detection[entity_type] = now
            
            # Crear evento
            event = DetectionEvent(
                entity_type=entity_type,
                confidence=confidence,
                frame_id=frame_id
            )
            
            # Encolar evento para transmisión
            try:
                self._event_queue.put_nowait(event)
                log(f"[PROCESO] ✓ Evento creado y encolado: {entity_type} "
                    f"(confianza: {confidence:.2f}, queue_size: {self._event_queue.qsize()})")
            except queue.Full:
                log(f"[PROCESO] ⚠ Cola de eventos llena. Evento descartado.")

    # ─── THREAD 3: TRANSMISSION con Semáforo HTTP ──────────────────────────
    def _transmit_thread(self) -> None:
        """Transmit events with semaphore-controlled concurrent HTTP requests."""
        log("[ENVIO] Hilo iniciado con semáforo HTTP (max 3 simultáneos)")
        log(f"[ENVIO] Backend URL: {Config.BACKEND_URL}")
        last_retry = time.perf_counter()

        while self._running:
            try:
                # Obtener evento de la cola (timeout 0.1s)
                event = self._event_queue.get(timeout=0.1)
                log(f"[ENVIO] Evento extraído de cola (queue_size: {self._event_queue.qsize()})")
                
                # ═══════════════════════════════════════════════════════════════
                # SEMÁFORO 3: Adquirir semáforo de transmisión HTTP
                # Permite hasta 3 requests HTTP concurrentes al backend
                # ═══════════════════════════════════════════════════════════════
                acquisition_start = time.perf_counter()
                
                # Intentar adquirir con timeout de 5 segundos
                if self._http_transmission_semaphore.acquire(timeout=5.0):
                    wait_time = (time.perf_counter() - acquisition_start) * 1000
                    available = self._http_transmission_semaphore._value
                    
                    log(f"[ENVIO] ✓ Semáforo HTTP adquirido "
                        f"(disponibles: {available}/3, esperó: {wait_time:.1f}ms)")
                    
                    try:
                        # Enviar evento al backend
                        self._send_event(event)
                    finally:
                        # ═══════════════════════════════════════════════════════════════
                        # CRÍTICO: Siempre liberar semáforo HTTP
                        # ═══════════════════════════════════════════════════════════════
                        self._http_transmission_semaphore.release()
                        available = self._http_transmission_semaphore._value
                        log(f"[ENVIO] ✓ Semáforo HTTP liberado (disponibles: {available}/3)")
                else:
                    # Timeout esperando semáforo
                    with self._stats_lock:
                        self._stats["semaphore_timeouts"] += 1
                        self._stats["events_buffered"] += 1
                    
                    log(f"[ENVIO] ⚠ TIMEOUT esperando semáforo HTTP (5s). "
                        f"Evento almacenado en buffer local")
                    
                    # Guardar en buffer local para retry posterior
                    self._local_buffer.add(event)
                    
            except queue.Empty:
                pass

            # Reintentar eventos del buffer periódicamente
            now = time.perf_counter()
            if (now - last_retry) >= Config.RETRY_INTERVAL_S:
                last_retry = now
                self._flush_buffer()

        # Al terminar, intentar enviar eventos pendientes
        self._flush_buffer()
        log(f"[ENVIO] Hilo terminado. "
            f"Eventos enviados: {self._stats['events_sent']}, "
            f"en buffer: {self._stats['events_buffered']}")

    def _send_event(self, event: DetectionEvent) -> None:
        """Attempt to send event via HTTP POST with frame image."""
        latency_ms = (time.perf_counter() - event.capture_time) * 1000

        log(f"[ENVIO] → POST {Config.BACKEND_URL}")
        log(f"[ENVIO]   Entity: {event.entity_type}, "
            f"Confidence: {event.confidence:.2f}")
        log(f"[ENVIO]   Latencia: {latency_ms:.1f}ms "
            f"({'✓ OK' if latency_ms < Config.DEADLINE_INTRUSO_MS else '✗ DEADLINE EXCEDIDO'})")

        # Obtener frame más reciente
        frame_to_send = None
        with self._latest_frame_lock:
            if self._latest_frame is not None:
                frame_to_send = self._latest_frame.copy()

        # Enviar request HTTP
        success = simulated_http_post(
            event=event,
            frame=frame_to_send
        )

        if success:
            with self._stats_lock:
                self._stats["events_sent"] += 1
            log(f"[ENVIO] ✓ Evento enviado exitosamente (total: {self._stats['events_sent']})")
        else:
            log(f"[ENVIO] ✗ Fallo al enviar evento. Guardando en buffer local...")
            self._local_buffer.add(event)
            with self._stats_lock:
                self._stats["events_buffered"] += 1

    def _flush_buffer(self) -> None:
        """Retry sending events from local buffer."""
        pending = self._local_buffer.get_all()
        
        if not pending:
            return
            
        log(f"[BUFFER] Reintentando envío de {len(pending)} eventos pendientes...")
        
        # Intentar enviar eventos del buffer (sin usar semáforo para retries)
        for event in pending:
            success = simulated_http_post(
                event=event,
                frame=None  # No reenviar frames en retries
            )
            
            if success:
                self._local_buffer.remove(event)
                log(f"[BUFFER] ✓ Evento reenviado: {event.entity_type}")

    # ─── THREAD 4: VIDEO STREAMING con Semáforo ────────────────────────────
    def _streaming_thread(self) -> None:
        """Stream frames with semaphore ensuring single active stream."""
        if not Config.ENABLE_VIDEO_STREAMING:
            log("[STREAM] Streaming deshabilitado en config")
            return
        
        # ═══════════════════════════════════════════════════════════════
        # SEMÁFORO 4: Garantizar un solo stream activo
        # Si ya existe un stream, este thread no se inicia
        # ═══════════════════════════════════════════════════════════════
        if not self._video_streaming_semaphore.acquire(blocking=False):
            log("[STREAM] ✗ Ya existe un stream activo. Thread NO iniciado.")
            return
        
        try:
            log(f"[STREAM] ✓ Semáforo de streaming adquirido. "
                f"Iniciando stream a {Config.STREAM_FPS} FPS...")
            
            frame_interval = 1.0 / Config.STREAM_FPS
            last_send_time = time.perf_counter()
            frames_sent = 0
            
            while self._running:
                now = time.perf_counter()
                
                # Controlar FPS del stream
                if (now - last_send_time) < frame_interval:
                    time.sleep(0.01)
                    continue
                
                # Obtener frame más reciente para streaming
                with self._latest_frame_lock:
                    frame_to_stream = (self._latest_frame.copy() 
                                      if self._latest_frame is not None 
                                      else None)
                
                if frame_to_stream is not None:
                    success = send_stream_frame(frame_to_stream)
                    if success:
                        frames_sent += 1
                        if frames_sent % 30 == 0:  # Log cada segundo
                            log(f"[STREAM] Streaming activo... "
                                f"({frames_sent} frames enviados)")
                
                last_send_time = now
            
            log(f"[STREAM] Streaming terminado. Total: {frames_sent} frames")
            
        finally:
            # ═══════════════════════════════════════════════════════════════
            # CRÍTICO: Siempre liberar el semáforo de streaming
            # ═══════════════════════════════════════════════════════════════
            self._video_streaming_semaphore.release()
            log("[STREAM] ✓ Semáforo de streaming liberado")

    def display_frame_mainthread(self) -> None:
        """Display live frame in main thread (LIVE mode only) - loop until 'q' pressed."""
        if not Config.LIVE_MODE:
            return
        
        import cv2
        log("[DISPLAY] Iniciando loop de visualización (presiona 'q' para salir)")
        
        while self._running:
            frame, detections = _shared_frame.read()
            
            if frame is not None:
                # Agregar overlay con estadísticas
                display = frame.copy()
                
                # Mostrar estadísticas de semáforos
                with self._stats_lock:
                    stats_text = [
                        f"Capturados: {self._stats['frames_captured']}",
                        f"Descartados: {self._stats['frames_dropped']}",
                        f"Procesados: {self._stats['frames_processed']}",
                        f"Eventos: {self._stats['events_sent']}",
                        f"Buffer: {self._stats['events_buffered']}",
                        f"Sem Waits: {self._stats['semaphore_waits']}",
                    ]
                
                y_offset = 30
                for i, text in enumerate(stats_text):
                    cv2.putText(display, text, (10, y_offset + i*25),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Dibujar detecciones
                if detections:
                    display = draw_boxes(display, detections)
                
                cv2.imshow("Edge Module - Live Feed", display)
            
            # Esperar tecla (1ms) y salir si se presiona 'q'
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                log("[DISPLAY] Tecla 'q' presionada. Cerrando...")
                self._running = False
                break
            
            # Pequeña pausa para no saturar CPU
            time.sleep(0.01)
        
        log("[DISPLAY] Loop de visualización terminado")

    def start(self) -> list:
        """Start all threads with semaphore synchronization."""
        log("="*70)
        log("INICIANDO EDGE MODULE CON SEMÁFOROS")
        log("="*70)
        
        self._running = True
        
        threads = [
            threading.Thread(target=self._capture_thread, name="CaptureThread", daemon=True),
            threading.Thread(target=self._processing_thread, name="ProcessingThread", daemon=True),
            threading.Thread(target=self._transmit_thread, name="TransmitThread", daemon=True),
            threading.Thread(target=self._streaming_thread, name="StreamingThread", daemon=True),
        ]
        
        for t in threads:
            t.start()
            log(f"[MAIN] ✓ Thread iniciado: {t.name}")
        
        log("="*70)
        log("SISTEMA OPERANDO CON CONTROL DE SEMÁFOROS")
        log("="*70)
        
        return threads

    def stop(self) -> None:
        """Stop all threads and release all semaphores."""
        log("="*70)
        log("DETENIENDO SISTEMA...")
        log("="*70)
        
        self._running = False
        
        # Dar tiempo para que los threads terminen
        time.sleep(1.0)
        
        # Mostrar estadísticas finales
        with self._stats_lock:
            log("\nESTADÍSTICAS FINALES:")
            log(f"  Frames capturados: {self._stats['frames_captured']}")
            log(f"  Frames descartados: {self._stats['frames_dropped']}")
            log(f"  Frames procesados: {self._stats['frames_processed']}")
            log(f"  Eventos enviados: {self._stats['events_sent']}")
            log(f"  Eventos en buffer: {self._stats['events_buffered']}")
            log(f"  Esperas por semáforo: {self._stats['semaphore_waits']}")
            log(f"  Timeouts de semáforo: {self._stats['semaphore_timeouts']}")
        
        if Config.LIVE_MODE:
            import cv2
            cv2.destroyAllWindows()
        
        log("="*70)
        log("SISTEMA DETENIDO")
        log("="*70)
