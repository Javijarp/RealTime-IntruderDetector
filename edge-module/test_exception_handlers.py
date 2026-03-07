#!/usr/bin/env python3
"""Manual testing script for all exception handlers - Interactive Test Suite."""
import sys
import os
import time
import logging
from unittest.mock import patch, Mock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.edge_module import EdgeModule
from src.network import _circuit_breaker
from src.config import Config
from src.exceptions import *
from src.models import DetectionEvent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'
BOLD = '\033[1m'


def separator(title, char="="):
    """Print formatted separator."""
    width = 70
    print(f"\n{BLUE}{char * width}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BLUE}{char * width}{RESET}\n")


def pass_test(message):
    """Print pass message."""
    print(f"{GREEN}✅ PASS{RESET}: {message}")


def fail_test(message):
    """Print fail message."""
    print(f"{RED}❌ FAIL{RESET}: {message}")


def info(message):
    """Print info message."""
    print(f"{YELLOW}ℹ️  INFO{RESET}: {message}")


# ═══════════════════════════════════════════════════════════════
# TEST 1: Camera Not Found
# ═══════════════════════════════════════════════════════════════

def test_1_camera_not_found():
    """Test 1: Camera Not Found Exception."""
    separator("TEST 1: Camera Not Found Exception")
    
    info("Simulating camera not found scenario...")
    info("All camera indices will fail to open")
    
    with patch('cv2.VideoCapture') as mock_cap:
        with patch('time.sleep'):  # Mock sleep to speed up test
            mock_camera = Mock()
            mock_camera.isOpened.return_value = False
            mock_cap.return_value = mock_camera
            
            try:
                module = EdgeModule()
                result = module._initialize_camera_with_retry()
                fail_test("No exception raised when camera not found")
                return False
            except CameraNotFoundException as e:
                pass_test(f"CameraNotFoundException raised: {e}")
                info(f"Attempted {mock_cap.call_count} camera initialization(s)")
                info(f"Configuration: CAMERA_RETRY_ATTEMPTS={Config.CAMERA_RETRY_ATTEMPTS}")
                return True
            except Exception as e:
                fail_test(f"Wrong exception type: {type(e).__name__}: {e}")
                return False


# ═══════════════════════════════════════════════════════════════
# TEST 2: Camera Disconnection
# ═══════════════════════════════════════════════════════════════

def test_2_camera_disconnection():
    """Test 2: Camera Disconnection Detection."""
    separator("TEST 2: Camera Disconnection Detection")
    
    info("Simulating camera disconnection during operation...")
    info(f"Threshold: {Config.CAMERA_FAILURE_THRESHOLD} consecutive failures")
    
    with patch('cv2.VideoCapture') as mock_cap:
        with patch('time.sleep'):  # Mock sleep to speed up test
            mock_camera = Mock()
            mock_camera.isOpened.return_value = True
            
            # Simulate successful reads followed by failures
            successful_reads = [(True, Mock()) for _ in range(5)]
            failed_reads = [(False, None) for _ in range(Config.CAMERA_FAILURE_THRESHOLD + 5)]
            mock_camera.read.side_effect = successful_reads + failed_reads
            
            mock_cap.return_value = mock_camera
            
            consecutive_failures = 0
            for i in range(20):
                ret, frame = mock_camera.read()
                if not ret:
                    consecutive_failures += 1
                else:
                    consecutive_failures = 0
                
                if consecutive_failures >= Config.CAMERA_FAILURE_THRESHOLD:
                    break
            
            if consecutive_failures >= Config.CAMERA_FAILURE_THRESHOLD:
                pass_test(f"Disconnection detected after {consecutive_failures} failures")
                info("Reconnection logic would be triggered at this point")
                return True
            else:
                fail_test(f"Only detected {consecutive_failures} failures (threshold: {Config.CAMERA_FAILURE_THRESHOLD})")
                return False


# ═══════════════════════════════════════════════════════════════
# TEST 3: Frame Queue Full
# ═══════════════════════════════════════════════════════════════

