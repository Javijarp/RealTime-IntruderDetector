#!/usr/bin/env python3
"""
Test script to verify edge module can communicate with backend.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.models import DetectionEvent
from src.network import simulated_http_post
from src.config import Config
import numpy as np

def test_basic_event():
    """Test sending a basic event without frame."""
    print("\n=== Testing Basic Event (No Frame) ===")
    event = DetectionEvent("Person", 0.85, frame_id=1)
    success = simulated_http_post(event, frame=None)
    print(f"Result: {'✓ SUCCESS' if success else '✗ FAILED'}")
    return success

def test_event_with_frame():
    """Test sending event with a dummy frame."""
    print("\n=== Testing Event With Frame ===")
    event = DetectionEvent("Dog", 0.92, frame_id=2)
    
    # Create a dummy 640x480 image (black)
    dummy_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    success = simulated_http_post(event, frame=dummy_frame)
    print(f"Result: {'✓ SUCCESS' if success else '✗ FAILED'}")
    return success

def main():
    print(f"Testing edge module connection to: {Config.BACKEND_URL}")
    print("="*60)
    
    test1 = test_basic_event()
    test2 = test_event_with_frame()
    
    print("\n" + "="*60)
    print(f"Results: {2 if (test1 and test2) else (1 if (test1 or test2) else 0)}/2 tests passed")
    
    if test1 and test2:
        print("✓ All tests passed! Edge module can communicate with backend.")
        return 0
    else:
        print("✗ Some tests failed. Check backend logs.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
