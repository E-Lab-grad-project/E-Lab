from picamera2 import Picamera2
import cv2
from ultralytics import YOLO
import serial
import time
import numpy as np

# ================= SERIAL SETUP =================
ser = None
try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
    time.sleep(2)
    print("🟢 Serial connected to Arduino/ESP32")
except:
    print("⚠ WARNING: Could not open serial port")
    ser = None

# ================= YOLO SETUP =================
model = YOLO('yolov8n.pt')
target_class = 'cup'
class_names = model.names

# ================= PICAMERA2 SETUP =================
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(
    main={"format": "XRGB8888", "size": (640, 480)}
)
picam2.configure(preview_config)
picam2.start()
time.sleep(2)

# ================= ZOOM OUT FUNCTION =================
def set_zoom_out(picam2, zoom_factor=0.8):
    sensor_w, sensor_h = picam2.camera_properties['PixelArraySize']

    crop_w = int(sensor_w * zoom_factor)
    crop_h = int(sensor_h * zoom_factor)

    crop_x = (sensor_w - crop_w) // 2
    crop_y = (sensor_h - crop_h) // 2

    picam2.set_controls({
        "ScalerCrop": (crop_x, crop_y, crop_w, crop_h)
    })

# 🔍 APPLY ZOOM OUT
set_zoom_out(picam2, zoom_factor=0.8)

# ================= TRACKING PARAMS =================
alpha = 0.65
prev_cx = None
prev_cy = None

FRAME_SKIP = 2
frame_count = 0
last_results = None

tracking = False

# ================= HELPER FUNCTIONS =================
def clamp(val, minv, maxv):
    return max(minv, min(maxv, val))

def norm_to_angle(norm):
    angle = int(((norm + 1) / 2) * 180)
    return clamp(angle, 0, 180)

def estimate_distance(area):
    MAX_AREA = 640 * 480 * 0.6
    MIN_AREA = 2000
    area = clamp(area, MIN_AREA, MAX_AREA)
    z = 1 - ((area - MIN_AREA) / (MAX_AREA - MIN_AREA))
    return clamp(z, 0, 1)

def send_robot_state(x, y, z):
    msg = f"X:{x},Y:{y},Z:{z:.2f}\n"
    if ser:
        ser.write(msg.encode())

# ================= MAIN LOOP =================
try:
    while True:
        frame = picam2.capture_array()

        # FIX: BGRA → BGR
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        h, w = frame.shape[:2]
        cx_screen, cy_screen = w / 2, h / 2

        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            tracking = not tracking
            print("🚀 Tracking", "ON" if tracking else "OFF")

        if tracking:
            frame_count += 1
            if frame_count % FRAME_SKIP == 0:
                last_results = model(frame, imgsz=320, conf=0.4, verbose=False)

            if last_results:
                best_box, best_area = None, 0

                for box in last_results[0].boxes:
                    if class_names[int(box.cls[0])] != target_class:
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    area = (x2 - x1) * (y2 - y1)
                    if area > best_area:
                        best_area = area
                        best_box = (x1, y1, x2, y2)

                if best_box:
                    x1, y1, x2, y2 = best_box
                    cx = ((x1 + x2) / 2) - cx_screen
                    cy = ((y1 + y2) / 2) - cy_screen

                    if prev_cx is not None:
                        cx = alpha * prev_cx + (1 - alpha) * cx
                        cy = alpha * prev_cy + (1 - alpha) * cy

                    prev_cx, prev_cy = cx, cy

                    servo_x = norm_to_angle(cx / (w / 2))
                    servo_y = norm_to_angle(-cy / (h / 2))
                    z = estimate_distance(best_area)

                    send_robot_state(servo_x, servo_y, z)

                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.circle(frame, (int(x1+x2)//2, int(y1+y2)//2), 5, (0, 0, 255), -1)

        cv2.imshow("YOLO Tracking (Zoom Out)", frame)

        if key == ord('q'):
            break

finally:
    cv2.destroyAllWindows()
    if ser:
        ser.close()
    picam2.close()
