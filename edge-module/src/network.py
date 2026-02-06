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


def _encode_frame(frame, quality=85) -> bytes:
    """
    Encode OpenCV frame to JPEG bytes.
    
    Args:
        frame: OpenCV image array
        quality: JPEG quality (1-100)
        
    Returns:
        bytes: JPEG-encoded image data
    """
    if frame is None:
        return None
    try:
        success, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if success:
            return encoded.tobytes()
    except Exception as e:
        log(f"[NETWORK] Error encoding frame: {str(e)}")
    return None


def send_stream_frame(frame) -> bool:
    """
    Send a single frame to the backend streaming endpoint.
    
    Args:
        frame: OpenCV frame to send
        
    Returns:
        bool: True if successful, False otherwise
    """
    if frame is None:
        return False
        
    if Config.SIMULATE_NETWORK_FAILURE:
        return False
    
    try:
        # Encode frame with moderate quality for streaming
        frame_bytes = _encode_frame(frame, quality=75)
        if not frame_bytes:
            log(f"[STREAM] Failed to encode frame")
            return False
        
        # Send to stream endpoint
        files = {
            'frame': ('frame.jpg', frame_bytes, 'image/jpeg')
        }
        data = {
            'contentType': 'image/jpeg'
        }
        
        response = requests.post(
            Config.BACKEND_STREAM_URL,
            data=data,
            files=files,
            timeout=2  # Shorter timeout for streaming
        )
        
        return response.status_code in [200, 201]
        
    except requests.exceptions.ConnectionError as e:
        log(f"[STREAM] Connection error: Cannot reach {Config.BACKEND_STREAM_URL}")
        return False
    except requests.exceptions.Timeout as e:
        log(f"[STREAM] Timeout error: Server not responding")
        return False
    except Exception as e:
        log(f"[STREAM] Error sending frame: {type(e).__name__} - {str(e)}")
        return False


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
        
        # Encode frame if provided
        frame_bytes = None
        if frame is not None:
            frame_bytes = _encode_frame(frame)
            if frame_bytes:
                log(f"[NETWORK] Frame encoded: {len(frame_bytes)} bytes")
        
        # Send as JSON body with optional frame
        if frame_bytes:
            # Send as multipart/form-data
            files = {
                'frameImage': ('frame.jpg', frame_bytes, 'image/jpeg')
            }
            data = {
                'eventId': payload['eventId'],
                'entityType': payload['entityType'],
                'confidence': payload['confidence'],
                'frameId': payload['frameId'],
                'timestamp': payload['timestamp']
            }
            response = requests.post(
                Config.BACKEND_URL,
                data=data,
                files=files,
                timeout=5
            )
        else:
            # Send as JSON only
            response = requests.post(
                Config.BACKEND_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
        
        if response.status_code in [200, 201]:
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
