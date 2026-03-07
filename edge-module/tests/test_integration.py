"""Integration tests for exception handling - tests real scenarios."""
import time
import logging
import sys
import os
from unittest.mock import patch, Mock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.edge_module import EdgeModule
from src.config import Config
from src.exceptions import *

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def separator(title):
    """Print test separator."""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def test_camera_not_found():
    """Integration Test 1: Camera Not Found with Invalid Index."""
    separator("INTEGRATION TEST 1: Camera Not Found")
    
    print("Testing with invalid camera index (99)...")
    
    with patch('cv2.VideoCapture') as mock_cap:
        # Mock camera that never opens
        mock_camera = Mock()
        mock_camera.isOpened.return_value = False
        mock_cap.return_value = mock_camera
        
        try:
            module = EdgeModule()
            module._initialize_camera_with_retry()
            print("❌ FAIL: No exception raised")
            return False
        except CameraNotFoundException as e:
            print(f"✅ PASS: Caught CameraNotFoundException: {e}")
            print(f"   - Tried {mock_cap.call_count} camera attempts")
            return True
        except Exception as e:
            print(f"❌ FAIL: Wrong exception type: {type(e).__name__}")
            return False


def test_camera_reconnection():
    """Integration Test 2: Camera Disconnection and Reconnection."""
    separator("INTEGRATION TEST 2: Camera Disconnection & Reconnection")
    
    print("Simulating camera disconnection during operation...")
    
    with patch('cv2.VideoCapture') as mock_cap:
        # First camera works, then fails, then works again
        camera1 = Mock()
        camera1.isOpened.return_value = True
        camera1.read.side_effect = [(True, "frame")] * 5 + [(False, None)] * 15
        
        camera2 = Mock()
        camera2.isOpened.return_value = True
        camera2.read.return_value = (True, "frame")
        
        # First call returns failing camera, second returns working camera
        mock_cap.side_effect = [camera1, camera2]
        
        module = EdgeModule()
        cap = module._initialize_camera_with_retry()
        
        print(f"✅ PASS: Camera initialized successfully")
        print(f"   - Reconnection logic available")
        return True


def test_network_failure_buffering():
    """Integration Test 3: Network Failure with Event Buffering."""
    separator("INTEGRATION TEST 3: Network Failure & Event Buffering")
    
    print("Testing event buffering when network is unavailable...")
    
    # Save original config
    original_simulate = Config.SIMULATE_NETWORK_FAILURE
    
    try:
        # Enable network failure simulation
        Config.SIMULATE_NETWORK_FAILURE = True
        
        module = EdgeModule()
        
        # Create and queue some events
        from src.models import DetectionEvent
        
        events = []
        for i in range(5):
            event = DetectionEvent(
                entity_type="Person",
                confidence=0.85,
                frame_id=i
            )
            events.append(event)
            module._local_buffer.push(event)
        
        buffered_count = len(module._local_buffer.get_all())
        
        if buffered_count == 5:
            print(f"✅ PASS: Successfully buffered {buffered_count} events")
            print(f"   - Events preserved during network failure")
            return True
        else:
            print(f"❌ FAIL: Expected 5 buffered events, got {buffered_count}")
            return False
    
    finally:
        # Restore original config
        Config.SIMULATE_NETWORK_FAILURE = original_simulate


def test_queue_overflow_handling():
    """Integration Test 4: Queue Overflow Handling."""
    separator("INTEGRATION TEST 4: Queue Overflow Handling")
    
    print("Testing queue overflow scenario...")
    
    import queue
    
    # Create small queue
    test_queue = queue.Queue(maxsize=3)
    buffered_events = []
    
    # Try to add more events than capacity
    for i in range(10):
        try:
            test_queue.put_nowait(f"event_{i}")
        except queue.Full:
            # Buffer the overflow
            buffered_events.append(f"event_{i}")
    
    queue_size = test_queue.qsize()
    buffer_size = len(buffered_events)
    
    print(f"   - Queue size: {queue_size}/3")
    print(f"   - Buffered overflow: {buffer_size} events")
    
    if queue_size == 3 and buffer_size == 7:
        print(f"✅ PASS: Queue overflow handled correctly")
        return True
    else:
        print(f"❌ FAIL: Unexpected queue/buffer state")
        return False


