"""Network Communication Module."""

import time
import random
import requests
import json
import cv2
import io

try:
    from .config import Config
    from .shared import log
except ImportError:
    from config import Config
    from shared import log


def _encode_frame(frame) -> bytes:
    """
    Encode OpenCV frame to JPEG bytes.
    
    Args:
        frame: OpenCV image array
        
    Returns:
        bytes: JPEG-encoded image data
    """
    if frame is None:
        return None
    try:
        success, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if success:
            return encoded.tobytes()
    except Exception as e:
        log(f"[NETWORK] Error encoding frame: {str(e)}")
    return None


def simulated_http_post(event, frame=None) -> bool:
    """
    Send HTTP POST to backend with detection event and optional frame image.

    Handles network failures gracefully and respects test flags.

    Args:
        event: DetectionEvent to send
        frame: Optional OpenCV frame to send as image

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
        
        # Prepare multipart form data
        files = {
            'event': (None, json.dumps(payload), 'application/json')
        }
        
        # Add frame image if provided
        if frame is not None:
            frame_bytes = _encode_frame(frame)
            if frame_bytes:
                files['frameImage'] = ('frame.jpg', frame_bytes, 'image/jpeg')
                log(f"[NETWORK] Frame encoded: {len(frame_bytes)} bytes")
        
        response = requests.post(
            Config.BACKEND_URL,
            files=files,
            timeout=5
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
