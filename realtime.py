import cv2
import time
import numpy as np
from collections import deque, Counter
from ultralytics import YOLO

# =====================================================
# LOAD MODEL
# =====================================================

model = YOLO("best (7).pt")

# =====================================================
# CAMERA
# =====================================================

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# =====================================================
# SETTINGS
# =====================================================

CONF_THRESHOLD = 0.4

# Store color history
color_histories = {}

# Store smoothed boxes
box_history = {}

# =====================================================
# LIGHT NORMALIZATION
# =====================================================

def normalize_lighting(img):

    # Gamma correction
    gamma = 1.1

    look_up_table = np.empty((1, 256), np.uint8)

    for i in range(256):

        look_up_table[0, i] = np.clip(
            pow(i / 255.0, gamma) * 255.0,
            0,
            255
        )

    img = cv2.LUT(img, look_up_table)

    # CLAHE
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    l = clahe.apply(l)

    merged = cv2.merge((l, a, b))

    normalized = cv2.cvtColor(
        merged,
        cv2.COLOR_LAB2BGR
    )

    return normalized

# =====================================================
# BOX SMOOTHING
# =====================================================

def smooth_box(object_id, box, alpha=0.5):

    if object_id not in box_history:

        box_history[object_id] = box

        return box

    old_box = box_history[object_id]

    smoothed = [

        int(
            alpha * old_box[i] +
            (1 - alpha) * box[i]
        )

        for i in range(4)
    ]

    box_history[object_id] = smoothed

    return smoothed

# =====================================================
# LIQUID COLOR DETECTION  (FIXED)
# =====================================================

def detect_liquid_color(roi):

    if roi.size == 0:
        return "unknown"

    roi = cv2.resize(roi, (100, 100))

    roi = normalize_lighting(roi)

    roi = cv2.GaussianBlur(roi, (5, 5), 0)

    # --------------------------------------------------
    # FIX 5: Elliptical center mask to exclude glass walls
    # --------------------------------------------------
    mask_base = np.zeros((100, 100), dtype=np.uint8)

    cv2.ellipse(
        mask_base,
        (50, 50),
        (35, 45),
        0, 0, 360,
        255,
        -1
    )

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # =====================================================
    # COLOR RANGES  (FIXED)
    # =====================================================

    colors = {

        # FIX 2: Tightened transparent range — narrower
        # saturation ceiling to avoid swallowing real colors
        "transparent": [
            ((0, 0, 200), (180, 30, 255))
        ],

        "red": [
            ((0,  80,  40), (10,  255, 255)),
            ((170, 80, 40), (180, 255, 255))
        ],

        "blue": [
            ((95, 60, 40), (140, 255, 255))
        ],

        "green": [
            ((35, 40, 40), (85, 255, 255))
        ],

        "yellow": [
            ((18, 70, 80), (35, 255, 255))
        ],

        "orange": [
            ((8, 70, 70), (24, 255, 255))
        ],

        "purple": [
            ((120, 40, 40), (160, 255, 255))
        ],

        # FIX 4: Brown range narrowed to reduce red/orange overlap
        "brown": [
            ((5, 80, 20), (18, 200, 140))
        ]
    }

    detected_color = "unknown"
    max_pixels     = 0

    # =====================================================
    # FIND DOMINANT COLOR
    # =====================================================

    for color_name, ranges in colors.items():

        total_pixels = 0

        for lower, upper in ranges:

            color_mask = cv2.inRange(
                hsv,
                np.array(lower),
                np.array(upper)
            )

            # FIX 5: Apply elliptical mask before counting
            color_mask = cv2.bitwise_and(
                color_mask,
                mask_base
            )

            total_pixels += cv2.countNonZero(color_mask)

        if total_pixels > max_pixels:

            max_pixels     = total_pixels
            detected_color = color_name

    # =====================================================
    # CONFIDENCE CHECK  (FIXED)
    # =====================================================

    # FIX 1: Use masked area as denominator (not full frame)
    total_area = cv2.countNonZero(mask_base)

    coverage = max_pixels / total_area

    # FIX 1: Return "unknown" when coverage is too low
    # (previously both branches returned detected_color)
    if coverage < 0.08:
        return "unknown"

    return detected_color

# =====================================================
# LIQUID ROI
# =====================================================

def get_liquid_roi(frame, x1, y1, x2, y2, object_name):

    h = y2 - y1
    w = x2 - x1

    # =====================================================
    # CYLINDERS / TUBES
    # =====================================================

    if object_name in [
        "Beaker",
        "Measuring_Cylinder",
        "Test_Tube",
        "Reagent_Bottle",
        "Wash_Bottle"
    ]:

        roi = frame[
            y1 + int(h * 0.35): y1 + int(h * 0.90),
            x1 + int(w * 0.20): x1 + int(w * 0.80)
        ]

        # ROI offsets for debug rectangle
        ry1_off, ry2_off = 0.35, 0.90
        rx1_off, rx2_off = 0.20, 0.80

    # =====================================================
    # FLASKS
    # =====================================================

    elif object_name in [
        "Conical_Flask",
        "Volumetric_Flask",
        "Round_Bottom_Flask_Borosilicate_Glass_1_Neck",
        "Round_Bottom_Flask_Borosilicate_Glass_2_Neck",
        "Round_Bottom_Flask_Borosilicate_Glass_3_Neck"
    ]:

        roi = frame[
            y1 + int(h * 0.45): y1 + int(h * 0.92),
            x1 + int(w * 0.25): x1 + int(w * 0.75)
        ]

        ry1_off, ry2_off = 0.45, 0.92
        rx1_off, rx2_off = 0.25, 0.75

    # =====================================================
    # FUNNELS
    # =====================================================

    elif object_name in [
        "Separating_Funnel",
        "Funnel",
        "Buchner_Funnel"
    ]:

        roi = frame[
            y1 + int(h * 0.25): y1 + int(h * 0.85),
            x1 + int(w * 0.20): x1 + int(w * 0.80)
        ]

        ry1_off, ry2_off = 0.25, 0.85
        rx1_off, rx2_off = 0.20, 0.80

    # =====================================================
    # DEFAULT
    # =====================================================

    else:

        roi = frame[y1:y2, x1:x2]

        ry1_off, ry2_off = 0.0, 1.0
        rx1_off, rx2_off = 0.0, 1.0

    # Return roi AND the exact offsets used so the debug
    # rectangle always matches the analysed region  (FIX 3)
    return roi, rx1_off, ry1_off, rx2_off, ry2_off

