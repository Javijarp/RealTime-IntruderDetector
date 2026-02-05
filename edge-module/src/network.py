"""Network Communication Simulation."""

import time
import random

try:
    from .config import Config
except ImportError:
    from config import Config


def simulated_http_post(event) -> bool:
    """
    Simulate HTTP POST to backend.

    Respects SIMULATE_NETWORK_FAILURE flag for testing buffer behavior.

    Args:
        event: DetectionEvent to send

    Returns:
        bool: True if successful, False if network failure
    """
    if Config.SIMULATE_NETWORK_FAILURE:
        return False

    # Simulate network latency (5-20 ms)
    time.sleep(random.uniform(0.005, 0.020))
    return True
