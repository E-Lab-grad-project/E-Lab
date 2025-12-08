from ultralytics import YOLO
import cv2
import numpy as np
import serial
import time

# ---------------- SERIAL SETUP (with try/except) ----------------
ser = None
try:
    ser = serial.Serial('COM3', 9600, timeout=1)
    time.sleep(2)
    print("Serial connected to Arduino on COM3")
except Exception as e:
    print("⚠ WARNING: Could not open serial port (Arduino not connected?)")
    ser = None
# ----------------------------------------------------------------

model = YOLO('yolov8n.pt')

target_class = 'cup'

prev_center = None
alpha = 0.65

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

class_names = model.names

def convert_to_angle(x_norm):
    """
    x_norm: -1 → +1  (screen left → right)
    Output: servo angle (0 → 180), center at 90
    """
    angle = int(((x_norm + 1) / 2) * 180)
    angle = max(0, min(180, angle))
    return angle


def send_servo(x_norm):
    angle = convert_to_angle(x_norm)

    # If Arduino NOT connected → print angle only
    if ser is None:
        print(f"[NO ARDUINO] Servo Angle = {angle}")
        return

    # If Arduino connected → send angle
    try:
        msg = f"{angle}\n"
        ser.write(msg.encode())
        print(f"[SENT] Servo Angle = {angle}")
    except Exception as e:
        print("⚠ ERROR sending to servo:", e)


while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Could not read frame.")
        break

    frame = cv2.flip(frame, 1)

    results = model(frame, imgsz=640, verbose=False)
    frame_h, frame_w = frame.shape[:2]

    screen_cx = frame_w / 2

    best_target = None
    best_area = 0

    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        label = class_names[cls_id]

        if label != target_class:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        area = (x2 - x1) * (y2 - y1)

        if area > best_area:
            best_area = area
            best_target = (x1, y1, x2, y2)

    if best_target:
        x1, y1, x2, y2 = best_target
        w = x2 - x1
        h = y2 - y1

        obj_cx = x1 + w / 2
        obj_cy = y1 + h / 2

        raw_cx = obj_cx - screen_cx

        cx = raw_cx
        if prev_center is None:
            prev_center = (cx,)
        else:
            cx = alpha * prev_center[0] + (1 - alpha) * cx
            prev_center = (cx,)

        cx_norm = cx / (frame_w / 2)

        # -------- SEND TO SERVO --------
        send_servo(cx_norm)

        print("\n=== CUP DETECTED ===")
        print(f"X(center=0): {raw_cx:.2f}")
        print(f"Normalized X: {cx_norm:.3f}")

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)
        cv2.circle(frame, (int(obj_cx), int(obj_cy)), 6, (0,0,255), -1)

        display_text = f"X:{raw_cx:.1f}"
        cv2.putText(frame, display_text,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv2.imshow("YOLO Tracking + Servo Control", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

if ser is not None:
    ser.close()
