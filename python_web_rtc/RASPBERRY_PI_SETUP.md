# Raspberry Pi to Laptop Video Streaming with YOLO Processing

## System Architecture

```
┌─────────────────────┐
│  Raspberry Pi       │
│  ✓ Capture video    │
│  ✓ Encode H264      │
│  ✓ Stream via UDP   │
└──────────┬──────────┘
           │ UDP Stream (H264)
           │ 192.168.1.7:5000
           ▼
┌─────────────────────┐
│  Laptop (Host)      │
│  ✓ Receive stream   │
│  ✓ YOLO detection   │
│  ✓ WebRTC server    │
└─────────────────────┘
```

## Prerequisites

### On Raspberry Pi:
```bash
# Install required packages
sudo apt-get install -y ffmpeg libopenjp2-7 libtiff6 libjasper-dev libjasper1

# Install Python packages
pip install picamera2 opencv-python
```

### On Laptop:
```bash
# Install required packages
pip install aiohttp aiortc opencv-contrib-python ultralytics pillow numpy
```

## Configuration

### Step 1: Set Laptop IP on Raspberry Pi

Edit `camera_stream_pi.py` and update:
```python
LAPTOP_IP = "192.168.1.7"  # Change to your laptop's actual IP address
```

**To find your laptop's IP:**
- **Windows**: Open Command Prompt and run `ipconfig` (look for IPv4 Address)
- **Linux/Mac**: Open Terminal and run `hostname -I`

### Step 2: Ensure Laptop is Listening

Verify `core/config.py` has:
```python
CAMERA_TYPE = "opencv"  # Using OpenCV to receive UDP stream
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
```

The laptop automatically listens on UDP port 5000 when you start the web server.

## Running the System

### On Raspberry Pi:
```bash
cd ~/path/to/python_web_rtc
python camera_stream_pi.py
```

You should see:
```
🍓 Raspberry Pi Camera Stream
📤 Streaming to 192.168.1.7:5000
📹 Resolution: 640x480
⏱️  Frame Rate: 30 FPS
```

### On Laptop (in a new terminal):
```bash
cd path/to/python_web_rtc
python app.py
```

You should see:
```
======== Running on http://0.0.0.0:8080 ========
```

### Connect to WebRTC Stream:
1. Open a web browser on your laptop (or any device on the network)
2. Navigate to a client page that connects to `http://localhost:8080/offer`
3. You'll receive the processed video with YOLO detections

## Network Troubleshooting

### Issue: "Pi stream not accessible" error

**Solution 1: Check firewall**
```bash
# On Windows, allow Python through firewall
# Settings → Firewall → Allow an app through firewall
# Add python.exe or your Python script
```

**Solution 2: Verify network connectivity**
```bash
# From Raspberry Pi, ping laptop
ping 192.168.1.7

# From Laptop, ping Raspberry Pi
ping <pi-ip-address>
```

**Solution 3: Check UDP port**
```bash
# On laptop, verify port 5000 is not blocked
# Check if another process is using port 5000
netstat -an | findstr 5000  # Windows
lsof -i :5000               # Linux/Mac
```

### Issue: Slow/laggy video

**Solutions:**
1. Reduce frame rate in `camera_stream_pi.py`: Change `"FrameRate": 30` to `"FrameRate": 15`
2. Reduce bitrate: Change `BITRATE = "4000k"` to `"2000k"`
3. Reduce resolution: Change `FRAME_WIDTH = 640` to `320` (and `FRAME_HEIGHT = 480` to `240`)
4. Increase frame skip rate in `processor.py`: `self.skip_rate = 2` or `3`

## File Structure

```
python_web_rtc/
├── camera_stream_pi.py          # ← Runs on Raspberry Pi
├── app.py                       # ← Runs on Laptop
├── core/
│   └── config.py               # Configuration
├── media/
│   ├── video_source.py         # ← Receives UDP stream
│   └── yolo/
│       ├── detector.py         # YOLO model
│       └── processor.py        # ← Processes frames with YOLO
└── webRTC/
    ├── peer_factory.py         # WebRTC setup
    └── tracks.py               # Video track handling
```

## YOLO Processing Details

The laptop handles all heavy computation:
- **Frame Reception**: `media/video_source.py` receives UDP stream
- **YOLO Detection**: `media/yolo/processor.py` runs YOLO inference
- **Object Tracking**: Identifies target objects (e.g., "cup")
- **Robot Control**: Sends servo positions based on object location
- **WebRTC Streaming**: Sends processed video to clients

## Performance Tips

1. **GPU Acceleration**: If laptop has NVIDIA GPU, install `cuda` and `cudatoolkit` for faster YOLO inference
2. **Model Selection**: `yolov8n.pt` is fast. If accuracy needed, use `yolov8s.pt` or larger
3. **Frame Skipping**: Current setting skips frames for real-time performance
4. **Threading**: Processing uses separate threads to avoid bottlenecks

## Monitoring

Add this to `app.py` for stream status:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show:
- When connections are established
- Frame statistics
- Any errors in the pipeline