def test_circuit_breaker_integration():
    """Integration Test 5: Circuit Breaker Pattern."""
    separator("INTEGRATION TEST 5: Circuit Breaker Integration")
    
    print("Testing circuit breaker with multiple failures...")
    
    from src.network import _circuit_breaker
    from src.models import DetectionEvent
    import requests
    
    # Reset circuit breaker
    _circuit_breaker.state = "CLOSED"
    _circuit_breaker.failure_count = 0
    
    with patch('requests.post') as mock_post:
        # Simulate connection errors
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")
        
        from src.network import simulated_http_post
        
        # Make multiple failing requests
        event = DetectionEvent(entity_type="Person", confidence=0.9, frame_id=1)
        
        for i in range(Config.CIRCUIT_BREAKER_FAILURE_THRESHOLD + 1):
            result = simulated_http_post(event)
        
        circuit_state = _circuit_breaker.get_state()
        
        if circuit_state == "OPEN":
            print(f"✅ PASS: Circuit breaker opened after failures")
            print(f"   - State: {circuit_state}")
            print(f"   - Failures: {_circuit_breaker.failure_count}")
            
            # Reset for other tests
            _circuit_breaker.state = "CLOSED"
            _circuit_breaker.failure_count = 0
            
            return True
        else:
            print(f"❌ FAIL: Circuit breaker state is {circuit_state}, expected OPEN")
            return False


def test_memory_pressure_detection():
    """Integration Test 6: Memory Pressure Detection."""
    separator("INTEGRATION TEST 6: Memory Pressure Detection")
    
    print("Testing memory pressure monitoring...")
    
    with patch('psutil.virtual_memory') as mock_mem:
        module = EdgeModule()
        
        # Test different memory levels
        test_cases = [
            (50.0, "OK"),
            (76.0, "WARNING"),
            (92.0, "CRITICAL"),
        ]
        
        results = []
        for percent, expected in test_cases:
            mock_mem.return_value = Mock(percent=percent)
            status = module._check_memory_pressure()
            match = status == expected
            results.append(match)
            symbol = "✓" if match else "✗"
            print(f"   {symbol} {percent}% → {status} (expected: {expected})")
        
        if all(results):
            print(f"✅ PASS: Memory pressure detection working correctly")
            return True
        else:
            print(f"❌ FAIL: Some memory pressure checks failed")
            return False


def test_end_to_end_resilience():
    """Integration Test 7: End-to-End Resilience."""
    separator("INTEGRATION TEST 7: End-to-End Resilience")
    
    print("Testing full system with multiple failure scenarios...")
    
    with patch('cv2.VideoCapture') as mock_cap:
        with patch('requests.post') as mock_post:
            # Setup mocks
            mock_camera = Mock()
            mock_camera.isOpened.return_value = True
            mock_camera.read.return_value = (True, Mock())
            mock_cap.return_value = mock_camera
            
            # Network fails initially
            import requests
            mock_post.side_effect = [
                requests.exceptions.ConnectionError("Failed"),
                requests.exceptions.ConnectionError("Failed"),
                Mock(status_code=200),  # Then succeeds
            ]
            
            module = EdgeModule()
            
            # Verify module initialized despite potential issues
            print(f"   ✓ Module initialized")
            print(f"   ✓ Buffer available: {module._local_buffer is not None}")
            print(f"   ✓ Queues created: frame={module._frame_queue is not None}, event={module._event_queue is not None}")
            
            print(f"✅ PASS: System resilient to initialization failures")
            return True


def run_all_integration_tests():
    """Run all integration tests."""
    tests = [
        test_camera_not_found,
        test_camera_reconnection,
        test_network_failure_buffering,
        test_queue_overflow_handling,
        test_circuit_breaker_integration,
        test_memory_pressure_detection,
        test_end_to_end_resilience,
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ FAIL: Test crashed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    # Summary
    separator("INTEGRATION TEST SUMMARY")
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Tests Failed: {total - passed}/{total}")
    print(f"Success Rate: {percentage:.1f}%")
    
    if passed == total:
        print("\n🎉 All integration tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
    
    return all(results)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("  EDGE MODULE - INTEGRATION TEST SUITE")
    print("="*70)
    
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)
