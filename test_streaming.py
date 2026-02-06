#!/usr/bin/env python3
"""
Test script to verify video streaming setup.
Tests connectivity between edge module and backend.
"""

import sys
import time
import requests
import cv2
import io

# Configuration
BACKEND_URL = "http://192.168.5.74:8080/api"
STREAM_ENDPOINT = f"{BACKEND_URL}/stream/default/frame"
HEALTH_ENDPOINT = f"{BACKEND_URL}/stream/health"


def test_backend_connection():
    """Test if backend is accessible."""
    print("1. Testing backend connection...")
    try:
        response = requests.get(HEALTH_ENDPOINT, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Backend is UP")
            print(f"   - Service: {data.get('service', 'N/A')}")
            print(f"   - Subscribers: {data.get('totalSubscribers', 0)}")
            return True
        else:
            print(f"   ✗ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ✗ Failed to connect to backend: {e}")
        return False


def test_frame_upload():
    """Test uploading a frame to the stream endpoint."""
    print("\n2. Testing frame upload...")
    try:
        import numpy as np
        
        # Create a simple test frame (320x240 with colored background and text)
        print("   - Generating test frame...")
        frame = np.zeros((240, 320, 3), dtype=np.uint8)
        
        # Add a blue background
        frame[:, :] = (50, 100, 150)  # BGR format
        
        # Add text
        cv2.putText(frame, "Test Frame", (50, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, "Streaming Test", (30, 180), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
        
        # Encode frame as JPEG
        success, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            print("   ✗ Failed to encode test frame")
            return False
        
        frame_bytes = encoded.tobytes()
        print(f"   - Frame size: {len(frame_bytes)} bytes")
        
        # Upload frame
        files = {
            'frame': ('test_frame.jpg', frame_bytes, 'image/jpeg')
        }
        data = {
            'contentType': 'image/jpeg'
        }
        
        response = requests.post(STREAM_ENDPOINT, data=data, files=files, timeout=5)
        
        if response.status_code in [200, 201]:
            result = response.json()
            print(f"   ✓ Frame uploaded successfully")
            print(f"   - Status: {result.get('status', 'N/A')}")
            print(f"   - Message: {result.get('message', 'N/A')}")
            return True
        else:
            print(f"   ✗ Upload failed with status {response.status_code}")
            print(f"   - Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ✗ Error during frame upload: {e}")
        return False


def test_continuous_streaming(duration=5):
    """Test continuous frame streaming."""
    print(f"\n3. Testing continuous streaming ({duration} seconds)...")
    try:
        import numpy as np
        
        # Create base test frame with colored background
        base_frame = np.zeros((240, 320, 3), dtype=np.uint8)
        base_frame[:, :] = (50, 100, 150)  # Blue background (BGR)
        
        start_time = time.time()
        frames_sent = 0
        
        while (time.time() - start_time) < duration:
            # Create frame with counter
            frame = base_frame.copy()
            cv2.putText(frame, f"Frame {frames_sent}", (50, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
            # Encode and send
            success, encoded = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 75])
            if success:
                frame_bytes = encoded.tobytes()
                files = {'frame': ('frame.jpg', frame_bytes, 'image/jpeg')}
                data = {'contentType': 'image/jpeg'}
                
                try:
                    response = requests.post(STREAM_ENDPOINT, data=data, files=files, timeout=2)
                    if response.status_code in [200, 201]:
                        frames_sent += 1
                except:
                    pass
            
            time.sleep(0.066)  # ~15 FPS
        
        elapsed = time.time() - start_time
        fps = frames_sent / elapsed
        print(f"   ✓ Sent {frames_sent} frames in {elapsed:.1f}s ({fps:.1f} FPS)")
        return True
        
    except Exception as e:
        print(f"   ✗ Error during continuous streaming: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Video Streaming Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Backend connection
    results.append(test_backend_connection())
    
    if not results[0]:
        print("\n⚠ Backend is not accessible. Check if backend is running.")
        print("  Start backend with: cd backend/security-backend && ./gradlew bootRun")
        sys.exit(1)
    
    # Test 2: Frame upload
    results.append(test_frame_upload())
    
    # Test 3: Continuous streaming (optional)
    if all(results):
        try:
            results.append(test_continuous_streaming(5))
        except KeyboardInterrupt:
            print("\n   - Test interrupted by user")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Backend Connection: {'✓ PASS' if results[0] else '✗ FAIL'}")
    print(f"Frame Upload:       {'✓ PASS' if results[1] else '✗ FAIL'}")
    if len(results) > 2:
        print(f"Continuous Stream:  {'✓ PASS' if results[2] else '✗ FAIL'}")
    
    if all(results):
        print("\n✓ All tests passed! Streaming setup is working correctly.")
        print("\nNext steps:")
        print("1. Start the edge module: cd edge-module && python src/main.py")
        print("2. Open the frontend: http://localhost:3000/live-feed")
        print("3. You should see the live camera feed")
    else:
        print("\n✗ Some tests failed. Please check the configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
