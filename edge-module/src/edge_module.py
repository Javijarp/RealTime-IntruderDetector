"""Main EdgeModule Class — Multi-threaded Detection System."""

import threading
import time
import json
import queue

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
    """Main orchestrator for 3-thread detection system."""

    def __init__(self):
        """Initialize edge module with queues and buffers."""
        self._frame_queue: queue.Queue[tuple] = queue.Queue(maxsize=5)
        self._event_queue: queue.Queue[DetectionEvent] = queue.Queue(maxsize=10)
        self._local_buffer = LocalBuffer()
        self._last_detection: dict[str, float] = {}
        self._cooldown_lock = threading.Lock()
        self._frame_counter = 0
        self._running = False
        self._previous_detection_state: dict[str, bool] = {}  # Track if entity was detected last frame
        
        # Store latest frame to send with events
        self._latest_frame = None
        self._latest_frame_lock = threading.Lock()

    # ─── THREAD 1: CAPTURE (High Priority) ─────────────────────────
    def _capture_thread(self) -> None:
        """Capture frames from camera (LIVE) or simulate them."""
        if Config.LIVE_MODE:
            self._capture_live()
        else:
            self._capture_simulated()

    def _capture_live(self) -> None:
        """Capture frames from real camera using OpenCV."""
        import cv2

        cap = None
        camera_idx = Config.CAMERA_INDEX
        log(f"[CAPTURA] Intentando abrir cámara en índice {camera_idx}…")
        cap = cv2.VideoCapture(camera_idx)
        if cap.isOpened():
            ret, test_frame = cap.read()
            if ret and test_frame is not None:
                log(f"[CAPTURA] ✓ Cámara ABIERTA en índice {camera_idx}")
                log(
                    f"[CAPTURA]   Resolución: "
                    f"{test_frame.shape[1]}x{test_frame.shape[0]}"
                )
            else:
                log(
                    f"[CAPTURA] ✗ Cámara en índice {camera_idx} "
                    f"no captura frames"
                )
                cap.release()
                cap = None
        else:
            log(
                f"[CAPTURA] ✗ No se pudo abrir cámara "
                f"en índice {camera_idx}"
            )

        if cap is None or not cap.isOpened():
            log("[CAPTURA] ERROR: No se pudo abrir ninguna cámara disponible.")
            self._running = False
            return

        log("[CAPTURA] Leyendo frames en tiempo real…")
        frame_count = 0

        while self._running:
            self._frame_counter += 1
            frame_count += 1
            ret, frame = cap.read()
            if not ret:
                log("[CAPTURA] Error al leer frame. Reintentando en 1 s…")
                time.sleep(1.0)
                continue

            if frame_count % 30 == 0:
                log(
                    f"[CAPTURA] {frame_count} frames capturados. "
                    f"Frame actual: {self._frame_counter}"
                )

            try:
                self._frame_queue.put_nowait((self._frame_counter, frame))
            except queue.Full:
                log(f"[CAPTURA] Cola llena. Frame {self._frame_counter} descartado.")

        cap.release()
        log("[CAPTURA] Cámara liberada. Hilo terminado.")

    def _capture_simulated(self) -> None:
        """Simulate camera capture at 30 FPS."""
        log("[CAPTURA] Hilo iniciado. Simulando cámara a 30 FPS…")
        while self._running:
            self._frame_counter += 1
            try:
                self._frame_queue.put_nowait((self._frame_counter, None))
            except queue.Full:
                log(
                    "[CAPTURA] Cola de frames llena. Frame descartado.",
                    f"frame_id={self._frame_counter}",
                )
            time.sleep(Config.FRAME_INTERVAL_S)
        log("[CAPTURA] Hilo terminado.")

    # ─── THREAD 2: PROCESSING (Medium Priority) ────────────────────
    def _processing_thread(self) -> None:
        """Process frames: YOLO inference + filtering + cooldown."""
        log("[PROCESO] Hilo iniciado. Esperando frames…")

        while self._running:
            try:
                frame_id, frame = self._frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            # Store latest frame to send with events
            if frame is not None:
                with self._latest_frame_lock:
                    self._latest_frame = frame.copy()

            process_start = time.perf_counter()
            detections = run_yolo_inference(frame_id, frame)

            if Config.LIVE_MODE and frame is not None:
                _shared_frame.write(frame, detections)

            # Track state change: no detection → detection
            has_detections = len(detections) > 0
            
            # Update previous state and check for transition
            had_detections_before = any(self._previous_detection_state.values())
            
            if not detections:
                # No detections in this frame
                if had_detections_before:
                    log(f"[PROCESO] Frame {frame_id}: Transición detectada (con → sin detección)")
                self._previous_detection_state.clear()
                continue

            # Only process detections if transitioning from no-detection to detection
            if not had_detections_before:
                log(f"[PROCESO] Frame {frame_id}: TRANSICIÓN DE ESTADO - sin detección → CON DETECCIÓN")
                self._process_detections(frame_id, detections, process_start)
                # Update state to track that we now have detections
                for det in detections:
                    self._previous_detection_state[det["class"]] = True
            else:
                log(f"[PROCESO] Frame {frame_id}: Entidad(es) aún presente(s). Sin nuevo evento.")

        log("[PROCESO] Hilo terminado.")

    def _process_detections(
        self, frame_id: int, detections: list[dict], process_start: float
    ) -> None:
        """Create detection event on state transition (no detection → detection)."""
        now = time.perf_counter()
        
        # Use the first valid detection to create the event
        event_created = False
        
        for det in detections:
            cls = det["class"]
            confidence = det["confidence"]

            if confidence < Config.CONFIDENCE_THRESHOLD:
                log(
                    f"[PROCESO] Frame {frame_id}: {cls} descartado "
                    f"(confianza {confidence} < {Config.CONFIDENCE_THRESHOLD})"
                )
                continue

            # Only create ONE event for the state transition
            if not event_created:
                event = DetectionEvent(cls, confidence, frame_id)
                event.capture_time = process_start

                try:
                    self._event_queue.put_nowait(event)
                    log(
                        f"[PROCESO] Frame {frame_id}: EVENTO ENVIADO - {cls} detectado "
                        f"(conf={confidence:.3f})"
                    )
                    event_created = True
                except queue.Full:
                    self._local_buffer.push(event)
                    log(
                        f"[PROCESO] Frame {frame_id}: Cola de envío llena. "
                        f"Evento al buffer local."
                    )
                    event_created = True
            else:
                # Additional detections in same frame - log but don't create new event
                log(
                    f"[PROCESO] Frame {frame_id}: {cls} también detectado "
                    f"(conf={confidence:.3f}), pero evento ya creado."
                )

    # ─── THREAD 3: TRANSMISSION (Low Priority) ────────────────────
    def _transmit_thread(self) -> None:
        """Transmit events: HTTP POST + buffer retry logic."""
        log("[ENVIO ] Hilo iniciado. Esperando eventos…")
        last_retry = time.perf_counter()

        while self._running:
            try:
                event = self._event_queue.get(timeout=0.1)
                self._send_event(event)
            except queue.Empty:
                pass

            now = time.perf_counter()
            if (now - last_retry) >= Config.RETRY_INTERVAL_S:
                last_retry = now
                self._flush_buffer()

        self._flush_buffer()
        log("[ENVIO ] Hilo terminado.")

    def _send_event(self, event: DetectionEvent) -> None:
        """Attempt to send event via HTTP POST with frame image."""
        payload = event.to_dict()
        latency_ms = (time.perf_counter() - event.capture_time) * 1000

        log(f"[ENVIO ] → POST {Config.BACKEND_URL}")
        log(f"[ENVIO ]   Payload : {json.dumps(payload, indent=None)}")
        log(
            f"[ENVIO ]   Latencia desde captura: {latency_ms:.1f} ms "
            f"(deadline "
            f"{'✓ OK' if latency_ms < Config.DEADLINE_INTRUSO_MS else '✗ EXCEDIDO'})"
        )

        # Get latest frame to send with event
        with self._latest_frame_lock:
            frame_to_send = self._latest_frame.copy() if self._latest_frame is not None else None

        success = simulated_http_post(event, frame=frame_to_send)

        if success:
            event.sent = True
            log(f"[ENVIO ]   Estado   : ✓ Enviado exitosamente")
        else:
            log(
                f"[ENVIO ]   Estado   : ✗ Fallo de red — "
                f"guardado en buffer local"
            )
            self._local_buffer.push(event)

    def _flush_buffer(self) -> None:
        """Retry sending all buffered events."""
        pending = self._local_buffer.flush()
        if not pending:
            return

        log(
            f"[ENVIO ] ── Reintento de buffer: {len(pending)} "
            f"evento(s) pendientes ──"
        )
        now = time.perf_counter()
        
        # Get latest frame for buffer retries
        with self._latest_frame_lock:
            frame_to_send = self._latest_frame.copy() if self._latest_frame is not None else None

        for event in pending:
            age_s = now - event.capture_time
            if age_s > Config.EVENT_EXPIRY_S:
                log(
                    f"[ENVIO ]   Evento expirado (edad {age_s:.0f} s). "
                    f"Descartado."
                )
                continue

            success = simulated_http_post(event, frame=frame_to_send)

            if success:
                event.sent = True
                log(
                    f"[ENVIO ]   Reintento ✓ — {event.entity_type} "
                    f"frame_id={event.frame_id}"
                )
            else:
                self._local_buffer.push(event)
                log(f"[ENVIO ]   Reintento ✗ — Devuesto al buffer.")

    # ─── THREAD 4: VIDEO STREAMING (Continuous) ────────────────────
    def _streaming_thread(self) -> None:
        """Continuously stream frames to backend for live preview."""
        if not Config.ENABLE_VIDEO_STREAMING:
            log("[STREAM] Video streaming disabled in config")
            return
            
        log(f"[STREAM] Hilo iniciado. Enviando frames a {Config.STREAM_FPS} FPS...")
        frame_interval = 1.0 / Config.STREAM_FPS
        last_send_time = time.perf_counter()
        frames_sent = 0
        last_log_time = time.perf_counter()
        
        while self._running:
            now = time.perf_counter()
            
            # Rate limiting
            if (now - last_send_time) < frame_interval:
                time.sleep(0.01)
                continue
            
            # Get latest frame
            with self._latest_frame_lock:
                frame_to_stream = self._latest_frame.copy() if self._latest_frame is not None else None
            
            if frame_to_stream is not None:
                success = send_stream_frame(frame_to_stream)
                if success:
                    frames_sent += 1
                    
            last_send_time = now
            
            # Log stats every 5 seconds
            if (now - last_log_time) >= 5.0:
                fps_actual = frames_sent / (now - last_log_time)
                log(f"[STREAM] Streaming stats: {frames_sent} frames sent, {fps_actual:.1f} FPS")
                frames_sent = 0
                last_log_time = now
        
        log("[STREAM] Hilo terminado.")

    def display_frame_mainthread(self) -> None:
        """Display annotated frames in OpenCV window (main thread)."""
        import cv2

        WINDOW = "Sistema de Seguridad — Detección en Tiempo Real"
        frame_count = 0
        last_frame_time = time.perf_counter()

        log("[DISPLAY] Ventana abierta. Presiona 'q' para cerrar.")

        while self._running:
            frame, detections = _shared_frame.read()
            if frame is None:
                time.sleep(0.01)
                continue

            frame_count += 1

            if frame_count % 30 == 0:
                now = time.perf_counter()
                fps = 30 / (now - last_frame_time)
                log(
                    f"[DISPLAY] FPS: {fps:.1f} | "
                    f"Detecciones: {len(detections)}"
                )
                last_frame_time = now

            annotated = draw_boxes(frame.copy(), detections)
            cv2.imshow(WINDOW, annotated)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                log("[DISPLAY] Usuario presionó 'q'. Cerrando…")
                self._running = False
                break

        cv2.destroyAllWindows()
        log("[DISPLAY] Ventana cerrada.")

    def start(self) -> list:
        """Start all threads (capture, processing, transmission, streaming)."""
        self._running = True

        threads = [
            threading.Thread(
                target=self._capture_thread,
                name="Captura.........",
                daemon=True,
            ),
            threading.Thread(
                target=self._processing_thread,
                name="Procesamiento....",
                daemon=True,
            ),
            threading.Thread(
                target=self._transmit_thread,
                name="Transmision.....",
                daemon=True,
            ),
        ]
        
        # Add streaming thread if enabled
        if Config.ENABLE_VIDEO_STREAMING:
            threads.append(
                threading.Thread(
                    target=self._streaming_thread,
                    name="Streaming.......",
                    daemon=True,
                )
            )

        for t in threads:
            t.start()

        modo = (
            "LIVE (cámara + ventana)"
            if Config.LIVE_MODE
            else "SIMULACIÓN"
        )
        streaming_status = "Streaming ON" if Config.ENABLE_VIDEO_STREAMING else "Streaming OFF"
        log(
            f"[MAIN  ] Sistema Edge iniciado — modo {modo}, {streaming_status}. "
            f"Presiona Ctrl+C para detener."
        )
        return threads

    def stop(self) -> None:
        """Stop all threads gracefully."""
        self._running = False
