"""Network Communication Module."""

import time
import random
import requests
import json

try:
    from .config import Config
    from .shared import log
except ImportError:
    from config import Config
    from shared import log


def simulated_http_post(event) -> bool:
    """
    Send HTTP POST to backend with detection event.

    Handles network failures gracefully and respects test flags.

    Args:
        event: DetectionEvent to send

    Returns:
        bool: True if successful, False if network failure
    """
    if Config.SIMULATE_NETWORK_FAILURE:
        log(f"[NETWORK] Network failure simulated for event {event.id}")
        return False

    payload = event.to_dict()
    
    try:
        # Simulate network latency (5-20 ms)
        time.sleep(random.uniform(0.005, 0.020))
        
        response = requests.post(
            Config.BACKEND_URL,
            json=payload,
            timeout=5,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            log(f"[NETWORK] ✓ Event sent successfully. Response: {response.status_code}")
            return True
        else:
            log(f"[NETWORK] ✗ Unexpected response: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        log(f"[NETWORK] ✗ Connection error: {str(e)}")
        return False
    except requests.exceptions.Timeout as e:
        log(f"[NETWORK] ✗ Request timeout: {str(e)}")
        return False
    except requests.exceptions.RequestException as e:
        log(f"[NETWORK] ✗ Request failed: {str(e)}")
        return False
    except Exception as e:
        log(f"[NETWORK] ✗ Unexpected error: {str(e)}")
        return False
