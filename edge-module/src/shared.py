"""Shared Utilities and Thread-Safe Containers."""

import threading
from datetime import datetime


class SharedFrame:
    """Thread-safe container for latest frame and detections."""

    def __init__(self):
        """Initialize shared frame container."""
        self.frame = None
        self.detections = []
        self._lock = threading.Lock()

    def write(self, frame, detections: list[dict]) -> None:
        """Write frame and detections atomically."""
        with self._lock:
            self.frame = frame
            self.detections = detections

    def read(self):
        """Read frame and detections atomically."""
        with self._lock:
            return self.frame, list(self.detections)


# Global logger lock
_log_lock = threading.Lock()


def log(*parts: str) -> None:
    """
    Unified logging with timestamp and thread name.

    Args:
        *parts: Message parts to join with spaces
    """
    ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]
    thread = threading.current_thread().name
    msg = " ".join(parts)
    with _log_lock:
        print(f"[{ts}] [{thread:.<22}] {msg}")