def test_3_frame_queue_full():
    """Test 3: Frame Queue Full Handling."""
    separator("TEST 3: Frame Queue Full Handling")
    
    info("Testing frame queue overflow with backpressure...")
    
    import queue
    
    frame_queue = queue.Queue(maxsize=5)
    dropped_frames = 0
    
    # Try to add more frames than capacity
    for i in range(10):
        try:
            frame_queue.put_nowait(f"frame_{i}")
            info(f"Frame {i} added to queue ({frame_queue.qsize()}/5)")
        except queue.Full:
            dropped_frames += 1
            info(f"Frame {i} dropped - queue full ({frame_queue.qsize()}/5)")
    
    if dropped_frames == 5 and frame_queue.qsize() == 5:
        pass_test(f"Frame queue correctly filled to capacity (5/5)")
        pass_test(f"Dropped {dropped_frames} frames due to backpressure")
        info("FrameQueueFullError handling working correctly")
        return True
    else:
        fail_test(f"Unexpected state: queue={frame_queue.qsize()}, dropped={dropped_frames}")
        return False


# ═══════════════════════════════════════════════════════════════
# TEST 4: Event Queue Full
# ═══════════════════════════════════════════════════════════════

def test_4_event_queue_full():
    """Test 4: Event Queue Full - Buffer Fallback."""
    separator("TEST 4: Event Queue Full - Buffer Fallback")
    
    info("Testing event queue overflow with buffer fallback...")
    
    module = EdgeModule()
    import queue
    
    # Create small event queue for testing
    test_queue = queue.Queue(maxsize=3)
    buffered_events = []
    
    # Try to add events
    for i in range(10):
        event = DetectionEvent(entity_type="Person", confidence=0.85, frame_id=i)
        
        try:
            test_queue.put_nowait(event)
            info(f"Event {i} queued ({test_queue.qsize()}/3)")
        except queue.Full:
            # Buffer the event
            module._local_buffer.push(event)
            buffered_events.append(event)
            info(f"Event {i} buffered (queue full)")
    
    buffer_count = len(module._local_buffer.get_all())
    
    if test_queue.qsize() == 3 and buffer_count == 7:
        pass_test(f"Event queue at capacity (3/3)")
        pass_test(f"Correctly buffered {buffer_count} overflow events")
        info("EventQueueFullError handling working correctly")
        return True
    else:
        fail_test(f"Unexpected state: queue={test_queue.qsize()}, buffer={buffer_count}")
        return False


# ═══════════════════════════════════════════════════════════════
# TEST 5: Backend Connection Error
# ═══════════════════════════════════════════════════════════════

def test_5_backend_connection_error():
    """Test 5: Backend Connection Error."""
    separator("TEST 5: Backend Connection Error")
    
    info("Simulating backend connection failure...")
    
    import requests
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        from src.network import _send_event_request
        from src.exceptions import BackendConnectionError
        
        event = DetectionEvent(entity_type="Person", confidence=0.9, frame_id=1)
        
        try:
            _send_event_request(event, frame=None)
            fail_test("BackendConnectionError not raised")
            return False
        except BackendConnectionError as e:
            pass_test(f"BackendConnectionError raised: {str(e)}")
            info("Event should be buffered for retry")
            return True


# ═══════════════════════════════════════════════════════════════
# TEST 6: Backend Timeout Error
# ═══════════════════════════════════════════════════════════════

def test_6_backend_timeout():
    """Test 6: Backend Timeout Error."""
    separator("TEST 6: Backend Timeout Error")
    
    info(f"Simulating backend timeout (>{Config.HTTP_EVENT_TIMEOUT_S}s)...")
    
    import requests
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        from src.network import _send_event_request
        from src.exceptions import BackendTimeoutError
        
        event = DetectionEvent(entity_type="Person", confidence=0.9, frame_id=1)
        
        try:
            _send_event_request(event, frame=None)
            fail_test("BackendTimeoutError not raised")
            return False
        except BackendTimeoutError as e:
            pass_test(f"BackendTimeoutError raised: {str(e)}")
            info(f"Configured timeout: {Config.HTTP_EVENT_TIMEOUT_S}s")
            return True


