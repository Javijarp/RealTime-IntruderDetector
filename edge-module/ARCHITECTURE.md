# Edge Module Architecture

## Overview

The Edge Module is a lightweight, multi-threaded Python application that runs on edge devices (cameras, IoT devices) to detect persons and dogs in real-time using YOLOv8. It implements a 3-thread architecture with built-in network failure tolerance and local buffering.

**Institution:** Universidad Iberoamericana (UNIBE)  
**Course:** Ingeniería de Software en Tiempo Real

---

## 3-Thread Design

```
┌─────────────────────────────────────────────────────────────┐
│                      EDGE MODULE                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Thread 1: CAPTURA (High Priority)                         │
│  ├─ Reads frames from camera (LIVE mode)                   │
│  ├─ Or simulates frames at 30 FPS (SIMULATION mode)        │
│  └─ Enqueues frames → Frame Queue (maxsize=5)             │
│                                                             │
│  Thread 2: PROCESAMIENTO (Medium Priority)                 │
│  ├─ Dequeues frames from Frame Queue                       │
│  ├─ Runs YOLO inference (Person/Dog detection)            │
│  ├─ Applies confidence threshold (0.6)                     │
│  ├─ Enforces cooldown (1s per entity type)                │
│  └─ Enqueues valid events → Event Queue (maxsize=10)      │
│                                                             │
│  Thread 3: TRANSMISIÓN (Low Priority)                      │
│  ├─ Dequeues events from Event Queue                       │
│  ├─ Simulates HTTP POST to backend                         │
│  ├─ On failure: buffers locally (max 100 events)          │
│  ├─ Retries every 5s (buffer flush)                        │
│  └─ Drops expired events (>1 hour old)                     │
│                                                             │
│  Display (Main Thread)                                      │
│  └─ Shows annotated frames in OpenCV window                │
│     (LIVE mode only, requires macOS/Linux with display)    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Thread Responsibilities

### Thread 1: CAPTURA (Capture)

**Methods:**

- `_capture_thread()` — Dispatcher (calls live or simulated)
- `_capture_live()` — Real camera capture (OpenCV)
- `_capture_simulated()` — Generate dummy frames at 30 FPS

**Output Queue:** `_frame_queue` (maxsize=5)

**Behavior:**

- Iterates through camera indices (0, 1, 2, 3) until one opens successfully
- On success, continuously reads frames and enqueues them
- On queue full, drops frames with log message
- Dies gracefully when `_running = False`

**Logging Prefix:** `[CAPTURA]`

---

### Thread 2: PROCESAMIENTO (Processing)

**Methods:**

- `_processing_thread()` — Main loop
- `_process_detections(frame_id, detections, process_start)` — Filtering logic

**Input Queue:** `_frame_queue`  
**Output Queue:** `_event_queue` (maxsize=10)

**Pipeline:**

1. Dequeue frame from `_frame_queue`
2. Run YOLO inference via `run_yolo_inference()`
3. Write to shared frame (LIVE mode only)
4. For each detection:
   - Check confidence threshold (0.6)
   - Check cooldown (1s per entity type)
   - Create `DetectionEvent` and enqueue
   - On queue full, buffer locally

**Cooldown Lock:** `_cooldown_lock` (protects `_last_detection` dict)

**Logging Prefix:** `[PROCESO]`

---

### Thread 3: TRANSMISIÓN (Transmission)

**Methods:**

- `_transmit_thread()` — Main loop
- `_send_event(event)` — Send single event
- `_flush_buffer()` — Retry buffered events

**Input Queue:** `_event_queue`  
**Local Buffer:** `_local_buffer` (max 100 events)

**Behavior:**

1. Try to dequeue event from `_event_queue`
2. Attempt HTTP POST via `simulated_http_post()`
3. On success: mark `event.sent = True`
4. On failure: push to `_local_buffer`
5. Every 5 seconds: flush buffer (retry all pending)
6. During flush, drop expired events (>1 hour)

**Logging Prefix:** `[ENVIO ]`

---

## Data Flow

### Event Lifecycle

```
Camera/Simulation
       ↓
   Frame Queue ← (Thread 1: CAPTURA)
       ↓
   YOLO Inference (Thread 2: PROCESAMIENTO)
       ↓
  Confidence Filter → Cooldown Check
       ↓
   Event Queue
       ↓
   HTTP POST (Thread 3: TRANSMISIÓN)
       ↓
   Success?
   ├─ YES → Event marked as sent
   └─ NO  → Local Buffer → Retry every 5s
