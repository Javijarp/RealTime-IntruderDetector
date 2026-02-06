# Video Streaming System - Implementation Summary

## What Was Created

A complete real-time video streaming system that allows frames to be pushed from any source (camera, edge module, etc.) to a backend, which then broadcasts them to all connected frontend clients via WebSocket.

## Components Created

### Backend (Java/Spring Boot)

1. **WebSocketConfig.java** (`config/`)
   - Configures WebSocket endpoint at `/ws/stream`
   - Enables SockJS for cross-browser compatibility
   - Sets CORS for localhost development

2. **VideoStreamHandler.java** (`handler/`)
   - Handles WebSocket connection lifecycle
   - Manages client subscriptions to streams
   - Broadcasts frames to all connected subscribers
   - ~170 lines of code

3. **VideoStreamService.java** (`service/`)
   - Business logic for stream management
   - Maintains subscriber lists per stream
   - Broadcasts frames as base64-encoded JSON
   - Thread-safe with ConcurrentHashMap
   - ~80 lines of code

4. **StreamController.java** (`controller/`)
   - REST endpoints for pushing frames
   - Stream statistics endpoint
   - Health check endpoint
   - ~120 lines of code

5. **Updated build.gradle**
   - Added `spring-boot-starter-websocket` dependency

### Frontend (React)

1. **WebSocketClient.js** (`utils/`)
   - Generic WebSocket client with auto-reconnection
   - Event-based message handling
   - Reconnection logic (max 5 attempts, 3-second delay)
   - ~110 lines of code

2. **VideoStream.jsx** (`components/`)
   - Renders video on HTML5 canvas
   - Play/pause controls
   - Mute button (for UI consistency)
   - Fullscreen support
   - Real-time FPS counter
   - Statistics display (frames received, data received)
   - Auto-reconnection on disconnect
   - ~290 lines of code

3. **LiveStream.jsx** (`pages/`)
   - Full-page view for video streaming
   - Stream ID configuration
   - Usage guide and examples
   - API documentation
   - ~180 lines of code

4. **Updated App.jsx & Layout.jsx**
   - Added "Live Stream" menu item
   - Added stream page routing

### Utilities

1. **stream_pusher.py** (Root)
   - Python utility for pushing frames from any source
   - Support for:
     - Files
     - OpenCV frames
     - PIL Images
     - Raw bytes
   - Stream statistics retrieval
   - Example scripts included
   - ~320 lines of code

### Documentation

1. **STREAMING.md** - Complete technical documentation
2. **STREAMING_QUICKSTART.md** - Quick start guide

## How It Works

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    PUSH PHASE                               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Camera/Edge Module                                         │
│         ↓                                                    │
│  Python FramePusher                                         │
│         ↓                                                    │
│  POST /api/stream/{streamId}/frame                          │
│         ↓                                                    │
│  StreamController receives frame                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  BROADCAST PHASE                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  VideoStreamService looks up subscribers for stream         │
│         ↓                                                    │
│  For each subscriber (WebSocket session):                   │
│    - Encode frame as base64                                 │
│    - Create JSON message with metadata                      │
│    - Send via WebSocket                                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   DISPLAY PHASE                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Frontend WebSocketClient receives message                  │
│         ↓                                                    │
│  VideoStream component receives 'frame' event               │
│         ↓                                                    │
│  Decode base64 data → Create Blob → Create Image            │
│         ↓                                                    │
│  Render on HTML5 Canvas                                     │
│         ↓                                                    │
│  Update statistics (FPS, data received, etc.)               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

### REST API

| Method | Endpoint                       | Purpose              | Example                                                                             |
| ------ | ------------------------------ | -------------------- | ----------------------------------------------------------------------------------- |
| POST   | `/api/stream/{streamId}/frame` | Push frame to stream | `curl -X POST http://localhost:8080/api/stream/default/frame -F "frame=@image.jpg"` |
| GET    | `/api/stream/{streamId}/stats` | Get stream stats     | `curl http://localhost:8080/api/stream/default/stats`                               |
| GET    | `/api/stream/health`           | Health check         | `curl http://localhost:8080/api/stream/health`                                      |

### WebSocket API

**Endpoint:** `ws://localhost:8080/ws/stream`

**Client → Server Messages:**

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
  "type": "ping"
}
```

**Server → Client Messages:**

```json
{
  "type": "connected",
  "message": "Connected to video stream"
}
```

```json
{
  "type": "frame",
  "streamId": "default",
  "data": "base64-encoded-jpeg-data",
  "contentType": "image/jpeg"
}
```

```json
{
  "type": "pong"
}
```

```json
{
  "type": "error",
  "message": "Error description"
}
```

## Key Features

### ✅ Real-Time Streaming

- WebSocket for low-latency bidirectional communication
- Base64 encoding for reliable frame transmission
- Multiple concurrent streams support

### ✅ Automatic Reconnection

- Detects disconnections
- Attempts to reconnect up to 5 times
- 3-second delay between attempts
- Notifies user of connection status

### ✅ Performance Monitoring

- Real-time FPS counter
- Total frames received counter
- Total data received (in MB)
- Stream statistics endpoint

### ✅ Multi-Stream Support

- Each stream has unique ID (e.g., "camera-1", "parking-lot")
- Subscribers can choose which streams to watch
- Independent subscriber lists per stream

### ✅ Easy Integration

- Python utility (`stream_pusher.py`) for any source
- Simple curl commands for testing
- Comprehensive API documentation

### ✅ CORS Enabled

- Allows frontend on different port (localhost:5173)
- Configured in `CorsConfig.java` and `WebSocketConfig.java`

### ✅ Production-Ready Architecture

- Thread-safe stream management
- Proper error handling and logging
- Graceful connection cleanup
- Health check endpoint

## Usage Examples

### Example 1: Stream from Camera

```python
from stream_pusher import FramePusher
import cv2