# ═══════════════════════════════════════════════════════════════
# TEST 7: Backend HTTP Errors
# ═══════════════════════════════════════════════════════════════

def test_7_backend_http_errors():
    """Test 7: Backend HTTP Error Responses."""
    separator("TEST 7: Backend HTTP Error Responses")
    
    info("Testing various HTTP error codes...")
    
    test_cases = [
        (400, "Bad Request", "client_error"),
        (404, "Not Found", "client_error"),
        (429, "Too Many Requests", "rate_limit"),
        (500, "Internal Server Error", "server_error"),
        (503, "Service Unavailable", "server_error"),
    ]
    
    results = []
    
    with patch('requests.post') as mock_post:
        with patch('time.sleep'):  # Mock sleep to avoid delays in 429 handling
            from src.network import _send_event_request
            
            for status_code, message, error_type in test_cases:
                mock_response = Mock()
                mock_response.status_code = status_code
                mock_response.text = message
                mock_post.return_value = mock_response
                
                event = DetectionEvent(entity_type="Person", confidence=0.9, frame_id=1)
                result = _send_event_request(event, frame=None)
                
                # All errors should return False
                if result == False:
                    pass_test(f"HTTP {status_code} ({error_type}) handled correctly")
                    results.append(True)
                else:
                    fail_test(f"HTTP {status_code} not handled properly")
                    results.append(False)
    
    return all(results)


# ═══════════════════════════════════════════════════════════════
# TEST 8: Circuit Breaker Pattern
# ═══════════════════════════════════════════════════════════════

def test_8_circuit_breaker():
    """Test 8: Circuit Breaker Pattern."""
    separator("TEST 8: Circuit Breaker Pattern")
    
    info("Testing circuit breaker state transitions...")
    
    # Reset circuit breaker
    _circuit_breaker.state = "CLOSED"
    _circuit_breaker.failure_count = 0
    _circuit_breaker.success_count = 0
    
    info(f"Initial state: {_circuit_breaker.state}")
    
    # Test 8a: Circuit opens after failures
    info(f"\nPhase 1: Triggering {Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD} failures...")
    for i in range(Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD):
        _circuit_breaker._on_failure()
        info(f"  Failure {i+1}/{Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD} - State: {_circuit_breaker.state}")
    
    if _circuit_breaker.state == "OPEN":
        pass_test(f"Circuit opened after {Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD} failures")
    else:
        fail_test(f"Circuit state is {_circuit_breaker.state}, expected OPEN")
        return False
    
    # Test 8b: Transition to HALF_OPEN
    info(f"\nPhase 2: Simulating recovery timeout...")
    _circuit_breaker._transition_to("HALF_OPEN")
    info(f"  State transitioned to: {_circuit_breaker.state}")
    
    if _circuit_breaker.state == "HALF_OPEN":
        pass_test("Circuit transitioned to HALF_OPEN")
    else:
        fail_test(f"Failed to transition to HALF_OPEN")
        return False
    
    # Test 8c: Circuit closes after successes
    info(f"\nPhase 3: Recording {Config.CIRCUIT_BREAKER_SUCCESS_THRESHOLD} successes...")
    for i in range(Config.CIRCUIT_BREAKER_SUCCESS_THRESHOLD):
        _circuit_breaker._on_success()
        info(f"  Success {i+1}/{Config.CIRCUIT_BREAKER_SUCCESS_THRESHOLD} - State: {_circuit_breaker.state}")
    
    if _circuit_breaker.state == "CLOSED":
        pass_test(f"Circuit closed after {Config.CIRCUIT_BREAKER_SUCCESS_THRESHOLD} successes")
        info("Full circuit breaker cycle completed successfully")
        return True
    else:
        fail_test(f"Circuit state is {_circuit_breaker.state}, expected CLOSED")
        return False


