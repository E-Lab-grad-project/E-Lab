# Quick Start Guide: Pi Camera Stream + YOLO on Laptop

## What You Have Now ✅

Your system is set up to:
1. **Raspberry Pi**: Captures video from Pi camera → streams via UDP to laptop
2. **Laptop**: Receives stream → processes with YOLO → serves via WebRTC

## Before You Start

### 1. Find Your Laptop's IP Address

**On Windows:**
```powershell
ipconfig
```
Look for "IPv4 Address" under your network adapter (usually like `192.168.x.x`)

**Example output:**
```
IPv4 Address . . . . . . . . . . . : 192.168.1.100
```

### 2. Update Raspberry Pi Configuration

Edit `camera_stream_pi.py` on your Raspberry Pi:
```python
LAPTOP_IP = "192.168.1.100"  # Use YOUR laptop's IP from above
```

## Running the System

### Step 1: Start Laptop (HTTP Server with YOLO Processing)

```bash
cd path/to/python_web_rtc
python app.py
```

Expected output:
```
======== Running on http://0.0.0.0:8080 ========
```

✅ Laptop is now listening for Pi stream on port 5000

### Step 2: Test Connection (Optional but Recommended)

In a new terminal on your laptop:
```bash
python test_stream_connection.py
```

This will:
- Check if port 5000 is available
- Wait for frames from Pi
- Display received frames
- Show FPS statistics

### Step 3: Start Raspberry Pi Camera Stream

```bash
cd path/to/python_web_rtc
python camera_stream_pi.py
```

Expected output:
```
🍓 Raspberry Pi Camera Stream
📤 Streaming to 192.168.1.100:5000
📹 Resolution: 640x480
⏱️  Frame Rate: 30 FPS
```

### Step 4: Access the Processed Video

You need a WebRTC client. Create a simple `index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Pi Camera + YOLO</title>
</head>
<body>
    <h1>Raspberry Pi Camera Stream (YOLO Processing)</h1>
    
    <video id="video" width="640" height="480" autoplay></video>
    
    <script src="https://cdn.jsdelivr.net/npm/webrtc-adapter@8"></script>
    <script>
        const pc = new RTCPeerConnection({
            iceServers: [{ urls: ["stun:stun.l.google.com:19302"] }]
        });
        
        pc.addEventListener('track', (e) => {
            if (e.track.kind === 'video') {
                document.getElementById('video').srcObject = e.streams[0];
            }
        });
        
        pc.addTransceiver('video', { direction: 'recvonly' });
        
        pc.createOffer().then(async (offer) => {
            await pc.setLocalDescription(offer);
            
            const response = await fetch('http://localhost:8080/offer', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sdp: pc.localDescription.sdp,
                    type: pc.localDescription.type,
                    processor: "yolo"
                })
            });
            
            const answer = await response.json();
            await pc.setRemoteDescription(new RTCSessionDescription(answer));
        });
    </script>
</body>
</html>
```

Then open `http://localhost:8080/index.html` in your browser.

## If Something Goes Wrong

### Problem: "Pi stream not accessible"

1. **Check firewall** - Allow Python through Windows Firewall
2. **Verify IP address** - Make sure laptop IP in `camera_stream_pi.py` is correct
3. **Test network** - Run `test_stream_connection.py` (Step 2)
4. **Try alternative** - Use `camera_stream_pi_simple.py` instead of `camera_stream_pi.py`

### Problem: Video is laggy/slow

- Reduce frame rate: `"FrameRate": 15` in `camera_stream_pi.py`
- Reduce resolution: Change `640x480` to `320x240`
- Reduce bitrate: Change `4000000` to `2000000`

### Problem: YOLO not detecting objects

- Check `processor.py` line 12: Change target class from `"cup"` to what you want
- Available classes: person, car, cup, bottle, etc.

## File Reference

| File | Purpose | Runs On |
|------|---------|---------|
| `camera_stream_pi.py` | Captures & streams video | Raspberry Pi |
| `app.py` | Web server + YOLO processing | Laptop |
| `test_stream_connection.py` | Network & stream tester | Laptop |
| `media/video_source.py` | UDP stream receiver | Laptop |
| `media/yolo/processor.py` | YOLO object detection | Laptop |
| `media/yolo/detector.py` | YOLO model loader | Laptop |

## Performance Notes

- **GPU**: If your laptop has NVIDIA GPU, install CUDA for 10x faster YOLO processing
- **Model Size**: Using `yolov8n.pt` (nano) for speed. Use `yolov8s.pt` (small) for better accuracy
- **Frame Rate**: Currently 30 FPS. Reduce if CPU usage is high
- **Resolution**: 640x480 is a good balance. Can go up to 1920x1080 for better accuracy

## Next Steps

1. ✅ Verify laptop IP address
2. ✅ Update `camera_stream_pi.py` with laptop IP
3. ✅ Start `app.py` on laptop
4. ✅ Run `test_stream_connection.py` to verify
5. ✅ Start camera stream on Pi
6. ✅ Open WebRTC client in browser
7. 🎉 Watch YOLO detections in real-time!