```

### Shared Data Structures

| Structure         | Type                  | Protected By     | Purpose                                   |
| ----------------- | --------------------- | ---------------- | ----------------------------------------- |
| `_frame_queue`    | Queue[tuple]          | Internal lock    | IPC between CAPTURA and PROCESAMIENTO     |
| `_event_queue`    | Queue[DetectionEvent] | Internal lock    | IPC between PROCESAMIENTO and TRANSMISIÓN |
| `_local_buffer`   | LocalBuffer           | Internal lock    | Network failure tolerance                 |
| `_last_detection` | dict[str, float]      | `_cooldown_lock` | Cooldown state per entity type            |
| `_shared_frame`   | SharedFrame           | Internal lock    | LIVE mode: frame display                  |

---

## Configuration

All configuration is centralized in `config.py`:

```python
class Config:
    LIVE_MODE = False                      # Camera + window vs. simulation
    FRAME_INTERVAL_S = 0.033               # 30 FPS
    DEADLINE_INTRUSO_MS = 200              # End-to-end latency deadline
    COOLDOWN_S = 1.0                       # Per-class detection cooldown
    BUFFER_MAX = 100                       # Local buffer capacity
    RETRY_INTERVAL_S = 5.0                 # Buffer retry interval
    EVENT_EXPIRY_S = 3600.0                # Event expiration (1 hour)
    CONFIDENCE_THRESHOLD = 0.6             # YOLO detection confidence
    BACKEND_URL = "http://localhost:8080/api/events"
    SIMULATE_NETWORK_FAILURE = False       # Test network resilience
    CAMERA_INDEX = 0                       # Camera device index
    YOLO_CLASS_PERSON = 0                  # COCO class ID
    YOLO_CLASS_DOG = 16                    # COCO class ID
```

---

## Module Descriptions

### `config.py`

Centralized configuration. Edit here to change behavior without touching code.

**Key Exports:**

- `Config` class with all parameters

---

### `models.py`

Data structures for events and states.

**Key Classes:**

- `DetectionState` (enum): IDLE, DETECTING, SENDING, COOLDOWN
- `DetectionEvent`: Event payload with timestamp, confidence, frame_id
  - `to_dict()` → JSON-serializable dict for backend transmission

---

### `shared.py`

Utilities for inter-thread communication.

**Key Classes:**

- `SharedFrame`: Thread-safe container for latest frame + detections
  - `write(frame, detections)` — Atomic write
  - `read()` → (frame, detections) — Atomic read

**Key Functions:**

- `log(*parts)` → Print timestamped log with thread name

---

### `buffer.py`

Local FIFO queue for network failure tolerance.

**Key Classes:**

- `LocalBuffer(max_size)`: Thread-safe deque with dropping policy
  - `push(event)` → Add event (drop oldest if full)
  - `flush()` → Extract all and clear buffer
  - `pending_count()` → Current size

---

### `inference.py`

YOLO detection engine.

**Key Functions:**

- `run_yolo_inference(frame_id, frame)` → list[dict]
  - LIVE mode: Real YOLOv8 inference
  - SIM mode: Random detections for testing
  - Returns: [{"class": str, "confidence": float, "box": (x1, y1, x2, y2)}]

---

### `drawing.py`

Visualization of detections.

**Key Functions:**

- `draw_boxes(frame, detections)` → annotated_frame
  - Colors: Person=Blue, Dog=Green
  - Draws bounding boxes + labels

---

### `network.py`

Network communication simulation.

**Key Functions:**

- `simulated_http_post(event)` → bool
  - Returns True (success) or False (network failure)
  - Respects `Config.SIMULATE_NETWORK_FAILURE` flag

---

### `edge_module.py`

Main orchestrator class.

**Key Class:**

- `EdgeModule`: Manages 3 threads and queues
  - `start()` → Launch all threads
  - `stop()` → Signal graceful shutdown
  - `display_frame_mainthread()` → Display loop (main thread)

---

### `main.py`

Entry point.

**Key Function:**

- `main()` → Initialize EdgeModule and start system

---

## Logging Format

All logs follow this format:

```
[HH:MM:SS.mmm] [ThreadName.........] Message
```

**Example:**

```
[15:30:42.300] [Captura.........] Leyendo frames en tiempo real…
[15:30:42.450] [Procesamiento....] Frame 15: Person detectado (conf=0.85). Evento encolado para envío.
[15:30:42.460] [Transmision.....] → POST http://localhost:8080/api/events
[15:30:42.470] [Transmision.....] ✓ Enviado exitosamente
```

**Thread Name Mappings:**

- `[CAPTURA]` — Capture thread
- `[PROCESO]` — Processing thread
- `[ENVIO ]` — Transmission thread
- `[BUFFER]` — Buffer operations
- `[DISPLAY]` — Display thread
- `[YOLO  ]` — YOLO inference
- `[MAIN  ]` — Main thread

---

## Performance

### Typical Latencies (Simulation Mode)

```
Frame Capture      → 33 ms (30 FPS)
YOLO Inference     → 45 ms (nano model on CPU)
Processing Queue   → 5 ms
Network (simulated)→ 10 ms
───────────────────────────
Total E2E          → 93 ms ✓ (well under 200ms deadline)
```

### System Requirements

- **CPU**: 2+ cores recommended
- **RAM**: 512 MB minimum (with YOLO model: 1.5 GB)
- **Storage**: 100 MB (for yolov8n.pt model)
- **Network**: Not required (simulator uses local buffer)

---

## Testing Scenarios

### 1. Network Resilience Test

```python
# In config.py:
Config.SIMULATE_NETWORK_FAILURE = True

