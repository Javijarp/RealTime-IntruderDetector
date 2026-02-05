"""
============================================================
  Sistema de Seguridad — Módulo Edge (Captura & Detección)
  Universidad Iberoamericana – UNIBE
  Ingeniería de Software en Tiempo Real
============================================================

Arquitectura (3 hilos según el Plan de Diseño):
  Thread 1 — Captura      (Alta prioridad)   → lee frames, los mete en cola
  Thread 2 — Procesamiento (Media prioridad) → YOLO → genera eventos
  Thread 3 — Transmisión   (Baja prioridad)  → "envía" al backend (simulate)

Reglas clave:
  • Solo reporta "alguien apareció" (Person) o "perro detectado" (Dog).
    El backend es responsable de identificar quién es.
  • Cooldown de 1 segundo por tipo de entidad: no se saturan
    los eventos con la misma clase.
  • Si la "red cae" (se simula con una bandera), los eventos se
    acumulan en un buffer local (máx 100). Se reintenta cada 5 s.
  • Todas las marcas de tiempo se miden desde el inicio del frame
    para poder validar los deadlines del documento.
"""

import threading
import time
import json
import queue
import random
from datetime import datetime, timezone
from collections import deque
from enum import Enum


# ──────────────────────────────────────────────
# 1.  CONFIGURACIÓN CENTRALIZADA
# ──────────────────────────────────────────────
class Config:
    # ── modo de ejecución ──────────────────────────────────────────
    # False → todo simulado, sin cámara ni ventana.
    # True  → abre la cámara, muestra bounding boxes en tiempo real.
    LIVE_MODE: bool = True

    # Frecuencia de captura simulada (solo cuando LIVE_MODE = False)
    FRAME_INTERVAL_S: float = 0.033          # 30 FPS

    # Deadline end-to-end para un evento crítico (intruso)
    DEADLINE_INTRUSO_MS: int = 200

    # Cooldown mínimo entre eventos de la misma clase (1 s)
    COOLDOWN_S: float = 1.0

    # Capacidad máxima del buffer local cuando la red falla
    BUFFER_MAX: int = 100

    # Intervalo de reintento cuando el backend no responde (5 s)
    RETRY_INTERVAL_S: float = 5.0

    # Tiempo que un evento puede estar en el buffer antes de expirar (1 h)
    EVENT_EXPIRY_S: float = 3600.0

    # Confianza mínima que YOLO debe devolver para considerar la detección
    CONFIDENCE_THRESHOLD: float = 0.6

    # URL simulada del backend (no se usa para conexión real)
    BACKEND_URL: str = "http://localhost:8080/api/events"

    # Simular fallo de red? (ponlo en True para ver el buffer en acción)
    SIMULATE_NETWORK_FAILURE: bool = False

    # Índice de cámara a usar en modo LIVE (0 = default, prueba 1, 2, 3 si no funciona)
    CAMERA_INDEX: int = 0

    # ── IDs de clase en el modelo YOLOv8 coco ─────────────────────
    # (se usan solo cuando LIVE_MODE = True)
    YOLO_CLASS_PERSON: int = 0
    YOLO_CLASS_DOG:    int = 16


# ──────────────────────────────────────────────
# 2.  ESTADOS DEL GESTOR DE DETECCIÓN (Máquina de Estados)
#     Idle → Detecting → Sending → Cooldown → Idle
# ──────────────────────────────────────────────
class DetectionState(Enum):
    IDLE       = "IDLE"
    DETECTING  = "DETECTING"
    SENDING    = "SENDING"
    COOLDOWN   = "COOLDOWN"


# ──────────────────────────────────────────────
# 3.  MODELO DE EVENTO (lo que se "envía" al backend)
# ──────────────────────────────────────────────
class DetectionEvent:
    """Representa un único evento de detección listo para transmitir."""

    def __init__(self, entity_type: str, confidence: float, frame_id: int):
        self.id            = id(self)                          # ID único en memoria
        self.entity_type   = entity_type                      # "Person" | "Dog"
        self.confidence    = round(confidence, 3)
        self.frame_id      = frame_id
        self.timestamp     = datetime.now(timezone.utc).isoformat()
        self.capture_time  = time.perf_counter()              # Para medir latencia
        self.sent          = False

    def to_dict(self) -> dict:
        return {
            "event_id":    self.id,
            "entity_type": self.entity_type,
            "confidence":  self.confidence,
            "frame_id":    self.frame_id,
            "timestamp":   self.timestamp,
        }


