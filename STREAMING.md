# Video Streaming System Documentation

## Overview

The video streaming system enables real-time transmission of video frames from the backend/edge module to the frontend via WebSocket. The architecture consists of:

1. **Backend WebSocket Handler** - Manages client connections and broadcasts frames
2. **Stream Controller** - REST endpoint for pushing frames to streams
3. **Frontend WebSocket Client** - Connects to the WebSocket and handles incoming frames
4. **Video Component** - Renders frames on an HTML5 canvas with playback controls

## Architecture

```
Edge Module / Camera
       ↓
   POST /api/stream/{streamId}/frame
       ↓
Backend StreamController
       ↓
VideoStreamService (manages subscribers)
       ↓
VideoStreamHandler (WebSocket)
       ↓
      WS ↔ Multiple Frontend Clients
       ↓
VideoStream Component
       ↓
HTML5 Canvas (Display)
```

## Backend Components

### 1. WebSocketConfig

**Location:** `src/main/java/com/javier/security_backend/config/WebSocketConfig.java`

Configures WebSocket endpoint at `/ws/stream` with CORS support.

```java
registry.addHandler(videoStreamHandler, "/ws/stream")
    .setAllowedOrigins("http://localhost:5173", "http://localhost:3000")
    .withSockJS();
```

### 2. VideoStreamHandler

**Location:** `src/main/java/com/javier/security_backend/handler/VideoStreamHandler.java`

Manages WebSocket connections and broadcasts frames to all connected clients.

**Key Methods:**

- `afterConnectionEstablished()` - Register new client
- `handleTextMessage()` - Handle client commands (subscribe, unsubscribe, ping)
- `broadcastFrame()` - Send frame to all connected clients
- `afterConnectionClosed()` - Cleanup disconnected client

**Message Types:**

```json
{
  "type": "subscribe",
  "streamId": "default"
}
```

```json
{
  "type": "unsubscribe"
}
```

```json
{
  "type": "frame",
  "streamId": "default",
  "data": "base64-encoded-image-data",
  "contentType": "image/jpeg"
}
```

### 3. VideoStreamService

**Location:** `src/main/java/com/javier/security_backend/service/VideoStreamService.java`

Manages stream subscriptions and broadcasts frames to subscribers.

**Key Methods:**

- `subscribe(streamId, session)` - Subscribe to a stream
- `unsubscribe(session)` - Unsubscribe from all streams
- `broadcastFrame(streamId, data, contentType)` - Broadcast frame to all subscribers
- `getSubscriberCount(streamId)` - Get number of active subscribers

### 4. StreamController

**Location:** `src/main/java/com/javier/security_backend/controller/StreamController.java`

REST endpoints for pushing frames and checking stream status.

**Endpoints:**

#### POST /api/stream/{streamId}/frame

Push a frame to a stream

```bash
curl -X POST http://localhost:8080/api/stream/default/frame \
  -F "frame=@image.jpg" \
  -F "contentType=image/jpeg"
```

Response:

```json
{
  "status": "success",
  "message": "Frame broadcast to 5 subscribers"
}
```

#### GET /api/stream/{streamId}/stats

Get stream statistics

```bash
curl http://localhost:8080/api/stream/default/stats
```

Response:

```json
{
  "streamId": "default",
  "subscribers": 3,
  "totalSubscribers": 5
}
```

#### GET /api/stream/health

Health check

```bash
curl http://localhost:8080/api/stream/health
```

Response:

```json
{
  "status": "UP",
  "service": "Video Stream Service",
  "totalSubscribers": 2
}
```

## Frontend Components

### 1. WebSocketClient

**Location:** `src/utils/WebSocketClient.js`

Generic WebSocket client with reconnection logic.

```javascript
const client = new WebSocketClient("ws://localhost:8080/ws/stream");

client.on("connected", () => {
  console.log("Connected!");
});

client.on("frame", (message) => {
  // Handle frame data
});

client.on("error", (error) => {
  console.error("Error:", error);
});

client.connect();
```