# Run: python main.py
# Watch logs for:
# [ENVIO ] Status : ✗ Network failure — guardado en buffer local
# [BUFFER] Cola llena si hay muchos eventos...

# After 10 seconds, change to:
Config.SIMULATE_NETWORK_FAILURE = False

# Watch buffer drain every 5 seconds:
# [ENVIO ] ── Reintento de buffer: N evento(s) pendientes ──
# [ENVIO ] Reintento ✓ — Person frame_id=42
```

### 2. Cooldown Behavior Test

```
[15:30:42.300] [PROCESO] Frame 10: Person detectado → encolado
[15:30:42.500] [PROCESO] Frame 15: Person en cooldown (quedan 0.80 s)
[15:30:42.800] [PROCESO] Frame 24: Person en cooldown (quedan 0.20 s)
[15:30:43.300] [PROCESO] Frame 30: Person detectado → encolado (cooldown expired)
```

### 3. Confidence Threshold Test

Edit `Config.CONFIDENCE_THRESHOLD` in `config.py`:

```python
Config.CONFIDENCE_THRESHOLD = 0.9  # Very strict
# Fewer detections, but higher quality

Config.CONFIDENCE_THRESHOLD = 0.3  # Very lenient
# More detections, including false positives
```

---

## Backend Integration

The Edge Module sends JSON POST requests to:

```
POST http://localhost:8080/api/events
Content-Type: application/json

{
  "event_id": 140734123456,
  "entity_type": "Person",
  "confidence": 0.87,
  "frame_id": 42,
  "timestamp": "2026-02-05T15:30:42.300Z"
}
```

**Backend Responsibilities:**

- Store events in database
- Perform face recognition (if Person detected)
- Trigger alerts to frontend
- Handle duplicate events (same frame_id)
- Return HTTP 2xx for success

---

## Graceful Shutdown

When user presses Ctrl+C:

1. Main thread catches `KeyboardInterrupt`
2. Calls `edge.stop()` → sets `_running = False`
3. All 3 threads detect `_running == False` and exit loops
4. Main thread joins all threads with 3-second timeout
5. Finally block executes cleanup
6. Program terminates

---

## Future Enhancements

- [ ] Real HTTP POST to Spring Boot backend (remove simulation)
- [ ] WebSocket streaming for live frames to frontend
- [ ] Multi-camera support (multiple EdgeModule instances)
- [ ] GPU acceleration (CUDA/Metal)
- [ ] Model quantization for faster inference
- [ ] Edge model retraining pipeline
- [ ] Prometheus metrics export
- [ ] Configuration hot-reload (without restart)

---

## Troubleshooting

### Issue: "No module named 'ultralytics'"

```bash
pip install ultralytics==8.0.196
```

### Issue: "Camera not found"

```python
# In config.py, try different indices:
Config.CAMERA_INDEX = 0  # Default
Config.CAMERA_INDEX = 1  # Try this
Config.CAMERA_INDEX = 2  # Or this
```

### Issue: "YOLOv8 model not downloading"

```bash
cd src
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

### Issue: "OpenCV window won't open (macOS)"

```bash
# Install XQuartz
brew install xquartz

# Or switch to SIMULATION mode:
Config.LIVE_MODE = False
```

### Issue: "Events not buffering"

Ensure `Config.SIMULATE_NETWORK_FAILURE = True` is set in `config.py`.

---

## Code Map

```
src/
├── __init__.py             ← Package exports
├── main.py                 ← Entry point (print header, start EdgeModule)
├── config.py               ← All configuration constants
├── models.py               ← DetectionEvent, DetectionState
├── shared.py               ← SharedFrame, log()
├── buffer.py               ← LocalBuffer class
├── inference.py            ← run_yolo_inference()
├── drawing.py              ← draw_boxes()
├── network.py              ← simulated_http_post()
└── edge_module.py          ← EdgeModule class (3 threads)
```

---

## License

Universidad Iberoamericana (UNIBE) — Ingeniería de Software en Tiempo Real
