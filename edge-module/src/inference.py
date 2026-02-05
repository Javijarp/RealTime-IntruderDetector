"""YOLO Inference for Person and Dog Detection."""

import random
import time

try:
    from .config import Config
    from .shared import log
except ImportError:
    from config import Config
    from shared import log


def run_yolo_inference(frame_id: int, frame=None) -> list[dict]:
    """
    Execute YOLO inference on frame.

    LIVE_MODE = False  → Generate fake detections (simulation)
    LIVE_MODE = True   → Real YOLOv8 inference

    Args:
        frame_id (int): Frame identifier
        frame: Image data (None in simulation mode)

    Returns:
        list: Detections with format [{"class": str, "confidence": float, "box": tuple}]
    """
    if not Config.LIVE_MODE:
        return _simulate_inference()

    return _real_inference(frame)


def _simulate_inference() -> list[dict]:
    """
    Generate simulated detections for testing.

    Returns:
        list: Random detections with probabilities
    """
    roll = random.random()

    if roll < 0.60:
        detections = [
            {
                "class": "Person",
                "confidence": round(random.uniform(0.65, 0.98), 3),
            }
        ]
    elif roll < 0.80:
        detections = [
            {
                "class": "Dog",
                "confidence": round(random.uniform(0.70, 0.95), 3),
            }
        ]
    elif roll < 0.90:
        detections = [
            {
                "class": "Person",
                "confidence": round(random.uniform(0.65, 0.98), 3),
            },
            {
                "class": "Dog",
                "confidence": round(random.uniform(0.70, 0.95), 3),
            },
        ]
    else:
        detections = []

    # Simulate inference latency
    time.sleep(random.uniform(0.020, 0.045))
    return detections


def _real_inference(frame) -> list[dict]:
    """
    Execute real YOLOv8 inference on frame.

    Uses lazy loading for YOLO model (loaded once).

    Args:
        frame: Image data (numpy array, BGR)

    Returns:
        list: Detections filtered to Person/Dog only
    """
    from ultralytics import YOLO as _YOLO

    # Lazy load model (singleton pattern)
    if not hasattr(run_yolo_inference, "_model"):
        log("[YOLO  ] Cargando modelo yolov8n.pt …")
        run_yolo_inference._model = _YOLO("yolov8n.pt")
        log("[YOLO  ] Modelo cargado.")

    results = run_yolo_inference._model(frame, verbose=False)[0]

    detections = []
    for box in results.boxes:
        cls_id = int(box.cls[0].item())

        # Filter to Person and Dog only
        if cls_id not in (Config.YOLO_CLASS_PERSON, Config.YOLO_CLASS_DOG):
            continue

        conf = round(float(box.conf[0].item()), 3)
        if conf < Config.CONFIDENCE_THRESHOLD:
            continue

        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
        label = "Person" if cls_id == Config.YOLO_CLASS_PERSON else "Dog"

        detections.append({
            "class": label,
            "confidence": conf,
            "box": (int(x1), int(y1), int(x2), int(y2)),
        })

    return detections
