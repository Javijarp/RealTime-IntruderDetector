"""
Stream Frame Pusher
Sends frames to the backend streaming service for display on the frontend.
"""

import requests
import cv2
import base64
from io import BytesIO
from PIL import Image
import logging
from typing import Optional
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FramePusher:
    """Pushes frames to the backend streaming service."""

    def __init__(self, backend_url: str = "http://localhost:8080", stream_id: str = "default"):
        """
        Initialize the FramePusher.

        Args:
            backend_url: Backend server URL (default: http://localhost:8080)
            stream_id: Stream ID to send frames to (default: "default")
        """
        self.backend_url = backend_url.rstrip("/")
        self.stream_id = stream_id
        self.endpoint = f"{self.backend_url}/api/stream/{stream_id}/frame"

    def push_frame_from_file(self, image_path: str, content_type: str = "image/jpeg") -> bool:
        """
        Push a frame from a file to the stream.

        Args:
            image_path: Path to the image file
            content_type: Content type of the image (default: image/jpeg)

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(image_path, "rb") as f:
                files = {"frame": f}
                params = {"contentType": content_type}

                response = requests.post(self.endpoint, files=files, params=params, timeout=5)

                if response.status_code == 200:
                    logger.info(f"Frame pushed successfully to stream '{self.stream_id}'")
                    return True
                else:
                    logger.error(f"Failed to push frame: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error pushing frame from file: {e}")
            return False

    def push_frame_from_bytes(self, frame_bytes: bytes, content_type: str = "image/jpeg") -> bool:
        """
        Push a frame from bytes to the stream.

        Args:
            frame_bytes: Frame data as bytes
            content_type: Content type of the frame (default: image/jpeg)

        Returns:
            True if successful, False otherwise
        """
        try:
            files = {"frame": ("frame.jpg", frame_bytes, content_type)}
            params = {"contentType": content_type}

            response = requests.post(self.endpoint, files=files, params=params, timeout=5)

            if response.status_code == 200:
                logger.info(f"Frame pushed successfully to stream '{self.stream_id}'")
                return True
            else:
                logger.error(f"Failed to push frame: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error pushing frame from bytes: {e}")
            return False

    def push_frame_from_opencv(self, cv_frame) -> bool:
        """
        Push a frame from OpenCV to the stream.

        Args:
            cv_frame: OpenCV image frame

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert OpenCV frame (BGR) to JPEG bytes
            ret, buffer = cv2.imencode(".jpg", cv_frame)
            if not ret:
                logger.error("Failed to encode frame")
                return False

            frame_bytes = buffer.tobytes()
            return self.push_frame_from_bytes(frame_bytes, "image/jpeg")
        except Exception as e:
            logger.error(f"Error pushing frame from OpenCV: {e}")
            return False

    def push_frame_from_pil(self, pil_image: Image.Image) -> bool:
        """
        Push a frame from PIL Image to the stream.

        Args:
            pil_image: PIL Image object

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert PIL image to JPEG bytes
            buffer = BytesIO()
            pil_image.save(buffer, format="JPEG")
            frame_bytes = buffer.getvalue()

            return self.push_frame_from_bytes(frame_bytes, "image/jpeg")
        except Exception as e:
            logger.error(f"Error pushing frame from PIL: {e}")
            return False

    def get_stream_stats(self) -> Optional[dict]:
        """
        Get stream statistics.

        Returns:
            Stream stats dict if successful, None otherwise
        """
        try:
            stats_endpoint = f"{self.backend_url}/api/stream/{self.stream_id}/stats"
            response = requests.get(stats_endpoint, timeout=5)

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to get stream stats: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting stream stats: {e}")
            return None


def example_continuous_stream_from_camera():
    """
    Example: Stream frames continuously from a webcam.
    """
    pusher = FramePusher(stream_id="camera-1")

    cap = cv2.VideoCapture(0)  # Use default camera

    if not cap.isOpened():
        logger.error("Failed to open camera")
        return

    frame_count = 0
    last_stats_time = time.time()

    try:
        while True:
            ret, frame = cap.read()

            if not ret:
                logger.error("Failed to read frame from camera")
                break

            # Resize frame for better performance
            frame = cv2.resize(frame, (640, 480))

            # Push frame to stream
            pusher.push_frame_from_opencv(frame)
            frame_count += 1

            # Print stats every 10 seconds
            current_time = time.time()
            if current_time - last_stats_time >= 10:
                stats = pusher.get_stream_stats()
                if stats:
                    logger.info(f"Stream stats: {stats}")
                logger.info(f"Frames pushed: {frame_count}")
                last_stats_time = current_time

            # Small delay to avoid overwhelming the server
            time.sleep(0.033)  # ~30 FPS

    except KeyboardInterrupt:
        logger.info("Streaming stopped by user")
    finally:
        cap.release()
        logger.info(f"Total frames pushed: {frame_count}")


def example_stream_from_files():
    """
    Example: Stream frames from a directory of image files.
    """
    import glob
    import os

    pusher = FramePusher(stream_id="file-stream")

    image_dir = "./frames"
    image_extensions = ["*.jpg", "*.jpeg", "*.png"]

    if not os.path.exists(image_dir):
        logger.error(f"Directory not found: {image_dir}")
        return

    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(image_dir, ext)))

    image_files.sort()

    if not image_files:
        logger.error("No image files found in directory")
        return

    logger.info(f"Found {len(image_files)} image files")

    for image_path in image_files:
        logger.info(f"Pushing frame: {image_path}")
        pusher.push_frame_from_file(image_path)
        time.sleep(0.033)  # ~30 FPS


if __name__ == "__main__":
    # Example: Stream from camera
    # example_continuous_stream_from_camera()

    # Example: Stream from files
    # example_stream_from_files()

    # Simple example: Push a single frame
    pusher = FramePusher(stream_id="default")
    print("Frame Pusher initialized")
    print(f"Endpoint: {pusher.endpoint}")
    print("\nUsage:")
    print("  pusher.push_frame_from_file('image.jpg')")
    print("  pusher.push_frame_from_opencv(frame)")
    print("  pusher.get_stream_stats()")