### 2. VideoStream Component

**Location:** `src/components/VideoStream.jsx`

Displays live video stream with controls.

**Props:**

- `streamId` - Stream ID to subscribe to (default: "default")

**Features:**

- Real-time frame rendering on HTML5 canvas
- Play/pause controls
- FPS counter
- Data received counter
- Connection status indicator
- Fullscreen support
- Auto-reconnection on disconnect

**Usage:**

```jsx
<VideoStream streamId="camera-1" />
```

### 3. LiveStream Page

**Location:** `src/pages/LiveStream.jsx`

Full-page view with stream settings and usage guide.

**Features:**

- Stream ID configuration
- Real-time statistics
- Usage documentation
- Settings panel

## Python Streaming Utility

**Location:** `stream_pusher.py`

Helper utility for pushing frames from Python applications.

### Installation

```bash
pip install requests pillow opencv-python
```

### Usage

#### Push from Camera

```python
from stream_pusher import FramePusher
import cv2

pusher = FramePusher(stream_id="camera-1")
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    pusher.push_frame_from_opencv(frame)
```

#### Push from File

```python
pusher = FramePusher(stream_id="default")
pusher.push_frame_from_file("image.jpg")
```

#### Push from PIL Image

```python
from PIL import Image

pusher = FramePusher(stream_id="default")
img = Image.open("photo.jpg")
pusher.push_frame_from_pil(img)
```

#### Get Stream Statistics

```python
stats = pusher.get_stream_stats()
print(stats)
# Output: {'streamId': 'default', 'subscribers': 3, 'totalSubscribers': 5}
```

## Data Flow

### Frame Upload Flow

```
1. Client pushes frame via HTTP POST
   POST /api/stream/{streamId}/frame with file

2. StreamController receives request
   → Extracts frame data and content type

3. StreamController calls VideoStreamService.broadcastFrame()
   → Service looks up all subscribers for that stream

4. VideoStreamService broadcasts to all subscribers
   → Encodes frame as base64 JSON message
   → Sends via WebSocket to each client

5. Frontend VideoStream component receives frame
   → Decodes base64 data
   → Creates image blob
   → Renders on canvas
   → Updates statistics
```

## Configuration

### Backend (application.properties)

```properties
# Default configuration, no special WebSocket settings needed
# CORS is configured in CorsConfig.java
```

### Frontend (Environment Variables)

```javascript
// Hardcoded in src/components/VideoStream.jsx
const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
const wsUrl = `${wsProtocol}//localhost:8080/ws/stream`;
```

To customize, edit the WebSocket URL in `VideoStream.jsx`:

```javascript
const wsUrl = `${wsProtocol}//your-backend-url:8080/ws/stream`;
```

## Performance Considerations

### Frame Size

- **Small frames** (e.g., 320x240): 5-10 KB per frame
- **Medium frames** (e.g., 640x480): 20-50 KB per frame
- **Large frames** (e.g., 1920x1080): 100-200 KB per frame

### Bandwidth

- 30 FPS with 640x480 frames (~30KB each): ~7.2 Mbps
- 15 FPS with 1280x720 frames (~80KB each): ~9.6 Mbps

### Optimization Tips

1. Compress frames using appropriate JPEG quality
2. Reduce frame resolution if bandwidth is limited
3. Limit frame rate (30 FPS is usually sufficient)
4. Close unused stream subscriptions

## Security

### Current Implementation

- ✅ CORS configured for localhost development
- ⚠️ No authentication/authorization on WebSocket

### Production Recommendations

1. **Add Authentication**
   - JWT token validation on WebSocket connection
   - Verify stream access permissions

2. **Restrict CORS**

   ```java
   .setAllowedOrigins("your-domain.com")
   ```

3. **Add Rate Limiting**
   - Limit frame push rate per stream
   - Prevent frame data bombing

4. **Use Secure WebSocket (WSS)**
   - Enable SSL/TLS for production
   - Update WebSocket URL to use `wss://`

