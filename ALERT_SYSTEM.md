# Real-Time Alert System

## Overview

The system now includes a **real-time alert notification** that triggers when a new entity (Person or Dog) is detected after a period of no detections. Alerts are pushed to the frontend via WebSocket with the detection frame image.

## How It Works

### Backend Alert Service

**State Machine:**
```
No Entities (30s+) → First Detection → 🚨 TRIGGER ALERT → Active Detection State
                                                              ↓
                                              (30s no detection) → Back to No Entities
```

**Key Features:**
- Tracks time since last detection
- Enters "no entity state" after 30 seconds with no detections
- When first entity appears after this period → Broadcasts alert to all connected WebSocket clients
- Alert includes: entity type, confidence, timestamp, and frame image (if available)

### Frontend Alert Component

**Features:**
- Full-screen overlay popup
- Shows detection frame image
- Entity icon (👤 for Person, 🐕 for Dog)
- Detection details (type, confidence, timestamp)
- Auto-closes after 10 seconds
- Manual "Acknowledge" button
- Smooth animations

**Connection Status:**
- Shows orange indicator if WebSocket disconnected
- Auto-reconnects with exponential backoff

## API Endpoints

### Get Alert State
```bash
curl http://192.168.5.74:8080/api/alerts/state
```

**Response:**
```json
{
  "inNoEntityState": true,
  "lastDetectionTime": "2026-02-06T14:30:00Z",
  "secondsSinceLastDetection": 45
}
```

### Reset Alert State
```bash
curl -X POST http://192.168.5.74:8080/api/alerts/reset
```

Useful for testing - resets to initial state.

## Testing the Alert System

### 1. Open Frontend
Navigate to: `http://192.168.5.74:3000`

The WebSocket connection will establish automatically.

### 2. Verify Connection
Check browser console for: `Alert WebSocket connected`

Or check backend state:
```bash
curl http://192.168.5.74:8080/api/alerts/state
```

### 3. Trigger an Alert

**Option A: Using Edge Module (Recommended)**

Run the edge module after ensuring no detections for 30+ seconds:

```bash
cd edge-module
python3 src/main.py
```

Wait 30 seconds with no detections, then trigger a detection (walk in front of camera).

**Option B: Manual API Test**

1. Reset alert state:
```bash
curl -X POST http://192.168.5.74:8080/api/alerts/reset
```

2. Wait 1 second (simulates "no entity" period)

3. Send detection event with frame:
```bash
curl -X POST http://192.168.5.74:8080/api/events \
  -F "eventId=999" \
  -F "entityType=Person" \
  -F "confidence=0.95" \
  -F "frameId=1" \
  -F "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -F "frameImage=@test_image.jpg"
```

(Replace `test_image.jpg` with an actual image file)

**Option C: Create Dummy Frame**

```bash
# Create a simple test image
convert -size 640x480 xc:blue -pointsize 72 -fill white \
  -annotate +200+250 "TEST DETECTION" test_frame.jpg

# Send detection
curl -X POST http://192.168.5.74:8080/api/events \
  -F "eventId=$(date +%s)" \
  -F "entityType=Person" \
  -F "confidence=0.92" \
  -F "frameId=1" \
  -F "timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  -F "frameImage=@test_frame.jpg"
```

### 4. Expected Behavior

1. **First Detection after 30s:**
   - Backend logs: `🚨 ALERT: First Person detected after period of no entities!`
   - Frontend: Alert popup appears with image and details
   - Auto-closes after 10 seconds or click "Acknowledge"

2. **Subsequent Detections (within 30s):**
   - No alert triggered (already in active state)
   - Events still saved to database

3. **After 30s of No Detections:**
   - System returns to "no entity" state
   - Next detection will trigger another alert

## WebSocket Message Format

**Alert Message:**
```json
{
  "type": "alert",
  "eventId": 123,
  "entityType": "Person",
  "confidence": 0.95,
  "timestamp": "2026-02-06T14:30:00Z",
  "message": "New Person detected!",
  "imageData": "base64_encoded_image_data...",
  "imageType": "image/jpeg"
}
```

## Configuration

### Adjust No-Entity Threshold

Edit `AlertService.java` line 24:
```java
private static final long NO_ENTITY_THRESHOLD_SECONDS = 30;
```

Change to desired seconds (e.g., 60 for 1 minute).

### WebSocket URL

Frontend automatically detects the backend URL. To override, edit `App.tsx`:
```typescript
const wsUrl = `ws://your-backend-url:8080/ws/stream`;
```

## Troubleshooting

### Alert Not Appearing

1. **Check WebSocket Connection:**
   - Open browser console
   - Look for "Alert WebSocket connected"
   - Check for connection errors

2. **Verify Backend State:**
```bash
curl http://192.168.5.74:8080/api/alerts/state
```

Should show `"inNoEntityState": true` before first detection.

3. **Check Backend Logs:**
```bash
docker logs -f face_recognition_backend | grep -i alert
```

Look for:
- `🚨 ALERT: First Person detected...`
- `Alert broadcast to X clients`

### Alert Image Not Showing

- Ensure frame data is being sent with detection event
- Check that `frameImage` parameter is included in multipart request
- Verify image is valid JPEG/PNG

### No Reconnection After Disconnect

- Check backend is running: `docker ps`
- Restart backend: `docker-compose restart backend`
- Clear browser cache and reload

## Architecture

```
Edge Module
    ↓
  POST /api/events (multipart with frame)
    ↓
DetectionEventController
    ↓
AlertService.processDetection()
    ↓
[Check if first detection after 30s]
    ↓
VideoStreamService.getAllSessions()
    ↓
Broadcast via WebSocket to all clients
    ↓
Frontend receives "alert" message
    ↓
Alert Component displays popup
```

## Files Modified/Created

### Backend
- `AlertService.java` - Alert state machine and broadcasting
- `DetectionEventController.java` - Integrated alert processing
- `VideoStreamService.java` - Added `getAllSessions()` method

### Frontend
- `Alert.tsx` - Alert popup component
- `Alert.css` - Alert styling
- `useAlertWebSocket.ts` - WebSocket hook for alerts
- `App.tsx` - Integrated alert system globally

## Production Considerations

1. **Scaling:** Currently broadcasts to all WebSocket sessions. For high-scale deployments, consider Redis pub/sub.

2. **Authentication:** Add token validation to WebSocket connections.

3. **Rate Limiting:** Prevent alert spam if many detections occur rapidly.

4. **Custom Thresholds:** Allow per-user configuration of no-entity threshold.

5. **Mobile Push:** Integrate with FCM/APNS for mobile app alerts.

## Next Steps

1. Test with real edge module and camera
2. Adjust threshold timing as needed
3. Add sound notification (browser permission required)
4. Store alert history in database
5. Add alert filtering by entity type (Person/Dog)
