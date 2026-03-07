# Exception Handling Plan - Edge Module

## Overview

This document outlines the comprehensive exception handling strategy for the Face Recognition System edge module. The plan ensures system resilience, graceful degradation, and proper recovery from various failure scenarios.

## Core Exception Categories

### 1. Camera Exceptions

#### 1.1 Camera Not Found

**Scenario**: Camera cannot be opened during initialization

**Current Behavior**:

- Attempts to open the configured camera index (default: 1)
- Falls back to camera index 0
- System stops if no camera is available

**Improved Handling Strategy**:

```python
class CameraNotFoundException(Exception):
    """Raised when no camera device is found."""
    pass

class CameraInitializationError(Exception):
    """Raised when camera fails to initialize properly."""
    pass
```

**Recovery Actions**:

1. Retry camera initialization with exponential backoff (1s, 2s, 4s, 8s)
2. Try alternative camera indices (0, 1, 2, 3)
3. Log detailed error information (device permissions, driver status)
4. Send alert to backend about camera unavailability
5. Switch to simulation mode if all retries fail
6. Periodically attempt to reconnect (every 30 seconds)

**Monitoring**:

- Log camera status to file: `camera_status.log`
- Track retry attempts and success/failure rates
- Send telemetry to backend

---

#### 1.2 Camera Disconnected

**Scenario**: Camera connection is lost during operation

**Detection Methods**:

- `cap.read()` returns `ret = False` multiple times consecutively
- OpenCV reports device not accessible
- Sudden increase in failed frame reads

**Current Behavior**:

- Logs error and continues attempting to read
- May result in infinite loop of failed reads

**Improved Handling Strategy**:

```python
class CameraDisconnectionError(Exception):
    """Raised when camera disconnects during operation."""
    pass
```

**Recovery Actions**:

1. Count consecutive failed reads (threshold: 10 failures)
2. Release current camera handle
3. Wait 2 seconds for hardware to stabilize
4. Attempt reconnection (same strategy as "Camera Not Found")
5. If reconnection fails after 3 attempts (30 seconds), switch to simulation mode
6. Continue background reconnection attempts every 60 seconds
7. Send real-time alert to backend

**Implementation**:

```python
MAX_CONSECUTIVE_FAILURES = 10
consecutive_failures = 0
camera_reconnecting = False

while self._running:
    ret, frame = cap.read()

    if not ret:
        consecutive_failures += 1
        log(f"[CAPTURA] Failed read {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}")

        if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            if not camera_reconnecting:
                camera_reconnecting = True
                self._handle_camera_disconnection(cap)
        continue

    # Reset counter on successful read
    consecutive_failures = 0
    camera_reconnecting = False
    # ... process frame
```

---

### 2. Queue Exceptions

#### 2.1 Frame Queue Full

**Scenario**: Frame buffer queue reaches maximum capacity (5 frames)

**Current Behavior**:

- Semaphore blocks new frames
- Frames are dropped with warning log
- Stats counter incremented

**Improved Handling Strategy**:

```python
class FrameQueueFullError(Exception):
    """Raised when frame queue is at capacity."""
    pass
```

**Recovery Actions**:

1. **Backpressure Mechanism** (ALREADY IMPLEMENTED):
   - Semaphore prevents queue overflow
   - Frames dropped when no slots available
2. **Enhanced Monitoring**:
   - Track drop rate (frames dropped per minute)
   - Alert if drop rate exceeds 20%
   - Log oldest frame in queue for diagnosis

3. **Adaptive Processing**:
   - If drop rate > 30% for 1 minute, reduce capture FPS temporarily
   - Increase YOLO semaphore capacity if CPU/GPU allows
   - Consider skipping frames (process every Nth frame)

4. **Alerting**:
   - Send warning to backend if sustained high drop rate
   - Include system resource metrics (CPU, memory, GPU)

**Metrics to Track**:

```python
{
    "queue_full_events": 0,
    "frames_dropped_rate": 0.0,  # frames/second
    "avg_queue_depth": 0.0,
    "max_queue_latency_ms": 0,
}
```

---

#### 2.2 Event Queue Full

**Scenario**: Detection event queue reaches maximum capacity (10 events)

**Current Behavior**:

