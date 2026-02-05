# Edge Module — Real-Time Security Detection System

Complete refactored and modularized version of the edge detection system.

## Quick Start

```bash
cd edge-module
pip install -r requirements.txt
cd src
python main.py
```

**Configuration:** Edit `src/config.py` before running.

## Directory Structure

```
edge-module/
├── README.md                    # Quick start (this file)
├── ARCHITECTURE.md              # Detailed documentation
├── requirements.txt             # Python dependencies
│
└── src/
    ├── __init__.py              # Package marker
    ├── main.py                  # Entry point
    │
    ├── config.py                # Centralized configuration
    ├── models.py                # DetectionEvent, DetectionState
    │
    ├── buffer.py                # LocalBuffer (FIFO with tolerance)
    ├── shared.py                # SharedFrame + log utility
    │
    ├── inference.py             # YOLO detection
    ├── drawing.py               # Bounding box visualization
    ├── network.py               # HTTP simulation
    │
    └── edge_module.py           # Main orchestrator (3 threads)
```

## Execution Modes

### SIMULATION Mode (No Camera Required)

```python
# In src/config.py:
Config.LIVE_MODE = False
```

```bash
cd src && python main.py
```

### LIVE Mode (With Camera)

```python
# In src/config.py:
Config.LIVE_MODE = True
```

```bash
cd src && python main.py
```

Opens OpenCV window with annotated detections.

## Network Failure Testing

```python
# In src/config.py:
Config.SIMULATE_NETWORK_FAILURE = True
```

Watch events buffer and retry every 5 seconds.

## Module Overview

| File             | Purpose                                    |
| ---------------- | ------------------------------------------ |
| `config.py`      | Centralized configuration constants        |
| `models.py`      | DetectionEvent, DetectionState enums       |
| `shared.py`      | SharedFrame (thread-safe), log() function  |
| `buffer.py`      | LocalBuffer (FIFO queue with dropping)     |
| `inference.py`   | run_yolo_inference() — real or simulated   |
| `drawing.py`     | draw_boxes() — bounding box visualization  |
| `network.py`     | simulated_http_post() — network simulation |
| `edge_module.py` | EdgeModule class — 3-thread orchestrator   |
| `main.py`        | Entry point with startup info              |

## 3-Thread Architecture

1. **CAPTURA (Capture)** — Reads frames or simulates them
2. **PROCESAMIENTO (Processing)** — YOLO inference, filtering, cooldown
3. **TRANSMISIÓN (Transmission)** — HTTP POST, buffer retry

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed diagrams and behavior.

## Key Features

✅ **3-thread design** with queue-based IPC  
✅ **Network resilience** — local buffer (max 100 events)  
✅ **Cooldown filtering** — 1s between same-class detections  
✅ **Deadline tracking** — measures latency end-to-end  
✅ **Thread-safe** — all shared data protected by locks  
✅ **Configurable** — all parameters in `config.py`  
✅ **Simulation mode** — test without camera/dependencies

## Dependencies

- `opencv-python` — Camera capture & visualization
- `ultralytics` — YOLOv8 inference
- `numpy` — Array operations
- `Pillow` — Image processing

## Troubleshooting

**Camera not found?**

```python
Config.CAMERA_INDEX = 1  # Try 0, 1, 2, 3
```

**YOLOv8 model download fails?**

```bash
python -c "from ultralytics import YOLO; YOLO('yolov8n.pt')"
```

**macOS display issues?**

```bash
brew install xquartz
```

See [ARCHITECTURE.md](./ARCHITECTURE.md) for more details.

## Configuration

The configuration settings can be found in `src/config.py`. Key settings include:

- `LIVE_MODE`: Set to `True` to use the camera, or `False` for simulated frames.
- `COOLDOWN_S`: Minimum time between events of the same type.
- `BUFFER_MAX`: Maximum number of events to store in the local buffer during network failures.
- `BACKEND_URL`: URL of the backend service for event transmission.

## Dependencies

This module requires the following Python packages:

- `opencv-python`
- `ultralytics`
- `numpy`
- `queue`
- `threading`
- `datetime`

Install these dependencies using the `requirements.txt` file.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