# ──────────────────────────────────────────────
# 4.  BUFFER LOCAL (tolerancia a fallos de red)
# ──────────────────────────────────────────────
class LocalBuffer:
    """
    Cola FIFO con capacidad máxima.  Si se llena, descarta el evento
    más antiguo (como indica el plan: política FIFO, máx 100).
    Thread-safe via Lock interno.
    """

    def __init__(self, max_size: int = Config.BUFFER_MAX):
        self._buffer: deque[DetectionEvent] = deque(maxlen=max_size)
        self._lock   = threading.Lock()

    # ── escritura ──
    def push(self, event: DetectionEvent) -> None:
        with self._lock:
            if len(self._buffer) == self._buffer.maxlen:
                dropped = self._buffer[0]                     # el más viejo
                log("[BUFFER] Cola llena. Evento descartado:",
                    f"frame_id={dropped.frame_id} "
                    f"type={dropped.entity_type} "
                    f"ts={dropped.timestamp}")
            self._buffer.append(event)
            log("[BUFFER] Evento almacenado localmente.",
                f"Pendientes en buffer: {len(self._buffer)}")

    # ── lectura (consume todos los pendientes) ──
    def flush(self) -> list[DetectionEvent]:
        with self._lock:
            pending = list(self._buffer)
            self._buffer.clear()
            return pending

    # ── consulta ──
    def pending_count(self) -> int:
        with self._lock:
            return len(self._buffer)


# ──────────────────────────────────────────────
# 5.  UTILIDAD DE LOG (formato uniforme con timestamp)
# ──────────────────────────────────────────────
_log_lock = threading.Lock()

def log(*parts: str) -> None:
    """Imprime una línea de log con marca de tiempo y thread actual."""
    ts      = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thread  = threading.current_thread().name
    msg     = " ".join(parts)
    with _log_lock:
        print(f"[{ts}] [{thread:.<22}] {msg}")


# ──────────────────────────────────────────────
# 6.  FRAME COMPARTIDO (solo en modo LIVE)
#     El hilo de Captura escribe aquí; el hilo de Display lo lee.
#     Un Lock evita que display lea un frame a mitad de escritura.
# ──────────────────────────────────────────────
class SharedFrame:
    """Contenedor thread-safe para el último frame + sus bboxes."""
    def __init__(self):
        self.frame       = None          # numpy array BGR
        self.detections  = []            # lista de dicts {class, confidence, box}
        self._lock       = threading.Lock()

    def write(self, frame, detections: list[dict]) -> None:
        with self._lock:
            self.frame      = frame
            self.detections = detections

    def read(self):
        with self._lock:
            return self.frame, list(self.detections)

# Instancia global; se usa solo cuando LIVE_MODE = True
_shared_frame = SharedFrame()


