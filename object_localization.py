from ultralytics import YOLO
import cv2
import serial
import time

# ================= SERIAL SETUP =================
ser = None
try:
    ser = serial.Serial('COM8', 115200, timeout=1)
    time.sleep(2)
    print("Serial connected to Arduino on COM8")
except:
    print("⚠ WARNING: Could not open serial port")
    ser = None

# ================= YOLO SETUP =================
model = YOLO('yolov8n.pt')
target_class = 'person'
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

# ================= MAIN LOOP =================
try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)

        h, w = frame.shape[:2]
        screen_cx = w / 2

        # ---------- YOLO INFERENCE ----------
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

                # ---------- DRAW ANGLE TEXT ABOVE BOX ----------
                text = f"X Axis: {current_servo_angle}°"
                text_x = x1
                text_y = max(20, y1 - 10)  # prevent going outside frame

                cv2.putText(
                    frame,
                    text,
                    (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 255),  # YELLOW
                    2
                )

        cv2.imshow("YOLO Tracking + Servo Control", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('g'):
            send_grip(True)
        elif key == ord('o'):
            send_grip(False)

# ================= CLEANUP =================
finally:
    cap.release()
    cv2.destroyAllWindows()
    if ser:
        ser.close()
