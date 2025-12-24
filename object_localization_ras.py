from picamera2 import Picamera2
import cv2
from ultralytics import YOLO
import serial
import time
import math
import numpy as np

# ================= SERIAL SETUP =================
ser = None
try:
    ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)  # عدل البورت لو مختلف
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

# ================= TRACKING PARAMS =================
alpha = 0.65
prev_cx = None
prev_cy = None

FRAME_SKIP = 2
frame_count = 0
last_results = None

# ================= START FLAG =================
tracking = False  # toggle start/stop

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
    grip_state = "CLOSE" if z < 0.10 else "OPEN"
    msg = f"X:{x},Y:{y},Z:{z:.2f}\n"

    print("\n" + "=" * 60)
    print("🤖 ROBOT COMMAND")
    print(f"Base (X)        : {x}")
    print(f"Shoulder (Y)    : {y}")
    print(f"Distance (Z)    : {z:.2f}")
    print(f"Gripper         : {grip_state}")
    print(f"Serial Message  : {msg.strip()}")
    print("=" * 60)

    if ser is None:
        print("[NO SERIAL] Skipping send")
        return

    try:
        ser.write(msg.encode())
    except Exception as e:
        print("❌ Serial error:", e)

# ================= MAIN LOOP =================
try:
    while True:
        # Capture frame from Pi Camera
        frame = picam2.capture_array()

        # 🔥 FIX: Convert from BGRA (4 channels) → BGR (3 channels)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        h, w = frame.shape[:2]
        screen_cx = w / 2
        screen_cy = h / 2

        key = cv2.waitKey(1) & 0xFF

        # ===== TOGGLE TRACKING =====
        if key == ord('s'):
            tracking = not tracking
            state_str = "STARTED" if tracking else "STOPPED"
            print(f"🚀 Tracking {state_str}")

        # ===== DRAW STATUS TEXT =====
        status_text = "Tracking ON" if tracking else "Press 'S' to START"
        color = (0, 255, 0) if tracking else (0, 0, 255)
        cv2.putText(
            frame, status_text, (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2
        )

        if tracking:
            frame_count += 1
            if frame_count % FRAME_SKIP == 0:
                last_results = model(
                    frame,
                    imgsz=320,
                    conf=0.4,
                    verbose=False
                )

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

                    cx = ((x1 + x2) / 2) - screen_cx
                    cy = ((y1 + y2) / 2) - screen_cy

                    if prev_cx is None:
                        prev_cx, prev_cy = cx, cy
                    else:
                        cx = alpha * prev_cx + (1 - alpha) * cx
                        cy = alpha * prev_cy + (1 - alpha) * cy
                        prev_cx, prev_cy = cx, cy

                    cx_norm = cx / (w / 2)
                    cy_norm = cy / (h / 2)

                    servo_x = norm_to_angle(cx_norm)
                    servo_y = norm_to_angle(-cy_norm)
                    z_dist = estimate_distance(best_area)

                    send_robot_state(servo_x, servo_y, z_dist)

                    # ===== DRAW BOX & CENTER =====
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cx_pix = int((x1 + x2) / 2)
                    cy_pix = int((y1 + y2) / 2)
                    cv2.circle(frame, (cx_pix, cy_pix), 5, (0, 0, 255), -1)

                    cv2.putText(
                        frame, f"X:{servo_x} Y:{servo_y}", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2
                    )
                    cv2.putText(
                        frame, f"Z:{z_dist:.2f}", (10, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2
                    )

        # ===== SHOW FRAME =====
        cv2.imshow("YOLO X/Y/Z Tracking", frame)

        if key == ord('q'):
            break

finally:
    cv2.destroyAllWindows()
    if ser:
        ser.close()
    picam2.close()