# ──────────────────────────────────────────────
# 7.  INFERENCIA YOLO  (simulada o real)
# ──────────────────────────────────────────────
def run_yolo_inference(frame_id: int, frame=None) -> list[dict]:
    """
    LIVE_MODE = False  →  genera detecciones ficticias (sin cámara).
    LIVE_MODE = True   →  ejecuta YOLOv8 sobre 'frame' y retorna
                          solo Person / Dog con sus bounding boxes.
    """
    if not Config.LIVE_MODE:
        # ── modo simulado (igual que antes) ──
        roll = random.random()
        if roll < 0.60:
            detections = [{"class": "Person",
                           "confidence": round(random.uniform(0.65, 0.98), 3)}]
        elif roll < 0.80:
            detections = [{"class": "Dog",
                           "confidence": round(random.uniform(0.70, 0.95), 3)}]
        elif roll < 0.90:
            detections = [
                {"class": "Person", "confidence": round(random.uniform(0.65, 0.98), 3)},
                {"class": "Dog",    "confidence": round(random.uniform(0.70, 0.95), 3)},
            ]
        else:
            detections = []
        time.sleep(random.uniform(0.020, 0.045))   # simula tiempo de inferencia
        return detections

    # ── modo LIVE: inferencia real con YOLOv8 ──
    from ultralytics import YOLO as _YOLO          # import lazy: solo cuando hace falta

    # Modelo singleton (se carga una sola vez)
    if not hasattr(run_yolo_inference, "_model"):
        log("[YOLO  ] Cargando modelo yolov8n.pt …")
        run_ylo_inference_model = _YOLO("yolov8n.pt")   # nano: más rápido en edge
        run_yolo_inference._model = run_ylo_inference_model
        log("[YOLO  ] Modelo cargado.")

    results = run_yolo_inference._model(frame, verbose=False)[0]

    detections = []
    for box in results.boxes:
        cls_id = int(box.cls[0].item())
        if cls_id not in (Config.YOLO_CLASS_PERSON, Config.YOLO_CLASS_DOG):
            continue                                      # solo Person y Dog

        conf = round(float(box.conf[0].item()), 3)
        if conf < Config.CONFIDENCE_THRESHOLD:
            continue

        # box.xyxy → [[x1, y1, x2, y2]]
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
        label = "Person" if cls_id == Config.YOLO_CLASS_PERSON else "Dog"

        detections.append({
            "class":      label,
            "confidence": conf,
            "box":        (int(x1), int(y1), int(x2), int(y2)),
        })

    return detections


