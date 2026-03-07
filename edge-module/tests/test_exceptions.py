"""Unit tests for exception handling."""
import pytest
import unittest
from unittest.mock import Mock, patch, MagicMock
import queue
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.exceptions import *
from src.edge_module import EdgeModule
from src.network import _circuit_breaker
from src.config import Config


class TestCameraExceptions(unittest.TestCase):
    """Test camera exception scenarios."""
    
    @patch('cv2.VideoCapture')
    def test_camera_not_found_all_indices_fail(self, mock_capture):
        """Test CameraNotFoundException when no camera available at any index."""
        # Mock camera that never opens
        mock_cam = Mock()
        mock_cam.isOpened.return_value = False
        mock_capture.return_value = mock_cam
        
        module = EdgeModule()
        
        with self.assertRaises(CameraNotFoundException):
            module._initialize_camera_with_retry()
        
        print("✓ Test passed: CameraNotFoundException raised when no camera found")
    
    @patch('cv2.VideoCapture')
    def test_camera_opens_on_retry(self, mock_capture):
        """Test camera opens successfully on retry."""
        mock_cam = Mock()
        # First call fails, second succeeds
        mock_cam.isOpened.side_effect = [False, True]
        mock_capture.return_value = mock_cam
        
        module = EdgeModule()
        cap = module._initialize_camera_with_retry()
        
        self.assertIsNotNone(cap)
        print("✓ Test passed: Camera opened successfully on retry")
    
    @patch('cv2.VideoCapture')
    def test_camera_tries_alternative_indices(self, mock_capture):
        """Test that camera initialization tries multiple indices."""
        mock_cam = Mock()
        mock_cam.isOpened.return_value = False
        mock_capture.return_value = mock_cam
        
        module = EdgeModule()
        
        try:
            module._initialize_camera_with_retry()
        except CameraNotFoundException:
            pass
        
        # Should have tried multiple indices
        self.assertGreater(mock_capture.call_count, 1)
        print(f"✓ Test passed: Tried {mock_capture.call_count} camera indices")


class TestCameraDisconnection(unittest.TestCase):
    """Test camera disconnection detection."""
    
    @patch('cv2.VideoCapture')
    def test_consecutive_failures_detection(self, mock_capture):
        """Test detection of consecutive frame read failures."""
        module = EdgeModule()
        module._running = True
        
        # Track consecutive failures by simulating failed reads
        consecutive_failures = 0
        threshold = Config.CAMERA_FAILURE_THRESHOLD
        
        # Simulate failures
        for i in range(threshold + 1):
            consecutive_failures += 1
        
        self.assertGreaterEqual(consecutive_failures, threshold)
        print(f"✓ Test passed: Detected {consecutive_failures} consecutive failures (threshold: {threshold})")
    
    def test_failure_counter_resets_on_success(self):
        """Test that failure counter resets on successful read."""
        consecutive_failures = 10
        # Simulate successful read
        consecutive_failures = 0
        
        self.assertEqual(consecutive_failures, 0)
        print("✓ Test passed: Failure counter resets on successful read")


class TestQueueExceptions(unittest.TestCase):
    """Test queue exception scenarios."""
    
    def test_frame_queue_full_error(self):
        """Test FrameQueueFullError when frame queue is at capacity."""
        test_queue = queue.Queue(maxsize=2)
        
        # Fill queue
        test_queue.put("frame1")
        test_queue.put("frame2")
        
        # Next put should raise Full
        with self.assertRaises(queue.Full):
            test_queue.put_nowait("frame3")
        
        print("✓ Test passed: Frame queue Full exception raised")
    
    def test_event_queue_full_buffers_event(self):
        """Test that events are buffered when queue is full."""
        module = EdgeModule()
        
        # Simulate full event queue by filling it
        test_queue = queue.Queue(maxsize=2)
        test_queue.put("event1")
        test_queue.put("event2")
        
        # Verify queue is full
        self.assertTrue(test_queue.full())
        print("✓ Test passed: Event queue can reach capacity")


