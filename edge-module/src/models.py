"""Data Models for Detection Events."""

import time
from datetime import datetime, timezone
from enum import Enum


class DetectionState(Enum):
    """State machine for detection manager."""

    IDLE = "IDLE"
    DETECTING = "DETECTING"
    SENDING = "SENDING"
    COOLDOWN = "COOLDOWN"


class DetectionEvent:
    """Represents a single detection event ready for transmission."""

    def __init__(self, entity_type: str, confidence: float, frame_id: int):
        """
        Initialize a detection event.

        Args:
            entity_type (str): "Person" or "Dog"
            confidence (float): YOLO confidence score
            frame_id (int): Frame identifier
        """
        self.id = id(self)
        self.entity_type = entity_type
        self.confidence = round(confidence, 3)
        self.frame_id = frame_id
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.capture_time = time.perf_counter()
        self.sent = False

    def to_dict(self) -> dict:
        """Serialize event to dictionary for transmission (camelCase for backend API)."""
        return {
            "eventId": self.id,
            "entityType": self.entity_type,
            "confidence": self.confidence,
            "frameId": self.frame_id,
            "timestamp": self.timestamp,
        }

    def __repr__(self) -> str:
        return (
            f"DetectionEvent(id={self.id}, "
            f"type={self.entity_type}, "
            f"conf={self.confidence}, "
            f"frame={self.frame_id})"
        )