5. **Encrypt Sensitive Streams**
   - Add encryption layer for sensitive video streams

## Troubleshooting

### WebSocket Connection Failed

**Problem:** `Access to XMLHttpRequest at 'ws://localhost:8080/ws/stream' from origin 'http://localhost:5173' has been blocked`

**Solution:**

- Ensure backend is running with WebSocket enabled
- Check CORS configuration in `WebSocketConfig.java`
- Verify firewall allows WebSocket traffic

### Frames Not Rendering

**Problem:** Connection successful but no video displayed

**Solution:**

- Verify frames are being pushed to the backend
- Check browser console for frame decoding errors
- Ensure correct stream ID is being subscribed to
- Check stream statistics: `GET /api/stream/{streamId}/stats`

### High Latency/Lag

**Problem:** Video feed is delayed

**Solution:**

- Reduce frame size or resolution
- Reduce frame rate (push less frequently)
- Check network bandwidth
- Monitor backend CPU usage

### Memory Leak in Frontend

**Problem:** Browser memory continuously increases

**Solution:**

- Ensure components properly cleanup on unmount
- Check that blob URLs are revoked: `URL.revokeObjectURL(url)`
- Monitor WebSocket connections are closed

## Examples

### Example 1: Continuous Camera Stream

```python
from stream_pusher import FramePusher
import cv2

pusher = FramePusher(backend_url="http://localhost:8080", stream_id="main-camera")
cap = cv2.VideoCapture(0)

try:
    while True:
        ret, frame = cap.read()
        if ret:
            # Resize for better performance
            frame = cv2.resize(frame, (640, 480))
            pusher.push_frame_from_opencv(frame)
finally:
    cap.release()
```

### Example 2: Multi-Stream Setup

```python
from stream_pusher import FramePusher
import cv2

streams = {
    "front": FramePusher(stream_id="front-door"),
    "back": FramePusher(stream_id="back-door"),
    "parking": FramePusher(stream_id="parking-lot")
}

caps = {name: cv2.VideoCapture(i) for i, name in enumerate(streams.keys())}

try:
    while True:
        for name, cap in caps.items():
            ret, frame = cap.read()
            if ret:
                streams[name].push_frame_from_opencv(frame)
finally:
    for cap in caps.values():
        cap.release()
```

### Example 3: Check Stream Health

```python
from stream_pusher import FramePusher

pusher = FramePusher()
stats = pusher.get_stream_stats()

if stats:
    print(f"Stream: {stats['streamId']}")
    print(f"Active subscribers: {stats['subscribers']}")
    print(f"Total subscribers: {stats['totalSubscribers']}")
```

## API Reference Summary

| Method | Endpoint                     | Purpose               |
| ------ | ---------------------------- | --------------------- |
| POST   | /api/stream/{streamId}/frame | Push frame to stream  |
| GET    | /api/stream/{streamId}/stats | Get stream statistics |
| GET    | /api/stream/health           | Check service health  |
| WS     | /ws/stream                   | WebSocket connection  |

## Maintenance

### Cleanup Old Sessions

The backend automatically cleans up disconnected WebSocket sessions. No manual intervention needed.

### Monitor Stream Health

```bash
# Check if stream service is running
curl http://localhost:8080/api/stream/health

# Get statistics for a specific stream
curl http://localhost:8080/api/stream/default/stats
```

### Scale to Multiple Instances

For production with multiple backend instances, consider:

- **Redis Pub/Sub** for cross-instance broadcasting
- **Kafka** for message queuing
- **Load balancer** with sticky sessions for WebSocket

## Future Enhancements

1. **Compression** - Add MJPEG or H.264 streaming
2. **Resolution Adaptation** - Auto-adjust based on bandwidth
3. **Recording** - Record streams to disk
4. **Analytics** - Track stream performance metrics
5. **Multi-bitrate** - Support different quality levels
6. **Peer-to-Peer** - Direct P2P streaming between clients
7. **Audio Streaming** - Add audio channel support
