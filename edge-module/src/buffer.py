"""Local Buffer for Network Failure Tolerance."""

import threading
from collections import deque

try:
    from .models import DetectionEvent
    from .shared import log
    from .config import Config
except ImportError:
    from models import DetectionEvent
    from shared import log
    from config import Config


class LocalBuffer:
    """
    FIFO queue with maximum capacity.

    When full, drops oldest event. Thread-safe via internal lock.
    Policy: Newest events are more valuable than old ones.
    """

    def __init__(self, max_size: int = Config.BUFFER_MAX):
        """
        Initialize buffer.

        Args:
            max_size (int): Maximum number of events to buffer
        """
        self._buffer: deque[DetectionEvent] = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def push(self, event: DetectionEvent) -> None:
        """
        Add event to buffer.

        If buffer is at capacity, oldest event is automatically discarded.

        Args:
            event (DetectionEvent): Event to buffer
        """
        with self._lock:
            if len(self._buffer) == self._buffer.maxlen:
                dropped = self._buffer[0]
                log(
                    "[BUFFER] Cola llena. Evento descartado:",
                    f"frame_id={dropped.frame_id} "
                    f"type={dropped.entity_type} "
                    f"ts={dropped.timestamp}",
                )
            self._buffer.append(event)
            log(
                "[BUFFER] Evento almacenado localmente.",
                f"Pendientes en buffer: {len(self._buffer)}",
            )

    def flush(self) -> list[DetectionEvent]:
        """
        Extract all pending events (consumes buffer).

        Returns:
            list: All buffered events in order
        """
        with self._lock:
            pending = list(self._buffer)
            self._buffer.clear()
            return pending

    def pending_count(self) -> int:
        """
        Get current number of pending events.

        Returns:
            int: Number of events in buffer
        """
        with self._lock:
            return len(self._buffer)