- Not explicitly handled (queue may block)

**Improved Handling Strategy**:

```python
class EventQueueFullError(Exception):
    """Raised when event queue is at capacity."""
    pass
```

**Recovery Actions**:

1. Use `put_nowait()` instead of blocking `put()`
2. If queue full, immediately buffer event to LocalBuffer
3. Track events going directly to buffer vs. queue
4. If event queue consistently full:
   - Increase network transmission semaphore capacity
   - Reduce retry interval for buffered events
   - Alert backend of processing bottleneck

5. **Priority Queue Implementation** (Enhancement):
   - Critical events (Person/Intruder) get priority
   - Lower priority events (Dog) can be dropped if needed

**Implementation**:

```python
try:
    self._event_queue.put_nowait(event)
except queue.Full:
    log(f"[EVENTS] Queue full, buffering event {event.id}")
    self._local_buffer.push(event)

    with self._stats_lock:
        self._stats["events_direct_to_buffer"] += 1

    # Alert if happening frequently
    if self._stats["events_direct_to_buffer"] % 10 == 0:
        log("[EVENTS] WARNING: Event queue frequently full - check network/transmission")
```

---

### 3. Network Exceptions

#### 3.1 Connection Errors

**Scenario**: Cannot establish connection to backend

**Current Behavior**:

- `requests.exceptions.ConnectionError` caught
- Returns `False`
- Event added to buffer

**Improved Handling Strategy**:

```python
class BackendConnectionError(Exception):
    """Raised when backend server is unreachable."""
    pass

class BackendTimeoutError(Exception):
    """Raised when backend request times out."""
    pass
```

**Recovery Actions**:

1. **Immediate**:
   - Buffer the event locally
   - Log network failure with timestamp
   - Don't retry immediately (avoid flooding)

2. **Background Retry**:
   - Retry buffered events every 5 seconds (configurable)
   - Use exponential backoff for persistent failures (5s, 10s, 20s, 40s, max 60s)
   - Maximum retry attempts: 20 per event

3. **Circuit Breaker Pattern**:

   ```python
   class CircuitBreaker:
       states = ["CLOSED", "OPEN", "HALF_OPEN"]

       # CLOSED: Normal operation
       # OPEN: Too many failures, stop trying
       # HALF_OPEN: Testing if service recovered
   ```

4. **Health Check**:
   - Periodically ping backend health endpoint
   - Adjust retry strategy based on health status
   - Alert operator if backend down > 5 minutes

**Implementation**:

```python
# Circuit breaker configuration
FAILURE_THRESHOLD = 5  # failures to open circuit
RECOVERY_TIMEOUT = 30  # seconds before trying HALF_OPEN
SUCCESS_THRESHOLD = 2  # successes to close circuit

circuit_state = "CLOSED"
failure_count = 0
last_failure_time = 0

def send_with_circuit_breaker(event, frame=None):
    global circuit_state, failure_count, last_failure_time

    # If circuit OPEN, check if we should try HALF_OPEN
    if circuit_state == "OPEN":
        if time.time() - last_failure_time > RECOVERY_TIMEOUT:
            circuit_state = "HALF_OPEN"
            log("[NETWORK] Circuit breaker: OPEN → HALF_OPEN (testing recovery)")
        else:
            log("[NETWORK] Circuit OPEN, buffering event")
            return False

    # Attempt to send
    success = simulated_http_post(event, frame)

    if success:
        if circuit_state == "HALF_OPEN":
            # Success in HALF_OPEN, close circuit
            circuit_state = "CLOSED"
            failure_count = 0
            log("[NETWORK] Circuit breaker: HALF_OPEN → CLOSED (recovered)")
        return True
    else:
        # Failure
        failure_count += 1
        last_failure_time = time.time()

        if failure_count >= FAILURE_THRESHOLD:
            if circuit_state != "OPEN":
                circuit_state = "OPEN"
                log(f"[NETWORK] Circuit breaker: OPENED after {failure_count} failures")

        return False
```

---

#### 3.2 Timeout Errors

**Scenario**: Request to backend exceeds timeout (5 seconds for events, 2 seconds for streaming)

**Current Behavior**:

- `requests.exceptions.Timeout` caught
- Event buffered

**Improved Handling Strategy**:

