# ================= IMPORTS =================
import cv2
import serial
import time
import asyncio
import numpy as np
from ultralytics import YOLO
from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from av import VideoFrame
from aiohttp import web

# ================= SERIAL SETUP =================
ser = None
try:
    ser = serial.Serial('COM8', 115200, timeout=1)
    time.sleep(2)
    print("🟢 Serial connected to Arduino on COM8")
except:
    print("⚠ WARNING: Could not open serial port")
    ser = None

# ================= YOLO SETUP =================
model = YOLO('yolov8n.pt')
target_class = 'cup'
class_names = model.names

# ================= CAMERA SETUP =================
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

if not cap.isOpened():
    print("Error: Could not open camera")
    exit()

# ================= TRACKING PARAMS =================
alpha = 0.65
prev_center = None
FRAME_SKIP = 2
frame_count = 0
last_results = None
current_servo_angle = 90

# ================= HELPER FUNCTIONS =================
def convert_to_angle(x_norm):
    angle = int(((x_norm + 1) / 2) * 180)
    return max(0, min(180, angle))

def send_servo(x_norm):
    global current_servo_angle
    angle = convert_to_angle(x_norm)
    current_servo_angle = angle

    if ser is None:
        print(f"[NO ARDUINO] Servo={angle}")
        return

    try:
        ser.write(f"{angle}\n".encode())
    except:
        pass

def send_grip(close=True):
    if ser is None:
        print("[NO ARDUINO]", "GRIP" if close else "OPEN")
        return

    try:
        ser.write(b"GRIP\n" if close else b"OPEN\n")
    except:
        pass

# ================= VIDEO STREAM TRACK =================
class OpenCVVideoTrack(VideoStreamTrack):
    def __init__(self):
        super().__init__()
        self.frame = None

    async def recv(self):
        await asyncio.sleep(1 / 15)  # 15 FPS
        if self.frame is None:
            img = np.zeros((480, 640, 3), dtype=np.uint8)
        else:
            img = self.frame
        video_frame = VideoFrame.from_ndarray(img, format="bgr24")
        video_frame.pts, video_frame.time_base = await self.next_timestamp()
        return video_frame

video_track = OpenCVVideoTrack()

# ================= WEBRTC HANDLER =================
pcs = set()

async def offer_handler(request):
    params = await request.json()
    offer_sdp = params["sdp"]
    offer_type = params["type"]

    pc = RTCPeerConnection()
    pcs.add(pc)
    pc.addTrack(video_track)

    offer = RTCSessionDescription(sdp=offer_sdp, type=offer_type)
    await pc.setRemoteDescription(offer)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

# ================= MAIN LOOP =================
async def main_loop():
    global frame_count, last_results, prev_center

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            video_track.frame = frame.copy()

            h, w = frame.shape[:2]
            screen_cx = w / 2

            # ---------- YOLO INFERENCE ----------
            frame_count += 1
            if frame_count % FRAME_SKIP == 0:
                last_results = model(frame, imgsz=320, conf=0.4, verbose=False)

            if last_results:
                best_box = None
                best_area = 0

                for box in last_results[0].boxes:
                    cls_id = int(box.cls[0])
                    if class_names[cls_id] != target_class:
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    area = (x2 - x1) * (y2 - y1)

                    if area > best_area:
                        best_area = area
                        best_box = (x1, y1, x2, y2)

                if best_box:
                    x1, y1, x2, y2 = best_box
                    cx = (x1 + x2) / 2 - screen_cx

                    if prev_center is None:
                        prev_center = cx
                    else:
                        cx = alpha * prev_center + (1 - alpha) * cx
                        prev_center = cx

                    cx_norm = cx / (w / 2)
                    send_servo(cx_norm)

                    # ---------- DRAW BOX ----------
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cx_pix = int((x1 + x2) / 2)
                    cy_pix = int((y1 + y2) / 2)
                    cv2.circle(frame, (cx_pix, cy_pix), 5, (0, 0, 255), -1)

                    # ---------- ANGLE TEXT ----------
                    text = f"X Axis: {current_servo_angle}°"
                    text_x = x1
                    text_y = max(20, y1 - 10)
                    cv2.putText(frame, text, (text_x, text_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # cv2.imshow("YOLO Tracking + Servo Control", frame)

            # key = cv2.waitKey(1) & 0xFF
            # if key == ord('q'):
            #     break
            # elif key == ord('g'):
            #     send_grip(True)
            # elif key == ord('o'):
            #     send_grip(False)

            await asyncio.sleep(0)

    finally:
        cap.release()
        cv2.destroyAllWindows()
        if ser:
            ser.close()
        coros = [pc.close() for pc in pcs]
        await asyncio.gather(*coros)

# ================= RUN =================
async def main():
    # Start aiohttp web server
    app = web.Application()
    app.router.add_post("/offer", offer_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "192.168.1.13", 8080)
    await site.start()
    print("🟢 HTTP signaling server running at http://0.0.0.0:8080")

    # Start main loop
    await main_loop()

if __name__ == "__main__":
    asyncio.run(main())