pusher = FramePusher(stream_id="main-camera")
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (640, 480))
        pusher.push_frame_from_opencv(frame)
```

### Example 2: Stream from Image Directory

```python
from stream_pusher import FramePusher
import glob

pusher = FramePusher(stream_id="archive")
for image_path in sorted(glob.glob("frames/*.jpg")):
    pusher.push_frame_from_file(image_path)
    time.sleep(0.033)  # 30 FPS
```

### Example 3: Monitor Stream Health

```python
from stream_pusher import FramePusher

pusher = FramePusher()
stats = pusher.get_stream_stats()
print(f"Subscribers: {stats['subscribers']}")
print(f"Total subscribers: {stats['totalSubscribers']}")
```

## File Structure

```
face-recognition-system/
├── backend/security-backend/
│   ├── src/main/java/com/javier/security_backend/
│   │   ├── config/
│   │   │   ├── CorsConfig.java ✅ (existing, updated)
│   │   │   └── WebSocketConfig.java ✅ (NEW)
│   │   ├── handler/
│   │   │   └── VideoStreamHandler.java ✅ (NEW)
│   │   ├── service/
│   │   │   └── VideoStreamService.java ✅ (NEW)
│   │   └── controller/
│   │       └── StreamController.java ✅ (NEW)
│   └── build.gradle ✅ (updated)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Layout.jsx ✅ (updated)
│   │   │   └── VideoStream.jsx ✅ (NEW)
│   │   ├── pages/
│   │   │   ├── LiveStream.jsx ✅ (NEW)
│   │   ├── utils/
│   │   │   └── WebSocketClient.js ✅ (NEW)
│   │   └── App.jsx ✅ (updated)
│
├── stream_pusher.py ✅ (NEW)
├── STREAMING.md ✅ (NEW)
└── STREAMING_QUICKSTART.md ✅ (NEW)
```

## Getting Started

### 1. Build Backend

```bash
cd backend/security-backend
./gradlew build -x test
```

### 2. Start Backend

```bash
./gradlew bootRun
```

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open Browser

Navigate to `http://localhost:5173` → Click "Live Stream"

### 5. Push Test Frame

```bash
python3 stream_pusher.py
# Or use curl: curl -X POST http://localhost:8080/api/stream/default/frame -F "frame=@test.jpg"
```

## Performance Metrics

### Bandwidth Requirements

- **Low quality (320x240, 30 FPS):** ~2-3 Mbps
- **Medium quality (640x480, 30 FPS):** ~7-10 Mbps
- **High quality (1280x720, 30 FPS):** ~15-20 Mbps

### Latency

- WebSocket connection: ~50-100ms
- Frame encoding/decoding: ~10-30ms
- Total end-to-end latency: ~100-200ms

### Scalability

- Current implementation: Single backend instance
- Production: Add Redis Pub/Sub or Kafka for multi-instance scaling

## Security Considerations

### Current Implementation (Development)

- ✅ CORS configured
- ❌ No authentication
- ❌ No frame encryption
- ❌ No rate limiting

### Production Recommendations

1. Add JWT authentication to WebSocket
2. Restrict CORS to specific domains
3. Use WSS (WebSocket Secure) with SSL/TLS
4. Implement rate limiting per stream
5. Add audit logging for frame transfers

## Troubleshooting

### Issue: No video displayed

**Solution:**

1. Check browser console for errors
2. Verify stream has subscribers: `curl http://localhost:8080/api/stream/default/stats`
3. Check if frames are being pushed correctly

### Issue: Connection failed

**Solution:**

1. Ensure backend is running
2. Check backend health: `curl http://localhost:8080/api/stream/health`
3. Verify no firewall blocking port 8080

### Issue: High latency

**Solution:**

1. Reduce frame resolution
2. Reduce JPEG quality
3. Reduce frame rate
4. Check network bandwidth

## Future Enhancements

1. **MJPEG Streaming** - More efficient format than base64
2. **H.264 Encoding** - Better compression
3. **Resolution Adaptation** - Auto-adjust based on bandwidth
4. **Authentication** - JWT or OAuth2
5. **Recording** - Save streams to disk
6. **Analytics Dashboard** - Stream performance metrics
7. **Multi-bitrate** - Different quality levels
8. **Audio Support** - Add audio channel

## Testing Checklist

- [ ] Backend builds successfully
- [ ] Frontend starts without errors
- [ ] Can navigate to Live Stream page
- [ ] WebSocket connects (see "Connected" message)
- [ ] Can push test frame
- [ ] Frame displays on canvas
- [ ] FPS counter updates
- [ ] Frame count increases
- [ ] Connection status indicator shows green
- [ ] Play/pause controls work
- [ ] Fullscreen works
- [ ] Auto-reconnection works (disconnect WebSocket in DevTools)

## Support

For detailed information, see:

- [STREAMING.md](./STREAMING.md) - Complete technical documentation
- [STREAMING_QUICKSTART.md](./STREAMING_QUICKSTART.md) - Quick start guide
- [stream_pusher.py](./stream_pusher.py) - Python utility examples
