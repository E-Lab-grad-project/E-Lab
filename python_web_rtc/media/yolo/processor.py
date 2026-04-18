import cv2
import numpy as np
from threading import Thread, Lock
from queue import Queue, Empty
import time

from core.interface import frameProcessor
from .tracking import norm_to_angle, estimate_distance
from robot_control import RobotController


class YoloFrameProcessor(frameProcessor):

    def __init__(self, detector, robot_controller: RobotController):
        self.detector = detector
        self.robot_controller = robot_controller

        # -------- FRAME PIPELINE --------
        self.frame_queue = Queue(maxsize=1)      # always latest frame
        self.yolo_queue = Queue(maxsize=1)       # detection results

        self.running = True
        self.lock = Lock()

        # -------- TRACKER --------
        self.tracker = None
        self.tracker_box = None
        self.tracker_ok = False

        # -------- SMOOTHING --------
        self.prev_cx = None
        self.prev_cy = None
        self.alpha = 0.7

        # -------- CONTROL --------
        self.last_send_time = 0

        # -------- START THREADS --------
        self.camera_thread = Thread(target=self._frame_buffer_worker, daemon=True)
        self.yolo_thread = Thread(target=self._yolo_worker, daemon=True)

        self.camera_thread.start()
        self.yolo_thread.start()

    # ================= CAMERA BUFFER =================
    def _frame_buffer_worker(self):
        """Keeps only latest frame (no lag)"""
        while self.running:
            if hasattr(self, "_latest_frame"):
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except:
                        pass
                self.frame_queue.put(self._latest_frame)

            time.sleep(0.001)

    # ================= YOLO WORKER =================
    def _yolo_worker(self):
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1)
            except Empty:
                continue

            try:
                small = cv2.resize(frame, (320, 240))
                results = self.detector.detect(small)

                if self.yolo_queue.full():
                    self.yolo_queue.get_nowait()

                self.yolo_queue.put((results, frame.shape))

            except Exception as e:
                print("[YOLO ERROR]", e)

    # ================= MAIN PROCESS =================
    def process(self, frame: np.ndarray) -> np.ndarray:

        # update latest frame (producer input)
        self._latest_frame = frame

        h, w = frame.shape[:2]
        screen_cx, screen_cy = w / 2, h / 2

        # -------- UPDATE TRACKER --------
        if self.tracker is not None:
            self.tracker_ok, self.tracker_box = self.tracker.update(frame)

            if not self.tracker_ok:
                self._reset_tracker()

        # -------- GET YOLO RESULT --------
        try:
            results, original_shape = self.yolo_queue.get_nowait()
            self._update_tracker(frame, results, original_shape)
        except Empty:
            pass

        # -------- NO TRACK --------
        if not self.tracker_ok:
            return frame

        # -------- BOX --------
        x, y, bw, bh = map(int, self.tracker_box)
        area = bw * bh

        if area < 800 or area > (w * h * 0.7):
            self._reset_tracker()
            return frame

        x1, y1 = x, y
        x2, y2 = x + bw, y + bh

        cx = ((x1 + x2) / 2) - screen_cx
        cy = ((y1 + y2) / 2) - screen_cy

        # -------- SMOOTH --------
        if self.prev_cx is None:
            self.prev_cx, self.prev_cy = cx, cy
        else:
            cx = self.alpha * self.prev_cx + (1 - self.alpha) * cx
            cy = self.alpha * self.prev_cy + (1 - self.alpha) * cy
            self.prev_cx, self.prev_cy = cx, cy

        # -------- CONTROL --------
        servo_x = norm_to_angle(cx / (w / 2))
        servo_y = norm_to_angle(-cy / (h / 2))
        z_dist = estimate_distance(area)

        # -------- DRAW --------
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # -------- SEND --------
        now = time.time()
        if now - self.last_send_time > 0.05:
            try:
                self.robot_controller.send_state(servo_x, servo_y, z_dist)
            except:
                pass
            self.last_send_time = now

        return frame

    # ================= TRACKER UPDATE =================
    def _update_tracker(self, frame, results, shape):

        if results is None or len(results) == 0:
            return

        h, w = shape[:2]
        sx, sy = w / 320, h / 240

        best = None
        best_area = 0

        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])

            if self.detector.class_names[cls_id] != self.detector.target_class:
                continue
            if conf < 0.4:
                continue

            x1, y1, x2, y2 = box.xyxy[0]

            x1, y1 = int(x1 * sx), int(y1 * sy)
            x2, y2 = int(x2 * sx), int(y2 * sy)

            area = (x2 - x1) * (y2 - y1)

            if area > best_area:
                best_area = area
                best = (x1, y1, x2, y2)

        if best is None:
            return

        x1, y1, x2, y2 = best
        bbox = (x1, y1, x2 - x1, y2 - y1)

        self.tracker = cv2.legacy.TrackerCSRT_create()
        self.tracker.init(frame, bbox)

        self.tracker_box = bbox
        self.tracker_ok = True

    # ================= RESET =================
    def _reset_tracker(self):
        self.tracker = None
        self.tracker_box = None
        self.tracker_ok = False
        self.prev_cx = None
        self.prev_cy = None

    # ================= STOP =================
    def stop(self):
        self.running = False
        self.camera_thread.join()
        self.yolo_thread.join()
        self.robot_controller.close()