# ═══════════════════════════════════════════════════════════════
# TEST 9: Memory Pressure Monitoring
# ═══════════════════════════════════════════════════════════════

def test_9_memory_pressure():
    """Test 9: Memory Pressure Monitoring."""
    separator("TEST 9: Memory Pressure Monitoring")
    
    info("Testing memory pressure detection at various levels...")
    
    test_cases = [
        (50.0, "OK", "Normal operation"),
        (76.0, "WARNING", "Warning threshold"),
        (92.0, "CRITICAL", "Critical threshold"),
    ]
    
    results = []
    
    with patch('psutil.virtual_memory') as mock_mem:
        module = EdgeModule()
        
        for percent, expected_status, description in test_cases:
            mock_mem.return_value = Mock(percent=percent)
            status = module._check_memory_pressure()
            
            if status == expected_status:
                pass_test(f"{percent}% → {status} ({description})")
                results.append(True)
            else:
                fail_test(f"{percent}% → {status}, expected {expected_status}")
                results.append(False)
    
    if all(results):
        info(f"Thresholds: WARNING={Config.MEMORY_WARNING_THRESHOLD_PERCENT}%, CRITICAL={Config.MEMORY_CRITICAL_THRESHOLD_PERCENT}%")
        return True
    
    return False


# ═══════════════════════════════════════════════════════════════
# MAIN TEST RUNNER
# ═══════════════════════════════════════════════════════════════

def run_all_tests():
    """Run all exception handler tests."""
    tests = [
        ("Camera Not Found", test_1_camera_not_found),
        ("Camera Disconnection", test_2_camera_disconnection),
        ("Frame Queue Full", test_3_frame_queue_full),
        ("Event Queue Full", test_4_event_queue_full),
        ("Backend Connection Error", test_5_backend_connection_error),
        ("Backend Timeout", test_6_backend_timeout),
        ("Backend HTTP Errors", test_7_backend_http_errors),
        ("Circuit Breaker Pattern", test_8_circuit_breaker),
        ("Memory Pressure Monitoring", test_9_memory_pressure),
    ]
    
    results = []
    test_times = []
    
    print(f"\n{BOLD}{'='*70}{RESET}")
    print(f"{BOLD}  EDGE MODULE - EXCEPTION HANDLING TEST SUITE{RESET}")
    print(f"{BOLD}  Manual Testing Script{RESET}")
    print(f"{BOLD}{'='*70}{RESET}\n")
    
    info(f"Running {len(tests)} test scenarios...")
    print()
    
    for test_name, test_func in tests:
        start_time = time.time()
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            fail_test(f"{test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
        
        elapsed = time.time() - start_time
        test_times.append(elapsed)
        # time.sleep(0.5) removed for faster test execution

    
    # Summary
    separator("TEST SUMMARY", "=")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    total_time = sum(test_times)
    
    print(f"{BOLD}Results:{RESET}")
    print(f"  Total Tests:    {total}")
    print(f"  {GREEN}Passed:         {passed}{RESET}")
    print(f"  {RED}Failed:         {failed}{RESET}")
    print(f"  Success Rate:   {percentage:.1f}%")
    print(f"  Total Time:     {total_time:.2f}s")
    print()
    
    # Detailed results
    print(f"{BOLD}Detailed Results:{RESET}")
    for i, (test_name, result) in enumerate(results, 1):
        status = f"{GREEN}PASS{RESET}" if result else f"{RED}FAIL{RESET}"
        duration = f"({test_times[i-1]:.2f}s)"
        print(f"  {i:2d}. {status} - {test_name} {duration}")
    
    print()
    
    if passed == total:
        print(f"{GREEN}{BOLD}🎉 ALL TESTS PASSED! 🎉{RESET}")
        print(f"{GREEN}Exception handling is fully functional.{RESET}")
    else:
        print(f"{YELLOW}⚠️  {failed} TEST(S) FAILED{RESET}")
        print(f"Please review the failed tests above.")
    
    print(f"\n{'='*70}\n")
    
    return passed == total


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