- Adaptive timeout based on network latency
- Separate timeouts for critical vs. non-critical operations
- Track timeout patterns to detect network degradation

**Recovery Actions**:

1. Buffer the event
2. Track timeout rate (timeouts per minute)
3. If timeout rate > 50%, increase timeout value
4. If persistent, switch to batch sending mode (reduce frequency, send multiple events)
5. Alert if backend response time degraded

---

#### 3.3 HTTP Error Responses

**Scenario**: Backend returns error codes (4xx, 5xx)

**Current Behavior**:

- Logs unexpected response
- Returns `False`

**Improved Handling Strategy**:

```python
class BackendError(Exception):
    """Base class for backend HTTP errors."""
    pass

class BackendClientError(BackendError):
    """4xx client errors - data/auth issues."""
    pass

class BackendServerError(BackendError):
    """5xx server errors - backend malfunction."""
    pass
```

**Recovery Actions by Error Type**:

| Error Code | Type                    | Action                                    |
| ---------- | ----------------------- | ----------------------------------------- |
| 400        | Bad Request             | Log payload, alert developer, don't retry |
| 401        | Unauthorized            | Refresh auth token, retry once            |
| 403        | Forbidden               | Alert operator, requires manual fix       |
| 404        | Not Found               | Check endpoint URL, alert developer       |
| 429        | Too Many Requests       | Back off, reduce sending rate             |
| 500        | Internal Server Error   | Buffer and retry with backoff             |
| 502/503    | Bad Gateway/Unavailable | Circuit breaker pattern                   |
| 504        | Gateway Timeout         | Increase timeout, retry                   |

**Implementation**:

```python
def handle_http_error(response, event):
    status = response.status_code

    if 400 <= status < 500:
        # Client errors - likely our fault
        if status == 429:
            # Rate limited
            log("[NETWORK] Rate limited, backing off")
            time.sleep(5)
            return True  # Retry
        else:
            # Don't retry client errors (except 429)
            log(f"[NETWORK] Client error {status}: {response.text}")
            return False

    elif 500 <= status < 600:
        # Server errors - backend's fault, retry
        log(f"[NETWORK] Server error {status}, will retry")
        return True

    return False
```

---

### 4. Resource Exceptions

#### 4.1 Out of Memory

**Scenario**: System runs out of memory due to too many buffered frames/events

**Detection**:

- Monitor memory usage
- Track buffer sizes
- Watch for system slowdown

**Prevention**:

```python
import psutil

def check_memory_pressure():
    """Check if system is under memory pressure."""
    mem = psutil.virtual_memory()

    if mem.percent > 90:
        return "CRITICAL"
    elif mem.percent > 75:
        return "WARNING"
    return "OK"

# In capture thread:
if check_memory_pressure() == "CRITICAL":
    # Emergency: drop frames more aggressively
    log("[MEMORY] CRITICAL: Dropping every other frame")
    # Skip frame
```

---

#### 4.2 Disk Space (Logging)

**Scenario**: Disk fills up from excessive logging

**Prevention**:

- Implement log rotation
- Limit log file sizes
- Archive old logs

---

## Exception Hierarchy

```python
# exceptions.py

class EdgeModuleException(Exception):
    """Base exception for all edge module errors."""
    pass

# Camera Exceptions
class CameraException(EdgeModuleException):
    """Base for camera-related errors."""
    pass

class CameraNotFoundException(CameraException):
    """No camera device found."""
    pass

class CameraInitializationError(CameraException):
    """Camera failed to initialize."""
    pass

class CameraDisconnectionError(CameraException):
    """Camera disconnected during operation."""
    pass

# Queue Exceptions
class QueueException(EdgeModuleException):
    """Base for queue-related errors."""
    pass

class FrameQueueFullError(QueueException):
    """Frame queue at capacity."""
    pass

class EventQueueFullError(QueueException):
    """Event queue at capacity."""
    pass

# Network Exceptions
class NetworkException(EdgeModuleException):
    """Base for network-related errors."""
    pass

class BackendConnectionError(NetworkException):
    """Cannot connect to backend."""
    pass

class BackendTimeoutError(NetworkException):
    """Backend request timed out."""
    pass

class BackendError(NetworkException):
    """Backend returned error response."""
    pass

class BackendClientError(BackendError):
    """4xx client error from backend."""
    def __init__(self, status_code, message):
        self.status_code = status_code
        super().__init__(f"Client error {status_code}: {message}")

class BackendServerError(BackendError):
    """5xx server error from backend."""
    def __init__(self, status_code, message):
        self.status_code = status_code
        super().__init__(f"Server error {status_code}: {message}")

# Resource Exceptions
class ResourceException(EdgeModuleException):
    """Base for resource-related errors."""
    pass

class OutOfMemoryError(ResourceException):
    """System out of memory."""
    pass

class DiskFullError(ResourceException):
    """Disk space exhausted."""
    pass
```