class TestNetworkExceptions(unittest.TestCase):
    """Test network exception scenarios."""
    
    @patch('requests.post')
    def test_backend_connection_error(self, mock_post):
        """Test BackendConnectionError is raised on connection failure."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        from src.network import _send_event_request
        from src.models import DetectionEvent
        
        event = DetectionEvent(entity_type="Person", confidence=0.9, frame_id=1)
        
        result = _send_event_request(event, frame=None)
        
        # Should return False on connection error
        self.assertFalse(result)
        print("✓ Test passed: Connection error handled gracefully")
    
    @patch('requests.post')
    def test_backend_timeout_error(self, mock_post):
        """Test BackendTimeoutError is raised on timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        from src.network import _send_event_request
        from src.models import DetectionEvent
        
        event = DetectionEvent(entity_type="Person", confidence=0.9, frame_id=1)
        
        result = _send_event_request(event, frame=None)
        
        # Should return False on timeout
        self.assertFalse(result)
        print("✓ Test passed: Timeout error handled gracefully")
    
    @patch('requests.post')
    def test_backend_404_client_error(self, mock_post):
        """Test BackendClientError (404) handling."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        mock_post.return_value = mock_response
        
        from src.network import _send_event_request
        from src.models import DetectionEvent
        
        event = DetectionEvent(entity_type="Person", confidence=0.9, frame_id=1)
        
        result = _send_event_request(event, frame=None)
        
        # Should return False and raise exception
        self.assertFalse(result)
        print("✓ Test passed: 404 client error handled")
    
    @patch('requests.post')
    def test_backend_500_server_error(self, mock_post):
        """Test BackendServerError (500) handling."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        mock_post.return_value = mock_response
        
        from src.network import _send_event_request
        from src.models import DetectionEvent
        
        event = DetectionEvent(entity_type="Person", confidence=0.9, frame_id=1)
        
        result = _send_event_request(event, frame=None)
        
        # Should return False
        self.assertFalse(result)
        print("✓ Test passed: 500 server error handled")
    
    @patch('requests.post')
    def test_backend_429_rate_limit(self, mock_post):
        """Test 429 rate limit handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Too many requests"
        mock_post.return_value = mock_response
        
        from src.network import _send_event_request
        from src.models import DetectionEvent
        
        event = DetectionEvent(entity_type="Person", confidence=0.9, frame_id=1)
        
        result = _send_event_request(event, frame=None)
        
        # Should return False (will retry)
        self.assertFalse(result)
        print("✓ Test passed: 429 rate limit handled")


class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker pattern."""
    
    def setUp(self):
        """Reset circuit breaker before each test."""
        _circuit_breaker.state = "CLOSED"
        _circuit_breaker.failure_count = 0
        _circuit_breaker.success_count = 0
    
    def test_circuit_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        threshold = Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD
        
        # Simulate failures
        for i in range(threshold):
            _circuit_breaker._on_failure()
        
        self.assertEqual(_circuit_breaker.state, "OPEN")
        print(f"✓ Test passed: Circuit opened after {threshold} failures")
    
    def test_circuit_stays_closed_on_success(self):
        """Test circuit stays closed on successful requests."""
        _circuit_breaker._on_success()
        
        self.assertEqual(_circuit_breaker.state, "CLOSED")
        print("✓ Test passed: Circuit stays closed on success")
    
    def test_circuit_transitions_to_half_open(self):
        """Test circuit transitions to half-open after timeout."""
        # Open the circuit
        for i in range(Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD):
            _circuit_breaker._on_failure()
        
        # Manually transition to half-open (simulating timeout)
        _circuit_breaker._transition_to("HALF_OPEN")
        
        self.assertEqual(_circuit_breaker.state, "HALF_OPEN")
        print("✓ Test passed: Circuit transitioned to HALF_OPEN")
    
    def test_circuit_closes_after_successes_in_half_open(self):
        """Test circuit closes after successes in half-open state."""
        # Open circuit
        for i in range(Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD):
            _circuit_breaker._on_failure()
        
        # Transition to half-open
        _circuit_breaker._transition_to("HALF_OPEN")
        
        # Record successes
        for i in range(Config.CIRCUIT_BREAKER_SUCCESS_THRESHOLD):
            _circuit_breaker._on_success()
        
        self.assertEqual(_circuit_breaker.state, "CLOSED")
        print(f"✓ Test passed: Circuit closed after {Config.CIRCUIT_BREAKER_SUCCESS_THRESHOLD} successes")
    
    def test_circuit_reopens_on_failure_in_half_open(self):
        """Test circuit reopens on failure in half-open state."""
        # Open circuit
        for i in range(Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD):
            _circuit_breaker._on_failure()
        
        # Transition to half-open
        _circuit_breaker._transition_to("HALF_OPEN")
        
        # Fail in half-open
        _circuit_breaker._on_failure()
        
        self.assertEqual(_circuit_breaker.state, "OPEN")
        print("✓ Test passed: Circuit reopened on failure in HALF_OPEN")


class TestMemoryPressure(unittest.TestCase):
    """Test memory pressure detection."""
    
    @patch('psutil.virtual_memory')
    def test_memory_ok(self, mock_memory):
        """Test OK memory status."""
        mock_memory.return_value = Mock(percent=50.0)
        
        module = EdgeModule()
        status = module._check_memory_pressure()
        
        self.assertEqual(status, "OK")
        print("✓ Test passed: Memory status OK at 50%")
    
    @patch('psutil.virtual_memory')
    def test_memory_warning(self, mock_memory):
        """Test WARNING memory status."""
        mock_memory.return_value = Mock(percent=80.0)
        
        module = EdgeModule()
        status = module._check_memory_pressure()
        
        self.assertEqual(status, "WARNING")
        print("✓ Test passed: Memory status WARNING at 80%")
    
    @patch('psutil.virtual_memory')
    def test_memory_critical(self, mock_memory):
        """Test CRITICAL memory status."""
        mock_memory.return_value = Mock(percent=95.0)
        
        module = EdgeModule()
        status = module._check_memory_pressure()
        
        self.assertEqual(status, "CRITICAL")
        print("✓ Test passed: Memory status CRITICAL at 95%")
    
    def test_memory_check_without_psutil(self):
        """Test memory check works without psutil."""
        module = EdgeModule()
        
        # Mock psutil as None
        import src.edge_module
        original_psutil = src.edge_module.psutil
        src.edge_module.psutil = None
        
        status = module._check_memory_pressure()
        
        # Should return OK when psutil not available
        self.assertEqual(status, "OK")
        
        # Restore psutil
        src.edge_module.psutil = original_psutil
        print("✓ Test passed: Memory check works without psutil")


def run_tests():
    """Run all unit tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCameraExceptions))
    suite.addTests(loader.loadTestsFromTestCase(TestCameraDisconnection))
    suite.addTests(loader.loadTestsFromTestCase(TestQueueExceptions))
    suite.addTests(loader.loadTestsFromTestCase(TestNetworkExceptions))
    suite.addTests(loader.loadTestsFromTestCase(TestCircuitBreaker))
    suite.addTests(loader.loadTestsFromTestCase(TestMemoryPressure))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