# ──────────────────────────────────────────────
# 8.  DIBUJADOR DE BOUNDING BOXES (solo modo LIVE)
# ──────────────────────────────────────────────
def draw_boxes(frame, detections: list[dict]):
    """
    Dibuja rectángulos y etiquetas sobre el frame.
    Verde = Dog, Azul = Person.  Retorna el frame anotado.
    """
    import cv2
    COLORS = {"Person": (255, 50, 50), "Dog": (50, 220, 50)}   # BGR

    for det in detections:
        color = COLORS.get(det["class"], (200, 200, 200))
        x1, y1, x2, y2 = det["box"]
        conf            = det["confidence"]
        label           = f'{det["class"]} {conf}'

        # rectángulo
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness=2)

        # fondo de la etiqueta
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(frame, (x1, y1 - th - 4), (x1 + tw + 4, y1), color, -1)

        # texto
        cv2.putText(frame, label, (x1 + 2, y1 - 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1,
                    cv2.LINE_AA)

    return frame


# ──────────────────────────────────────────────
# 7.  SIMULADOR DE HTTP POST (no envía nada por red)
# ──────────────────────────────────────────────
def simulated_http_post(event: DetectionEvent) -> bool:
    """
    Simula el envío HTTP POST al backend.
    Imprime el payload como si fuera la llamada de red.
    Retorna False si Config.SIMULATE_NETWORK_FAILURE está activo.
    """
    if Config.SIMULATE_NETWORK_FAILURE:
        return False                                          # simular caída

    # Simula latencia de red (5-20 ms)
    time.sleep(random.uniform(0.005, 0.020))
    return True                                               # éxito


# ──────────────────────────────────────────────
# 8.  CLASE PRINCIPAL: EDGE MODULE
#     Contiene los 3 hilos y la lógica de cooldown / buffer.
# ──────────────────────────────────────────────
class EdgeModule:
    def __init__(self):
        # Colas inter-hilo (thread-safe por diseño de queue.Queue)
        self._frame_queue: queue.Queue[tuple]           = queue.Queue(maxsize=5)
        self._event_queue: queue.Queue[DetectionEvent]  = queue.Queue(maxsize=10)

        # Buffer local para eventos no enviados
        self._local_buffer = LocalBuffer()

        # Cooldown: guarda el timestamp de la última detección por clase
        self._last_detection: dict[str, float] = {}
        self._cooldown_lock  = threading.Lock()

        # Contador de frames (para trazabilidad)
        self._frame_counter = 0

        # Bandera de parada
        self._running = False

    # ─── HILO 1: CAPTURA (Alta prioridad) ────────────────────────
    def _capture_thread(self) -> None:
        """
        LIVE_MODE = False  →  simula frames a 30 FPS (solo meter IDs en cola).
        LIVE_MODE = True   →  abre cv2.VideoCapture, lee frames reales,
                              los mete en la cola como (frame_id, frame).
        """
        if Config.LIVE_MODE:
            import cv2
            
            # Intentar abrir cámara con múltiples índices (evitar iPhone como index 0)
            cap = None
            for camera_idx in [0, 1, 2, 3]:
                log(f"[CAPTURA] Intentando abrir cámara en índice {camera_idx}…")
                cap = cv2.VideoCapture(camera_idx)
                if cap.isOpened():
                    # Verificar que realmente se abrió correctamente
                    ret, test_frame = cap.read()
                    if ret and test_frame is not None:
                        log(f"[CAPTURA] ✓ Cámara ABIERTA en índice {camera_idx}")
                        log(f"[CAPTURA]   Resolución: {test_frame.shape[1]}x{test_frame.shape[0]}")
                        break
                    else:
                        log(f"[CAPTURA] ✗ Cámara en índice {camera_idx} no captura frames")
                        cap.release()
                        cap = None
                else:
                    log(f"[CAPTURA] ✗ No se pudo abrir cámara en índice {camera_idx}")
            
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
                
                # Log cada 30 frames
                if frame_count % 30 == 0:
                    log(f"[CAPTURA] {frame_count} frames capturados. Frame actual: {self._frame_counter}")
                
                try:
                    self._frame_queue.put_nowait((self._frame_counter, frame))
                except queue.Full:
                    log(f"[CAPTURA] Cola llena. Frame {self._frame_counter} descartado.")

            cap.release()
            log("[CAPTURA] Cámara liberada. Hilo terminado.")

        else:
            # ── modo simulado ──
            log("[CAPTURA] Hilo iniciado. Simulando cámara a 30 FPS…")
            while self._running:
                self._frame_counter += 1
                try:
                    self._frame_queue.put_nowait((self._frame_counter, None))
                except queue.Full:
                    log("[CAPTURA] Cola de frames llena. Frame descartado.",
                        f"frame_id={self._frame_counter}")
                time.sleep(Config.FRAME_INTERVAL_S)
            log("[CAPTURA] Hilo terminado.")

    # ─── HILO 2: PROCESAMIENTO (Media prioridad) ─────────────────
    def _processing_thread(self) -> None:
        """
        Consume frames de la cola, ejecuta YOLO (simulado o real),
        aplica el cooldown y mete eventos válidos en la cola de envío.
        En modo LIVE también escribe el frame anotado en SharedFrame.
        """
        log("[PROCESO] Hilo iniciado. Esperando frames…")

        while self._running:
            try:
                frame_id, frame = self._frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            process_start = time.perf_counter()

            # ── inferencia ──
            detections = run_yolo_inference(frame_id, frame)

            # ── en modo LIVE: guardar frame + detecciones para el display ──
            if Config.LIVE_MODE and frame is not None:
                _shared_frame.write(frame, detections)

            if not detections:
                log(f"[PROCESO] Frame {frame_id}: Sin detecciones.")
                continue

            # ── filtrar por confianza y aplicar cooldown ──
            now = time.perf_counter()

            for det in detections:
                cls        = det["class"]
                confidence = det["confidence"]

                # 1) Filtro de confianza (redundante en LIVE pero por seguridad)
                if confidence < Config.CONFIDENCE_THRESHOLD:
                    log(f"[PROCESO] Frame {frame_id}: {cls} descartado "
                        f"(confianza {confidence} < {Config.CONFIDENCE_THRESHOLD})")
                    continue

                # 2) Cooldown por entidad
                with self._cooldown_lock:
                    ultima = self._last_detection.get(cls, 0.0)
                    if (now - ultima) < Config.COOLDOWN_S:
                        log(f"[PROCESO] Frame {frame_id}: {cls} en cooldown "
                            f"(quedan {Config.COOLDOWN_S - (now - ultima):.2f} s)")
                        continue
                    self._last_detection[cls] = now

                # 3) Crear evento y encolarlo para transmisión
                event = DetectionEvent(cls, confidence, frame_id)
                event.capture_time = process_start

                try:
                    self._event_queue.put_nowait(event)
                    log(f"[PROCESO] Frame {frame_id}: {cls} detectado "
                        f"(conf={confidence}). Evento encolado para envío.")
                except queue.Full:
                    self._local_buffer.push(event)
                    log(f"[PROCESO] Frame {frame_id}: Cola de envío llena. "
                        f"Evento al buffer local.")

        log("[PROCESO] Hilo terminado.")

    # ─── HILO 3: TRANSMISIÓN (Baja prioridad) ────────────────────
    def _transmit_thread(self) -> None:
        """
        Consume eventos de la cola, simula el HTTP POST.
        Si falla, los mete en el buffer local y cada 5 s
        intenta vaciar el buffer (retry logic).
        """
        log("[ENVIO ] Hilo iniciado. Esperando eventos…")
        last_retry = time.perf_counter()

        while self._running:

            # ── A) Intentar enviar un evento nuevo ──
            try:
                event = self._event_queue.get(timeout=0.1)
                self._send_event(event)
            except queue.Empty:
                pass                                          # nada que enviar aún

            # ── B) Retry del buffer cada 5 s ──
            now = time.perf_counter()
            if (now - last_retry) >= Config.RETRY_INTERVAL_S:
                last_retry = now
                self._flush_buffer()

        # Al parar, intentar vaciar lo que quede en el buffer
        self._flush_buffer()
        log("[ENVIO ] Hilo terminado.")

    # ─── helpers de transmisión ───────────────────────────────────
    def _send_event(self, event: DetectionEvent) -> None:
        """Intenta 'enviar' un evento. Si falla, lo mete en buffer."""
        payload = event.to_dict()
        latency_ms = (time.perf_counter() - event.capture_time) * 1000

        log(f"[ENVIO ] → POST {Config.BACKEND_URL}")
        log(f"[ENVIO ]   Payload : {json.dumps(payload, indent=None)}")
        log(f"[ENVIO ]   Latencia desde captura: {latency_ms:.1f} ms "
            f"(deadline {'✓ OK' if latency_ms < Config.DEADLINE_INTRUSO_MS else '✗ EXCEDIDO'})")

        success = simulated_http_post(event)

        if success:
            event.sent = True
            log(f"[ENVIO ]   Estado   : ✓ Enviado exitosamente")
        else:
            log(f"[ENVIO ]   Estado   : ✗ Fallo de red — guardado en buffer local")
            self._local_buffer.push(event)

    def _flush_buffer(self) -> None:
        """Intenta reenviar todos los eventos pendientes del buffer."""
        pending = self._local_buffer.flush()
        if not pending:
            return

        log(f"[ENVIO ] ── Reintento de buffer: {len(pending)} evento(s) pendientes ──")
        now = time.perf_counter()

        for event in pending:
            # Descartar eventos expirados (> 1 hora)
            age_s = now - event.capture_time
            if age_s > Config.EVENT_EXPIRY_S:
                log(f"[ENVIO ]   Evento expirado (edad {age_s:.0f} s). Descartado.")
                continue

            # Reintento
            payload  = event.to_dict()
            success  = simulated_http_post(event)

            if success:
                event.sent = True
                log(f"[ENVIO ]   Reintento ✓ — {event.entity_type} "
                    f"frame_id={event.frame_id}")
            else:
                # Sigue fallando → vuelve al buffer
                self._local_buffer.push(event)
                log(f"[ENVIO ]   Reintento ✗ — Devuesto al buffer.")

    def display_frame_mainthread(self) -> None:
        """
        Método para llamar desde el main thread.
        Muestra frames con detecciones en una ventana OpenCV.
        """
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
            
            # Log cada 30 frames
            if frame_count % 30 == 0:
                now = time.perf_counter()
                fps = 30 / (now - last_frame_time)
                log(f"[DISPLAY] FPS: {fps:.1f} | Detecciones: {len(detections)}")
                last_frame_time = now

            # Dibujar boxes sobre una copia
            annotated = draw_boxes(frame.copy(), detections)
            
            # Mostrar en ventana
            cv2.imshow(WINDOW, annotated)

            # Detectar tecla 'q' (no-bloqueante)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                log("[DISPLAY] Usuario presionó 'q'. Cerrando…")
                self._running = False
                break

        cv2.destroyAllWindows()
        log("[DISPLAY] Ventana cerrada.")

    def start(self) -> list:
        self._running = True

        threads = [
            threading.Thread(target=self._capture_thread,     name="Captura.........",  daemon=True),
            threading.Thread(target=self._processing_thread,  name="Procesamiento....", daemon=True),
            threading.Thread(target=self._transmit_thread,    name="Transmision.....",  daemon=True),
        ]

        for t in threads:
            t.start()

        modo = "LIVE (cámara + ventana)" if Config.LIVE_MODE else "SIMULACIÓN"
        log(f"[MAIN  ] Sistema Edge iniciado — modo {modo}. Presiona Ctrl+C para detener.")
        return threads

    def stop(self) -> None:
        self._running = False


# ──────────────────────────────────────────────
# 9.  ENTRY POINT
# ──────────────────────────────────────────────
if __name__ == "__main__":
    modo_texto = "LIVE (cámara real + ventana)" if Config.LIVE_MODE else "SIMULACIÓN (sin cámara ni red)"

    print("=" * 70)
    print("  MÓDULO EDGE — Sistema de Seguridad con Detección en Tiempo Real")
    print(f"  Modo: {modo_texto}")
    print("=" * 70)
    print()
    print("  Config actual:")
    print(f"    • Modo                  : {'LIVE' if Config.LIVE_MODE else 'SIMULADO'}")
    print(f"    • FPS                   : {int(1 / Config.FRAME_INTERVAL_S)} {'(simulado)' if not Config.LIVE_MODE else '(cámara real)'}")
    print(f"    • Deadline intruso      : {Config.DEADLINE_INTRUSO_MS} ms")
    print(f"    • Cooldown por entidad  : {Config.COOLDOWN_S} s")
    print(f"    • Buffer máximo         : {Config.BUFFER_MAX} eventos")
    print(f"    • Fallo de red simulado : {Config.SIMULATE_NETWORK_FAILURE}")
    print(f"    • Backend URL (sim)     : {Config.BACKEND_URL}")
    print()

    if Config.LIVE_MODE:
        print("  LIVE: Se abrirá una ventana con la cámara.")
        print("        Azul  = Person | Verde = Dog")
        print("        Presiona 'q' en la ventana para cerrarla.")
    else:
        print("  SIMULADO: No se abre cámara ni ventana.")
        print("  TIPs:")
        print("    • Para ver la cámara real, cambia Config.LIVE_MODE = True")
        print("      (requiere: pip install opencv-python ultralytics)")
        print("    • Para ver el buffer en acción, cambia")
        print("      Config.SIMULATE_NETWORK_FAILURE = True")

    print("=" * 70)
    print()

    edge = EdgeModule()
    threads = edge.start()

    log("[MAIN  ] Sistema iniciado. Esperando datos de cámara…")
    print()
    print("  Ventana abierta. Presiona 'q' para cerrar.")
    print()

    try:
        # Ejecutar display en el main thread (requerido por macOS)
        edge.display_frame_mainthread()
    except KeyboardInterrupt:
        print()
        log("[MAIN  ] Ctrl+C recibido.")
    except Exception as e:
        log(f"[MAIN  ] Error en ventana: {e}")
    finally:
        log("[MAIN  ] Señal de parada. Cerrando hilos…")
        edge.stop()
        for t in threads:
            t.join(timeout=3)
        log("[MAIN  ] Sistema Edge apagado limpiamente.")