"""Centralized Configuration for Edge Module."""


class Config:
    """Configuration constants for real-time security detection."""

    # ── Execution Mode ──────────────────────────────────────────
    # False → Simulated (no camera, no window)
    # True  → Live mode (real camera, OpenCV window)
    LIVE_MODE: bool = True

    # Capture frequency (simulation mode only)
    FRAME_INTERVAL_S: float = 0.033  # 30 FPS

    # End-to-end deadline for critical events (intruder detection)
    DEADLINE_INTRUSO_MS: int = 200

    # Cooldown between detections of same class
    COOLDOWN_S: float = 1.0

    # Max capacity of local buffer (network failure tolerance)
    BUFFER_MAX: int = 100

    # Retry interval for failed events
    RETRY_INTERVAL_S: float = 5.0

    # Event expiration time in buffer
    EVENT_EXPIRY_S: float = 3600.0

    # Minimum confidence threshold for YOLO detections
    CONFIDENCE_THRESHOLD: float = 0.6

    # Backend URL (simulated)
    BACKEND_URL: str = "http://localhost:8080/api/events"

    # Simulate network failure?
    SIMULATE_NETWORK_FAILURE: bool = False

    # Camera index (try 0, 1, 2, 3 if default doesn't work)
    CAMERA_INDEX: int = 1

    # YOLOv8 COCO class IDs
    YOLO_CLASS_PERSON: int = 0
    YOLO_CLASS_DOG: int = 16
