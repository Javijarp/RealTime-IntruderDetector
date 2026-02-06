# Quick Start: Video Streaming

## Setup (5 minutes)

### 1. Build Backend with WebSocket Support

```bash
cd backend/security-backend
./gradlew build -x test
```

### 2. Start Backend

```bash
./gradlew bootRun
# Backend running on http://localhost:8080
```

### 3. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 4. Start Frontend

```bash
npm run dev
# Frontend running on http://localhost:5173
```

### 5. Navigate to Live Stream

Open browser and go to: `http://localhost:5173`
Click "Live Stream" in the sidebar

## Push Test Frame

### Using curl (Quick Test)

```bash
# Create a simple test image
curl -X POST http://localhost:8080/api/stream/default/frame \
  -F "frame=@/path/to/image.jpg" \
  -F "contentType=image/jpeg"
```

### Using Python

```python
from stream_pusher import FramePusher

pusher = FramePusher(stream_id="default")
pusher.push_frame_from_file("image.jpg")
print(pusher.get_stream_stats())
```

### Using OpenCV

```python
from stream_pusher import FramePusher
import cv2

pusher = FramePusher(stream_id="camera-1")
cap = cv2.VideoCapture(0)

for i in range(30):  # 30 frames
    ret, frame = cap.read()
    if ret:
        pusher.push_frame_from_opencv(frame)

cap.release()
```

## What You Should See

1. **Frontend**: Live Stream page with black canvas
2. **Console**: "Connected to video stream" message
3. **Push frame**: Canvas displays the image
4. **Stats**: Frame count and data received updates

## Troubleshooting

### No video displayed?

1. Check console for errors
2. Verify frame is being pushed: `curl http://localhost:8080/api/stream/default/stats`
3. Should show `subscribers: 1` (your browser tab)

### Connection failed?

1. Backend running? `curl http://localhost:8080/api/stream/health`
2. Check CORS: Should see `status: "UP"`
3. Frontend port correct? Should be `http://localhost:5173`

### Want to stream from camera continuously?

```bash
cd face-recognition-system
python3 stream_pusher.py
```

Then uncomment `example_continuous_stream_from_camera()` at the bottom

## Key Files

| File                                      | Purpose                           |
| ----------------------------------------- | --------------------------------- |
| `backend/.../WebSocketConfig.java`        | WebSocket configuration           |
| `backend/.../VideoStreamHandler.java`     | Frame broadcasting                |
| `backend/.../StreamController.java`       | REST endpoints                    |
| `frontend/src/components/VideoStream.jsx` | Video display component           |
| `frontend/src/pages/LiveStream.jsx`       | Live stream page                  |
| `stream_pusher.py`                        | Python utility for pushing frames |

## Common Tasks

### Change Stream ID

Edit `src/pages/LiveStream.jsx`:

```javascript
const [streamId, setStreamId] = useState("camera-1");
```

### Change Backend URL (Production)

Edit `src/components/VideoStream.jsx`:

```javascript
const wsUrl = `${wsProtocol}//your-backend-domain:8080/ws/stream`;
```

### Increase Frame Rate

Reduce delay in your pushing code (lower = faster):

```python
time.sleep(0.016)  # ~60 FPS instead of 30 FPS
```

### Monitor Stream

```bash
# Get subscriber count
curl http://localhost:8080/api/stream/default/stats

# Check overall health
curl http://localhost:8080/api/stream/health
```

## Architecture at a Glance

```
Camera/Edge Module
       ↓ (JPEG frames)
  Push to POST /api/stream/{streamId}/frame
       ↓
  Backend StreamController
       ↓
  VideoStreamService (broadcasts to all subscribers)
       ↓
  WebSocket /ws/stream (sends base64 frames)
       ↓
  Frontend WebSocket Client
       ↓
  HTML5 Canvas (displays video)
```

## Performance Tips

1. **Resolution**: Lower resolution = faster streaming

   ```python
   frame = cv2.resize(frame, (640, 480))
   ```

2. **JPEG Quality**: Lower quality = smaller file size

   ```python
   _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
   ```

3. **Frame Rate**: 15-30 FPS is usually sufficient

   ```python
   time.sleep(0.033)  # ~30 FPS
   ```

4. **Multiple Streams**: Use different stream IDs
   ```python
   pusher1 = FramePusher(stream_id="camera-1")
   pusher2 = FramePusher(stream_id="camera-2")
   ```

## Next Steps

- Read [STREAMING.md](./STREAMING.md) for detailed documentation
- Integrate with edge module frame processing
- Add authentication for production
- Scale to multiple streams
