import os
import cv2
import time
import threading
import numpy as np
from collections import deque, Counter
from ultralytics import YOLO

from core.interface import frameProcessor
from robot_control import RobotController
from .tracking import estimate_distance
import torch

# =====================================================
# INFERENCE DEVICE — prefer GPU, fall back to CPU safely
# =====================================================

def _resolve_inference_device():
    if not torch.cuda.is_available() or torch.cuda.device_count() < 1:
        return "cpu"
    try:
        torch.zeros(1, device="cuda:0")
        return 0
    except RuntimeError:
        return "cpu"

INFERENCE_DEVICE = _resolve_inference_device()
print(f"YOLO inference device: {INFERENCE_DEVICE}")

# =====================================================
# LOAD MODEL
# =====================================================

model = YOLO("media/yolo/best-5.pt")

# =====================================================
# CAMERA STREAM
# Uses Picamera2 when available, otherwise falls back
# to a normal OpenCV webcam capture stream.
# =====================================================

class CameraStream:
    def __init__(self, width=720, height=720, camera_index=0):
        self.width = width
        self.height = height
        self.camera_index = camera_index
        self.frame = None
        self.stopped = False
        self.lock = threading.Lock()
        self.use_picamera2 = False
        self.picam2 = None
        self.cap = None

        backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(self.camera_index, backend)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open webcam at index {self.camera_index}")
        print(f"CameraStream: using webcam index {self.camera_index}")

        # print("CameraStream: Picamera2 unavailable, falling back to cv2.VideoCapture:", exc)
        
        backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
        self.cap = cv2.VideoCapture( "udp://@:5000", cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open webcam at index {self.camera_index}")
        print(f"CameraStream: using webcam index {self.camera_index}")

        # try:
        #     from picamera2 import Picamera2
        #     self.picam2 = Picamera2()
        #     config = self.picam2.create_preview_configuration(
        #         main={"format": "RGB888", "size": (width, height)},
        #         buffer_count=1
        #     )
        #     self.picam2.configure(config)
        #     self.picam2.start()
        #     self.use_picamera2 = True
        #     print("CameraStream: using Picamera2")
        # except Exception as exc:
        #     print("CameraStream: Picamera2 unavailable, falling back to cv2.VideoCapture:", exc)
        #     backend = cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY
        #     self.cap = cv2.VideoCapture(self.camera_index, backend)
        #     self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        #     self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        #     if not self.cap.isOpened():
        #         raise RuntimeError(f"Cannot open webcam at index {self.camera_index}")
        #     print(f"CameraStream: using webcam index {self.camera_index}")

        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()

    def update(self):
        while not self.stopped:
            if self.use_picamera2:
                frame = self.picam2.capture_array()
                if frame is None:
                    continue
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            else:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    continue
            with self.lock:
                self.frame = frame

    def read(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def stop(self):
        self.stopped = True
        self.thread.join()
        if self.use_picamera2 and self.picam2 is not None:
            self.picam2.stop()
        if self.cap is not None:
            self.cap.release()

# NOTE: CameraStream and script execution are only started in the main() entrypoint below.

CONF_THRESHOLD = 0.40
color_histories = {}
z_histories     = {}
box_history     = {}
color_cache     = {}
COLOR_EVERY_N   = 10
INFERENCE_IMG_SIZE = 640
SUBMIT_EVERY_N = 1   # submit every 2 display frames for faster real-time performance
last_results    = []

# =====================================================
# DETECTION SETTINGS
# =====================================================

def detect_liquid_color(roi):
    if roi.size == 0:
        return "unknown"
    roi = cv2.resize(roi, (50, 50))

    lut = np.array([
        np.clip(pow(i / 255.0, 1.1) * 255.0, 0, 255)
        for i in range(256)
    ], dtype=np.uint8).reshape(1, 256)
    roi = cv2.LUT(roi, lut)

    mask_base = np.zeros((50, 50), dtype=np.uint8)
    cv2.ellipse(mask_base, (25, 25), (18, 22), 0, 0, 360, 255, -1)

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    colors = {
        "transparent": [((0,   0,  200), (180,  30, 255))],
        "red":         [((0,   80,  40), ( 10, 255, 255)),
                        ((170, 80,  40), (180, 255, 255))],
        "blue":        [((95,  60,  40), (140, 255, 255))],
        "green":       [((35,  40,  40), ( 85, 255, 255))],
        "yellow":      [((18,  70,  80), ( 35, 255, 255))],
        "orange":      [((8,   70,  70), ( 24, 255, 255))],
        "purple":      [((120, 40,  40), (160, 255, 255))],
        "brown":       [((5,   80,  20), ( 18, 200, 140))],
    }

    detected_color = "unknown"
    max_pixels     = 0

    for color_name, ranges in colors.items():
        total = 0
        for lower, upper in ranges:
            cm = cv2.inRange(hsv, np.array(lower), np.array(upper))
            cm = cv2.bitwise_and(cm, mask_base)
            total += cv2.countNonZero(cm)
        if total > max_pixels:
            max_pixels     = total
            detected_color = color_name

    total_area = cv2.countNonZero(mask_base)
    if max_pixels / total_area < 0.08:
        return "unknown"

    return detected_color

# =====================================================
# LIQUID ROI EXTRACTION
# =====================================================

def get_liquid_roi(frame, x1, y1, x2, y2, object_name):
    h = y2 - y1
    w = x2 - x1

    if object_name in ["Beaker", "Measuring_Cylinder", "Test_Tube",
                        "Reagent_Bottle", "Wash_Bottle"]:
        roi = frame[y1 + int(h*0.35): y1 + int(h*0.90),
                    x1 + int(w*0.20): x1 + int(w*0.80)]
        return roi, 0.20, 0.35, 0.80, 0.90

    elif object_name in ["Conical_Flask", "Volumetric_Flask",
                          "Round_Bottom_Flask_Borosilicate_Glass_1_Neck",
                          "Round_Bottom_Flask_Borosilicate_Glass_2_Neck",
                          "Round_Bottom_Flask_Borosilicate_Glass_3_Neck"]:
        roi = frame[y1 + int(h*0.45): y1 + int(h*0.92),
                    x1 + int(w*0.25): x1 + int(w*0.75)]
        return roi, 0.25, 0.45, 0.75, 0.92

    elif object_name in ["Separating_Funnel", "Funnel", "Buchner_Funnel"]:
        roi = frame[y1 + int(h*0.25): y1 + int(h*0.85),
                    x1 + int(w*0.20): x1 + int(w*0.80)]
        return roi, 0.20, 0.25, 0.80, 0.85

    else:
        return frame[y1:y2, x1:x2], 0.0, 0.0, 1.0, 1.0

# =====================================================
# BOX SMOOTHING
# =====================================================

def smooth_box(object_id, box, alpha=0.3):
    if object_id not in box_history:
        box_history[object_id] = box
        return box
    old = box_history[object_id]
    smoothed = [int(alpha * old[i] + (1 - alpha) * box[i]) for i in range(4)]
    box_history[object_id] = smoothed
    return smoothed

# =====================================================
# DRAW INFO PANEL
# =====================================================

def draw_info_panel(frame, detections):
    panel_w  = 280
    margin   = 10
    line_h   = 22
    padding  = 10
    rows     = max(1, len(detections))
    panel_h  = padding * 2 + rows * (line_h * 4 + 8) + 10

    fx = frame.shape[1]
    overlay = frame.copy()
    cv2.rectangle(overlay,
                  (fx - panel_w - margin, margin),
                  (fx - margin, margin + panel_h),
                  (15, 15, 15), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
    cv2.rectangle(frame,
                  (fx - panel_w - margin, margin),
                  (fx - margin, margin + panel_h),
                  (0, 200, 100), 1)

    font  = cv2.FONT_HERSHEY_SIMPLEX
    y_off = margin + padding + line_h

    cv2.putText(frame, "DETECTED OBJECTS", (fx - panel_w - margin + 8, y_off),
                font, 0.45, (0, 220, 120), 1, cv2.LINE_AA)
    y_off += line_h

    if not detections:
        cv2.putText(frame, "  None", (fx - panel_w - margin + 8, y_off),
                    font, 0.4, (150, 150, 150), 1, cv2.LINE_AA)
        return

    for d in detections:
        cv2.putText(frame, f"  {d['name']} [{d['color']}]",
                    (fx - panel_w - margin + 8, y_off),
                    font, 0.42, (0, 255, 200), 1, cv2.LINE_AA)
        y_off += line_h
        cv2.putText(frame, f"  X: {d['x']}   Y: {d['y']}",
                    (fx - panel_w - margin + 8, y_off),
                    font, 0.40, (100, 200, 255), 1, cv2.LINE_AA)
        y_off += line_h
        cv2.putText(frame, f"  Z: {d['z']:.2f} (normalized)",
                    (fx - panel_w - margin + 8, y_off),
                    font, 0.40, (255, 180, 100), 1, cv2.LINE_AA)
        y_off += line_h
        cv2.putText(frame, f"  Conf: {d['confidence']:.2f}",
                    (fx - panel_w - margin + 8, y_off),
                    font, 0.38, (160, 160, 160), 1, cv2.LINE_AA)
        y_off += line_h + 8
        cv2.line(frame,
                 (fx - panel_w - margin + 8, y_off - 4),
                 (fx - margin - 8,           y_off - 4),
                 (50, 50, 50), 1)

# =====================================================
# YOLO WORKER — runs inference in a background thread
# so the main loop (camera display) never freezes.
# Preserves all original logic: smooth_box, color
# cache, color_histories, get_liquid_roi, etc.
# =====================================================

class YOLOWorker:
    def __init__(self, model, conf_threshold=0.40):
        self.model          = model
        self.conf_threshold = conf_threshold

        self._input_frame  = None
        self._results      = []
        self._result_lock  = threading.Lock()
        self._input_lock   = threading.Lock()
        self._running      = True
        self._new_frame    = threading.Event()

        # per-worker frame counter (mirrors original COLOR_EVERY_N logic)
        self._frame_count  = 0

        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def submit(self, frame):
        """Hand a new frame to the worker. Non-blocking — returns instantly."""
        with self._input_lock:
            self._input_frame = frame.copy()
        self._new_frame.set()

    def get_results(self):
        """Fetch the latest detection list. Non-blocking."""
        with self._result_lock:
            return list(self._results)

    def set_conf(self, value):
        self.conf_threshold = value

    def _run(self):
        while self._running:
            triggered = self._new_frame.wait(timeout=0.5)
            if not triggered:
                continue
            self._new_frame.clear()

            with self._input_lock:
                frame = self._input_frame
            if frame is None:
                continue

            self._frame_count += 1

            results = self.model.track(
                    source=frame,
                    persist=True,
                    tracker="bytetrack.yaml",

                    conf=self.conf_threshold,
                    iou=0.35,

                    imgsz=INFERENCE_IMG_SIZE,

                    agnostic_nms=True,
                    max_det=20,

                    verbose=False,
                    device=INFERENCE_DEVICE,
                )

            detections = []

            for result in results:
                if result.boxes is None:
                    continue

                for idx, box in enumerate(result.boxes):
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    x1, y1, x2, y2 = smooth_box(idx, [x1, y1, x2, y2])

                    cls_id      = int(box.cls[0])
                    confidence  = float(box.conf[0])
                    object_name = self.model.names[cls_id]

                    if (x2 - x1) < 10 or (y2 - y1) < 10:
                        continue

                    # ── colour detection with original cache logic ──
                    cached_frame = color_cache.get(idx, (None, -999))[1]
                    if self._frame_count - cached_frame >= COLOR_EVERY_N:
                        liquid_roi, rx1o, ry1o, rx2o, ry2o = get_liquid_roi(
                            frame, x1, y1, x2, y2, object_name)
                        if liquid_roi.size == 0:
                            continue
                        raw_color = detect_liquid_color(liquid_roi)
                        color_cache[idx] = (raw_color, self._frame_count)
                    else:
                        raw_color        = color_cache[idx][0]
                        rx1o, ry1o, rx2o, ry2o = 0.0, 0.0, 1.0, 1.0

                    if idx not in color_histories:
                        color_histories[idx] = deque(maxlen=10)
                    color_histories[idx].append(raw_color)
                    stable_color = Counter(color_histories[idx]).most_common(1)[0][0]

                    cx_px = (x1 + x2) // 2
                    cy_px = (y1 + y2) // 2
                    bbox_area = (x2 - x1) * (y2 - y1)

                    if idx not in z_histories:
                        z_histories[idx] = deque(maxlen=8)
                    z_histories[idx].append(estimate_distance(bbox_area))
                    z_norm = float(np.mean(z_histories[idx]))

                    detections.append({
                        "name":        object_name,
                        "color":       stable_color,
                        "confidence":  confidence,
                        "x":           int(cx_px),
                        "y":           int(cy_px),
                        "z":           round(z_norm, 3),
                        "box":         (x1, y1, x2, y2),
                        "roi_offsets": (rx1o, ry1o, rx2o, ry2o),
                    })

            with self._result_lock:
                self._results = detections

    def stop(self):
        self._running = False
        self._new_frame.set()   # unblock the wait() so thread exits cleanly
        self.thread.join()

# =====================================================
# LATEST DETECTIONS (for API consumers)
# =====================================================

_latest_detections = []
_detections_lock = threading.Lock()


def get_latest_detections():
    with _detections_lock:
        return [
            {
                "name": d["name"],
                "color": d["color"],
                "confidence": d["confidence"],
                "x": d["x"],
                "y": d["y"],
                "z": d["z"],
                "z_unit": "normalized",
            }
            for d in _latest_detections
        ]


def _set_latest_detections(detections):
    global _latest_detections
    with _detections_lock:
        _latest_detections = list(detections)


# =====================================================
# MIXED GRID PROCESSOR (YOLO + coordinates, no grid overlay)
# =====================================================

class MixedGridProcessor(frameProcessor):
    def __init__(self, robot_controller: RobotController = None,
                 conf_threshold=CONF_THRESHOLD,
                 submit_every_n=SUBMIT_EVERY_N):
        self.robot_controller = robot_controller
        self.yolo_worker = YOLOWorker(model, conf_threshold=conf_threshold)
        self.frame_counter = 0
        self.submit_every_n = submit_every_n

    def process(self, frame: np.ndarray) -> np.ndarray:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        self.frame_counter += 1
        if self.frame_counter % self.submit_every_n == 0:
            self.yolo_worker.submit(frame)

        annotated = frame.copy()
        detections = self.yolo_worker.get_results()
        _set_latest_detections(detections)

        for d in detections:
            x1, y1, x2, y2        = d["box"]
            rx1o, ry1o, rx2o, ry2o = d["roi_offsets"]
            h = y2 - y1
            w = x2 - x1

            draw_color = (0, 255, 0) if d['color'] != "unknown" else (0, 255, 255)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), draw_color, 2)

            label = f"{d['name']} | ({d['x']}, {d['y']}, {d['z']:.2f})"
            cv2.putText(annotated, label, (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, draw_color, 2)

            cv2.circle(annotated, (d["x"], d["y"]), 4, (0, 0, 255), -1)

            cv2.rectangle(annotated,
                          (x1 + int(w * rx1o), y1 + int(h * ry1o)),
                          (x1 + int(w * rx2o), y1 + int(h * ry2o)),
                          (255, 0, 0), 1)

        draw_info_panel(annotated, detections)
        return annotated

    def stop(self):
        self.yolo_worker.stop()
        if self.robot_controller is not None:
            try:
                self.robot_controller.close()
            except Exception:
                pass


def main():
    cam = CameraStream(width=640, height=640)
    yolo_worker = YOLOWorker(model, conf_threshold=CONF_THRESHOLD)
    frame_count = 0

    while True:
        frame = cam.read()
        if frame is None:
            continue
        frame = cv2.resize(frame, (640, 640))
        start = time.time()
        annotated = frame.copy()
        frame_count += 1

        if frame_count % SUBMIT_EVERY_N == 0:
            yolo_worker.submit(frame)

        detections = yolo_worker.get_results()
        _set_latest_detections(detections)

        for d in detections:
            x1, y1, x2, y2        = d["box"]
            rx1o, ry1o, rx2o, ry2o = d["roi_offsets"]
            h = y2 - y1
            w = x2 - x1

            draw_color = (0, 255, 0) if d['color'] != "unknown" else (0, 255, 255)
            cv2.rectangle(annotated, (x1, y1), (x2, y2), draw_color, 2)

            label = f"{d['name']} | ({d['x']}, {d['y']}, {d['z']:.2f})"
            cv2.putText(annotated, label, (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, draw_color, 2)

            cv2.circle(annotated, (d["x"], d["y"]), 4, (0, 0, 255), -1)

            cv2.rectangle(annotated,
                          (x1 + int(w * rx1o), y1 + int(h * ry1o)),
                          (x1 + int(w * rx2o), y1 + int(h * ry2o)),
                          (255, 0, 0), 1)

        draw_info_panel(annotated, detections)

        fps = 1 / (time.time() - start)
        cv2.putText(annotated, f"FPS: {fps:.1f}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
        cv2.putText(annotated, f"Conf: {CONF_THRESHOLD:.2f}  [U/D to adjust]",
                    (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

        cv2.imshow("Chemical Detection + Grid", annotated)

        key = cv2.waitKey(1)
        if key == 27:
            break
        elif key == ord('u'):
            CONF_THRESHOLD = min(CONF_THRESHOLD + 0.05, 1.0)
            yolo_worker.set_conf(CONF_THRESHOLD)
            print("Confidence:", round(CONF_THRESHOLD, 2))
        elif key == ord('d'):
            CONF_THRESHOLD = max(CONF_THRESHOLD - 0.05, 0.0)
            yolo_worker.set_conf(CONF_THRESHOLD)
            print("Confidence:", round(CONF_THRESHOLD, 2))

    yolo_worker.stop()
    cam.stop()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

