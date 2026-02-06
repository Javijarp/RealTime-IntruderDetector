# Live Video Streaming Setup

## Overview

The system now supports continuous live video streaming from the edge module camera to the web frontend through the backend server.

## Architecture

```
Edge Module (Camera) → Backend Server → Frontend (Web Browser)
    [15 FPS]              [WebSocket]        [Canvas Display]
```

### Components

1. **Edge Module** (`edge-module/src/`)
   - Captures frames from camera at ~30 FPS
   - Continuously streams frames to backend at 15 FPS (configurable)
   - Sends frames to `/stream/default/frame` endpoint
   - Runs in a dedicated streaming thread

2. **Backend Server** (`backend/security-backend/`)
   - Receives frames via HTTP POST at `/stream/{streamId}/frame`
   - Broadcasts frames to WebSocket subscribers at `/ws/stream`
   - Handles multiple concurrent viewers
   - Provides connection status and statistics

3. **Frontend** (`frontend/src/`)
   - Connects to WebSocket at `ws://192.168.5.74:8080/ws/stream`
   - Subscribes to the "default" stream
   - Displays frames on HTML canvas with controls
   - Shows FPS, connection status, and statistics

## Configuration

### Edge Module Configuration

Edit `edge-module/src/config.py`:

```python
# Backend Stream URL for continuous video feed
BACKEND_STREAM_URL: str = "http://192.168.5.74:8080/stream/default/frame"

# Enable continuous video streaming to backend
ENABLE_VIDEO_STREAMING: bool = True

# Video stream frame rate (frames per second to send to backend)
STREAM_FPS: int = 15  # Lower than capture FPS to reduce bandwidth
```

### Frontend Configuration

Edit `frontend/src/components/VideoStream.jsx`:

```javascript
// Use the backend server IP directly
const wsHost = "192.168.5.74:8080";  // Backend server address
```

**Important**: Update the IP address to match your backend server's IP address.

## How It Works

### 1. Edge Module Streaming Thread

The edge module runs a dedicated streaming thread that:
- Reads the latest captured frame from shared memory
- Encodes it as JPEG (quality 75% for bandwidth efficiency)
- Sends it via HTTP POST to the backend stream endpoint
- Rate-limits to configured FPS (default 15 FPS)
- Logs statistics every 5 seconds

### 2. Backend Frame Broadcasting

The backend:
- Receives frames at `/stream/default/frame` endpoint
- Base64-encodes the frame data
- Broadcasts to all WebSocket subscribers
- Tracks subscriber count and connection status

### 3. Frontend Display

The frontend:
- Connects via WebSocket and subscribes to stream
- Receives frames as base64-encoded JSON messages
- Decodes and displays on HTML canvas
- Shows FPS counter and connection status
- Provides playback controls (play/pause/fullscreen)

## Testing the Stream

### 1. Start the Backend

```bash
cd backend/security-backend
./gradlew bootRun
```

The backend should be running at `http://192.168.5.74:8080`

### 2. Start the Edge Module

```bash
cd edge-module
python src/main.py
```

You should see:
```
[STREAM] Hilo iniciado. Enviando frames a 15 FPS...
[STREAM] Streaming stats: 75 frames sent, 15.0 FPS
```

### 3. Open the Frontend

```bash
cd frontend
npm start
```

Navigate to: `http://localhost:3000/live-feed`

You should see:
- Live video feed from the edge module camera
- Connection status indicator (green = connected)
- FPS counter showing actual frame rate
- Statistics (frames received, data transferred)

## Troubleshooting

### No Video Feed

1. **Check Backend Connection**
   ```bash
   curl http://192.168.5.74:8080/stream/health
   ```
   Should return: `{"status":"UP","service":"Video Stream Service"}`

2. **Check WebSocket Connection**
   - Open browser console (F12)
   - Look for: `VideoStream connecting to: ws://192.168.5.74:8080/ws/stream`
   - Check for connection errors

3. **Check Edge Module**
   - Verify `ENABLE_VIDEO_STREAMING = True` in config
   - Check logs for `[STREAM]` messages
   - Verify backend URL is correct

### Low Frame Rate

1. **Increase Stream FPS** in `config.py`:
   ```python
   STREAM_FPS: int = 20  # Increase from 15
   ```

2. **Check Network Latency**
   - Ping the backend server
   - Check network bandwidth

3. **Reduce JPEG Quality** in `network.py`:
   ```python
   frame_bytes = _encode_frame(frame, quality=60)  # Lower quality = smaller size
   ```

### High Bandwidth Usage

1. **Lower Stream FPS**:
   ```python
   STREAM_FPS: int = 10  # Reduce from 15
   ```

2. **Lower JPEG Quality**:
   ```python
   frame_bytes = _encode_frame(frame, quality=60)  # Lower quality
   ```

3. **Reduce camera resolution** in edge module capture settings

## Features

- **Real-time streaming**: Low-latency video feed from edge to frontend
- **Automatic reconnection**: Frontend automatically reconnects on disconnect
- **Playback controls**: Play/pause, fullscreen support
- **Statistics**: Live FPS, frame count, data transfer metrics
- **Multiple viewers**: Backend supports multiple concurrent WebSocket connections
- **Bandwidth optimization**: Configurable FPS and JPEG quality

## Performance

- **Capture**: ~30 FPS (camera-dependent)
- **Streaming**: 15 FPS (configurable)
- **Latency**: ~100-300ms (network-dependent)
- **Bandwidth**: ~500KB/s - 1MB/s (depends on resolution and quality)

## API Endpoints

### Backend Endpoints

- `POST /stream/{streamId}/frame` - Upload frame to stream
  - Form data: `frame` (multipart file), `contentType` (string)
  
- `GET /stream/health` - Health check
  - Returns service status and subscriber count
  
- `GET /stream/{streamId}/stats` - Stream statistics
  - Returns subscriber count for specific stream

### WebSocket Messages

#### Client → Server

```json
{"type": "subscribe", "streamId": "default"}
{"type": "unsubscribe"}
{"type": "ping"}
```

#### Server → Client

```json
{"type": "connected", "message": "Connected to video stream"}
{"type": "frame", "streamId": "default", "data": "<base64>", "contentType": "image/jpeg"}
{"type": "pong"}
{"type": "error", "message": "..."}
```

## Future Improvements

- [ ] Add support for multiple camera streams
- [ ] Implement adaptive bitrate based on network conditions
- [ ] Add recording capability
- [ ] Support for H.264 video encoding for better compression
- [ ] Add authentication for WebSocket connections
- [ ] Implement stream health monitoring and alerts
