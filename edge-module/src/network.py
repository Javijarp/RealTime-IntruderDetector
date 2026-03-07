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
    from .exceptions import (
        BackendConnectionError,
        BackendTimeoutError,
        BackendClientError,
        BackendServerError,
    )
except ImportError:
    from config import Config
    from shared import log
    from exceptions import (
        BackendConnectionError,
        BackendTimeoutError,
        BackendClientError,
        BackendServerError,
    )


# ═══════════════════════════════════════════════════════════════
# Circuit Breaker Pattern Implementation
# ═══════════════════════════════════════════════════════════════

class CircuitBreaker:
    """
    Circuit breaker pattern for network resilience.
    
    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Too many failures, requests blocked
    - HALF_OPEN: Testing if service recovered
    """
    
    def __init__(self):
        self.state = "CLOSED"
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = 0
        self.last_state_change = time.time()
    
    def call(self, func, *args, **kwargs):
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Result of function call or False if circuit is OPEN
        """
        # Check if circuit should transition from OPEN to HALF_OPEN
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > Config.CIRCUIT_BREAKER_RECOVERY_TIMEOUT_S:
                self._transition_to("HALF_OPEN")
                log("[CIRCUIT] Estado: OPEN → HALF_OPEN (probando recuperación)")
            else:
                log("[CIRCUIT] Estado OPEN - request bloqueado (esperando recuperación)")
                return False
        
        # Execute the function
        try:
            result = func(*args, **kwargs)
            
            if result:
                self._on_success()
            else:
                self._on_failure()
            
            return result
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _on_success(self):
        """Handle successful request."""
        if self.state == "HALF_OPEN":
            self.success_count += 1
            log(f"[CIRCUIT] HALF_OPEN: Éxito {self.success_count}/{Config.CIRCUIT_BREAKER_SUCCESS_THRESHOLD}")
            
            if self.success_count >= Config.CIRCUIT_BREAKER_SUCCESS_THRESHOLD:
                self._transition_to("CLOSED")
                log("[CIRCUIT] Estado: HALF_OPEN → CLOSED (recuperado)")
        
        elif self.state == "CLOSED":
            # Reset failure count on success
            if self.failure_count > 0:
                self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed request."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.state == "HALF_OPEN":
            # Failure in HALF_OPEN, go back to OPEN
            self._transition_to("OPEN")
            log(f"[CIRCUIT] Estado: HALF_OPEN → OPEN (fallo durante prueba)")
        
        elif self.state == "CLOSED":
            log(f"[CIRCUIT] CLOSED: Fallo {self.failure_count}/{Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD}")
            
            if self.failure_count >= Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD:
                self._transition_to("OPEN")
                log(f"[CIRCUIT] Estado: CLOSED → OPEN (threshold alcanzado: {self.failure_count} fallos)")
    
    def _transition_to(self, new_state):
        """Transition to new state."""
        old_state = self.state
        self.state = new_state
        self.last_state_change = time.time()
        
        if new_state == "CLOSED":
            self.failure_count = 0
            self.success_count = 0
        elif new_state == "HALF_OPEN":
            self.success_count = 0
    
    def get_state(self):
        """Get current circuit state."""
        return self.state


# Global circuit breaker instance
_circuit_breaker = CircuitBreaker()


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
            timeout=Config.HTTP_STREAM_TIMEOUT_S
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
    Uses circuit breaker pattern for resilience.

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
    
    # Use circuit breaker pattern
    return _circuit_breaker.call(_send_event_request, event, frame)


def _send_event_request(event, frame=None) -> bool:
    """
    Internal function to send event request (wrapped by circuit breaker).
    
    Args:
        event: DetectionEvent to send
        frame: Optional OpenCV frame to send as image
        
    Returns:
        bool: True if successful, False otherwise
    """
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
                timeout=Config.HTTP_EVENT_TIMEOUT_S
            )
        else:
            # Send as JSON only
            response = requests.post(
                Config.BACKEND_URL,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=Config.HTTP_EVENT_TIMEOUT_S
            )
        
        # Handle different response codes
        if response.status_code in [200, 201]:
            log(f"[NETWORK] ✓ Event sent successfully. Response: {response.status_code}")
            return True
        
        elif 400 <= response.status_code < 500:
            # Client errors
            if response.status_code == 429:
                # Rate limited - will retry
                log(f"[NETWORK] ⚠ Rate limited (429), backing off...")
                time.sleep(5)
                return False
            else:
                # Other client errors - don't retry
                log(f"[NETWORK] ✗ Client error {response.status_code}: {response.text}")
                raise BackendClientError(response.status_code, response.text)
        
        elif 500 <= response.status_code < 600:
            # Server errors - will retry
            log(f"[NETWORK] ✗ Server error {response.status_code}: {response.text}")
            raise BackendServerError(response.status_code, response.text)
        
        else:
            log(f"[NETWORK] ✗ Unexpected response: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError as e:
        log(f"[NETWORK] ✗ Connection error: Cannot reach backend")
        raise BackendConnectionError(f"Cannot connect to {Config.BACKEND_URL}")
    
    except requests.exceptions.Timeout as e:
        log(f"[NETWORK] ✗ Request timeout after {Config.HTTP_EVENT_TIMEOUT_S}s")
        raise BackendTimeoutError(f"Request timed out after {Config.HTTP_EVENT_TIMEOUT_S}s")
    
    except (BackendClientError, BackendServerError, BackendConnectionError, BackendTimeoutError):
        # Re-raise our custom exceptions
        return False
    
    except requests.exceptions.RequestException as e:
        log(f"[NETWORK] ✗ Request failed: {str(e)}")
        return False
    
    except Exception as e:
        log(f"[NETWORK] ✗ Unexpected error: {type(e).__name__} - {str(e)}")
        return False