---

## Monitoring & Alerting

### Metrics Dashboard

Track and expose these metrics:

```python
{
    # Camera Health
    "camera_status": "connected|disconnected|reconnecting",
    "camera_reconnection_attempts": 0,
    "camera_uptime_percent": 99.5,

    # Frame Processing
    "frames_captured_total": 0,
    "frames_dropped_total": 0,
    "frames_processed_total": 0,
    "frame_drop_rate_percent": 2.5,
    "avg_frame_processing_ms": 45,

    # Queue Health
    "frame_queue_depth": 2,
    "event_queue_depth": 3,
    "frame_queue_full_events": 10,
    "event_queue_full_events": 5,

    # Network Health
    "network_status": "healthy|degraded|offline",
    "events_sent_success": 1000,
    "events_sent_failed": 50,
    "events_buffered": 25,
    "network_success_rate_percent": 95.2,
    "circuit_breaker_state": "CLOSED|OPEN|HALF_OPEN",
    "avg_request_latency_ms": 120,

    # Resource Usage
    "cpu_percent": 45.2,
    "memory_percent": 62.3,
    "buffer_memory_mb": 15.7,
}
```

### Alert Conditions

| Condition                   | Severity | Action                         |
| --------------------------- | -------- | ------------------------------ |
| Camera disconnected > 1 min | CRITICAL | Send immediate alert           |
| Frame drop rate > 50%       | HIGH     | Alert + investigate bottleneck |
| Network offline > 5 min     | CRITICAL | Alert operator                 |
| Buffer > 80% full           | WARNING  | Prepare for data loss          |
| Buffer full (100%)          | CRITICAL | Events being dropped           |
| Memory usage > 90%          | CRITICAL | Risk of crash                  |
| CPU usage > 95% sustained   | HIGH     | Performance degradation        |

---

## Testing Strategy

### Unit Tests

```python
def test_camera_not_found():
    """Test camera not found exception handling."""
    with patch('cv2.VideoCapture') as mock_cap:
        mock_cap.return_value.isOpened.return_value = False

        edge = EdgeModule()
        # Should fall back to simulation mode
        assert edge._mode == "SIMULATION"

def test_camera_disconnection():
    """Test camera disconnection during operation."""
    with patch('cv2.VideoCapture') as mock_cap:
        cap_instance = mock_cap.return_value
        cap_instance.isOpened.return_value = True

        # Simulate disconnection after 10 frames
        cap_instance.read.side_effect = [
            (True, frame) for _ in range(10)
        ] + [(False, None)] * 20

        # Should trigger reconnection logic
        # Assert reconnection attempted

def test_network_failure_buffering():
    """Test event buffering on network failure."""
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.ConnectionError()

        event = DetectionEvent(...)
        result = simulated_http_post(event)

        assert result == False
        assert event in local_buffer.get_all()
```

### Integration Tests

- Test camera reconnection with physical device disconnect
- Test network failure with backend shutdown
- Test queue overflow scenarios with high frame rate
- Test memory pressure under sustained load

### Stress Tests

- Run for 24 hours with intermittent failures
- Simulate network flapping (up/down every 30s)
- Generate high detection load (100 events/minute)
- Monitor for memory leaks and resource exhaustion

---

## Configuration

Add to `config.py`:

```python
# Exception Handling Configuration
class ExceptionConfig:
    # Camera
    CAMERA_RETRY_ATTEMPTS: int = 5
    CAMERA_RETRY_BACKOFF_S: list = [1, 2, 4, 8, 16]
    CAMERA_RECONNECT_INTERVAL_S: int = 30
    CAMERA_FAILURE_THRESHOLD: int = 10

    # Queue
    FRAME_DROP_RATE_ALERT_THRESHOLD: float = 0.20  # 20%
    QUEUE_DEPTH_WARNING_THRESHOLD: float = 0.80  # 80% full

    # Network
    NETWORK_RETRY_ATTEMPTS: int = 20
    NETWORK_RETRY_BACKOFF_S: list = [5, 10, 20, 40, 60]
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT_S: int = 30
    CIRCUIT_BREAKER_SUCCESS_THRESHOLD: int = 2

    # Timeouts
    HTTP_EVENT_TIMEOUT_S: int = 5
    HTTP_STREAM_TIMEOUT_S: int = 2
    HTTP_HEALTH_CHECK_TIMEOUT_S: int = 3

    # Monitoring
    METRICS_REPORT_INTERVAL_S: int = 60
    HEALTH_CHECK_INTERVAL_S: int = 30

    # Resource Limits
    MEMORY_WARNING_THRESHOLD_PERCENT: float = 75.0
    MEMORY_CRITICAL_THRESHOLD_PERCENT: float = 90.0
```

---

## Implementation Checklist

- [ ] Create `exceptions.py` with exception hierarchy
- [ ] Implement camera reconnection logic with retries
- [ ] Add consecutive failure detection for camera disconnection
- [ ] Implement circuit breaker pattern for network calls
- [ ] Add adaptive timeout based on network latency
- [ ] Enhance queue full handling with alerts
- [ ] Add memory pressure monitoring
- [ ] Implement metrics collection and reporting
- [ ] Create health check endpoint
- [ ] Add comprehensive logging for all exception paths
- [ ] Write unit tests for all exception scenarios
- [ ] Write integration tests for failure recovery
- [ ] Add stress tests for sustained failure conditions
- [ ] Document alerting thresholds and procedures
- [ ] Create runbook for operators

---

## Recovery Procedures (Runbook)

### Camera Not Found

1. Check physical camera connection
2. Verify camera permissions: `ls -l /dev/video*`
3. Test camera manually: `ffplay /dev/video0`
4. Check logs: `tail -f camera_status.log`
5. Try different camera index in config
6. Restart edge module

### Network Offline

1. Check network connectivity: `ping backend-server`
2. Verify backend is running: `curl http://backend:8080/health`
3. Check firewall rules
4. Review buffered events: check buffer count in logs
5. Monitor automatic recovery when network restored

### High Frame Drop Rate

1. Check CPU usage: `top`
2. Check GPU usage: `nvidia-smi` (if applicable)
3. Review processing latency in logs
4. Reduce capture FPS if needed
5. Consider hardware upgrade if sustained

### Buffer Full

1. Check network status (likely offline)
2. Review buffer contents in logs
3. If critical, manually flush old events
4. Increase BUFFER_MAX if needed
5. Monitor buffer drain rate when network recovers

---

## Best Practices

1. **Fail Gracefully**: Never crash on expected failures
2. **Log Everything**: Comprehensive logging aids debugging
3. **Alert Proactively**: Detect issues before they become critical
4. **Retry Intelligently**: Use backoff, don't flood
5. **Monitor Continuously**: Track metrics and trends
6. **Test Failures**: Regularly test failure scenarios
7. **Document Decisions**: Record why choices were made
8. **Degrade Gracefully**: Reduced functionality > total failure
9. **Recover Automatically**: Self-healing where possible
10. **Escalate Appropriately**: Know when human intervention needed

---

## Future Enhancements

1. **Machine Learning Health Prediction**: Predict failures before they occur
2. **Adaptive Configuration**: Auto-tune based on environment
3. **Distributed Buffering**: Store events on external service
4. **Multi-Backend**: Failover to backup backend
5. **Edge Clustering**: Multiple edge modules with load balancing
6. **Advanced Telemetry**: Integration with Prometheus/Grafana
7. **Auto-restart**: Watchdog process to restart on critical failures
8. **Remote Management**: Control edge module remotely

---

**Document Version**: 1.0  
**Last Updated**: March 7, 2026  
**Author**: Edge Module Team  
**Status**: Draft - Ready for Implementation
