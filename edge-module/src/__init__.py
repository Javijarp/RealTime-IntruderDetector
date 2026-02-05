"""Edge Module Package — Real-Time Detection System."""

__version__ = "1.0.0"
__author__ = "UNIBE — Ingeniería de Software en Tiempo Real"

from .edge_module import EdgeModule
from .models import DetectionEvent, DetectionState
from .config import Config

__all__ = [
    "EdgeModule",
    "DetectionEvent",
    "DetectionState",
    "Config",
]