# =====================================================
# MAIN LOOP
# =====================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    start = time.time()

    annotated = frame.copy()

    # =====================================================
    # DETECTION + TRACKING
    # =====================================================

    results = model.track(
    source=frame,
    persist=True,
    tracker="bytetrack.yaml",

    conf=0.60,
    iou=0.35,

    imgsz=960,

    agnostic_nms=True,
    max_det=20,

    verbose=False
)

# =====================================================
# PROCESS RESULTS
# =====================================================

    for result in results:

     if result.boxes is None:
          continue

    boxes = result.boxes

    # ---------------------------------------------
    # KEEP ONLY BEST DETECTION FOR SAME OBJECT
    # ---------------------------------------------

    filtered_boxes = []

    if len(boxes) > 0:

        for box in boxes:

            conf = float(box.conf[0])

            if conf < 0.60:
                continue

            filtered_boxes.append(box)

    # ---------------------------------------------
    # DRAW
    # ---------------------------------------------

    for box in filtered_boxes:

        # =========================================
        # TRACK ID
        # =========================================

        if box.id is not None:
            track_id = int(box.id)
        else:
            track_id = id(box)

        # =========================================
        # BOX
        # =========================================

        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # =========================================
        # REJECT UNREALISTIC BOXES
        # =========================================

        w = x2 - x1
        h = y2 - y1

        if w < 15 or h < 15:
            continue

        if w > frame.shape[1] * 0.8:
            continue

        if h > frame.shape[0] * 0.8:
            continue

        # =========================================
        # SMOOTH BOX
        # =========================================

        x1, y1, x2, y2 = smooth_box(
            track_id,
            [x1, y1, x2, y2],
            alpha=0.85
        )

        # =========================================
        # CLASS
        # =========================================

        cls_id = int(box.cls[0])

        confidence = float(box.conf[0])

        object_name = model.names[cls_id]

        # =========================================
        # ROI
        # =========================================

        liquid_roi, rx1_off, ry1_off, rx2_off, ry2_off = get_liquid_roi(
            frame,
            x1, y1, x2, y2,
            object_name
        )

        if liquid_roi.size == 0:
            continue

        # =========================================
        # COLOR
        # =========================================

        liquid_color = detect_liquid_color(liquid_roi)

        # =========================================
        # TEMPORAL COLOR SMOOTHING
        # =========================================

        if track_id not in color_histories:
            color_histories[track_id] = deque(maxlen=10)

        color_histories[track_id].append(liquid_color)

        stable_color = Counter(
            color_histories[track_id]
        ).most_common(1)[0][0]

        # =========================================
        # LABEL
        # =========================================

        label = (
            f"{object_name} | "
            f"{stable_color} | "
            f"{confidence:.2f}"
        )

        # =========================================
        # COLOR
        # =========================================

        if stable_color == "unknown":
            draw_color = (0, 255, 255)
        else:
            draw_color = (0, 255, 0)

        # =========================================
        # MAIN BOX
        # =========================================

        cv2.rectangle(
            annotated,
            (x1, y1),
            (x2, y2),
            draw_color,
            2
        )

        cv2.putText(
            annotated,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            draw_color,
            2
        )

        # =========================================
        # ROI BOX
        # =========================================

        h = y2 - y1
        w = x2 - x1

        roi_x1 = x1 + int(w * rx1_off)
        roi_y1 = y1 + int(h * ry1_off)

        roi_x2 = x1 + int(w * rx2_off)
        roi_y2 = y1 + int(h * ry2_off)

        cv2.rectangle(
            annotated,
            (roi_x1, roi_y1),
            (roi_x2, roi_y2),
            (255, 0, 0),
            1
        )


    # =====================================================
    # FPS
    # =====================================================

    fps = 1 / (time.time() - start)

    cv2.putText(
        annotated,
        f"FPS: {fps:.1f}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2
    )

    # =====================================================
    # SHOW
    # =====================================================

    cv2.imshow("Stable Chemical Detection", annotated)

    # =====================================================
    # KEYBOARD
    # =====================================================

    key = cv2.waitKey(1)

    if key == 27:
        break

    elif key == ord('u'):

        CONF_THRESHOLD = min(CONF_THRESHOLD + 0.05, 1.0)

        print("Confidence:", round(CONF_THRESHOLD, 2))

    elif key == ord('d'):

        CONF_THRESHOLD = max(CONF_THRESHOLD - 0.05, 0.0)

        print("Confidence:", round(CONF_THRESHOLD, 2))

# =====================================================
# CLEANUP
# =====================================================

cap.release()
cv2.destroyAllWindows()