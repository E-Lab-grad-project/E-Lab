import cv2
import numpy as np
from threading import Thread
from queue import Queue, Empty
import time

from ultralytics import YOLO

from core.interface import frameProcessor
from .tracking import norm_to_angle, estimate_distance
from robot_control import RobotController


class YoloFrameProcessor(frameProcessor):

    def __init__(self, robot_controller: RobotController):

        # ================= YOLO =================
        self.model = YOLO("yolov8n.pt")
        self.target_class = "cup"
        self.class_names = self.model.names

        self.robot_controller = robot_controller

        # ================= PIPELINE =================
        self.frame_queue = Queue(maxsize=1)
        self.yolo_queue = Queue(maxsize=1)
        self.running = True

        # ================= SMOOTHING =================
        self.prev_cx = None
        self.prev_cy = None
        self.alpha = 0.65

        self.last_send_time = 0

        # ================= FRAME SKIP =================
        self.frame_counter = 0
        self.skip_rate = 1

        # ================= THREADS =================
        self.camera_thread = Thread(target=self._frame_worker, daemon=True)
        self.yolo_thread = Thread(target=self._yolo_worker, daemon=True)

        self.camera_thread.start()
        self.yolo_thread.start()

    # ================= INPUT =================
    def process(self, frame: np.ndarray) -> np.ndarray:
        self._latest_frame = frame

        try:
            results = self.yolo_queue.get_nowait()
        except Empty:
            return frame

        return self._process_detections(frame, results)

    # ================= FRAME BUFFER =================
    def _frame_worker(self):
        while self.running:
            if hasattr(self, "_latest_frame"):
                if self.frame_queue.full():
                    self.frame_queue.get_nowait()
                self.frame_queue.put(self._latest_frame)

            time.sleep(0.001)

    # ================= YOLO WORKER =================
    def _yolo_worker(self):
        latest_frame = None

        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1)
                latest_frame = frame
            except Empty:
                continue

            # ================= FRAME SKIPPING =================
            self.frame_counter += 1
            if self.frame_counter % self.skip_rate != 0:
                continue

            if latest_frame is None:
                continue

            # ================= YOLO INFERENCE =================
            results = self.model(
                latest_frame,
                imgsz=640,
                conf=0.4,
                verbose=False
            )

            if self.yolo_queue.full():
                self.yolo_queue.get_nowait()

            self.yolo_queue.put(results)

    # ================= MAIN LOGIC =================
    def _process_detections(self, frame, results):

        # ================= FIX ONLY HERE (COLOR CORRECTION) =================
        display = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        h, w = display.shape[:2]
        screen_cx = w / 2
        screen_cy = h / 2

        best_box = None
        best_area = 0

        # ================= FIND BEST OBJECT =================
        for box in results[0].boxes:

            cls_id = int(box.cls[0])

            if self.class_names[cls_id] != self.target_class:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])

            area = (x2 - x1) * (y2 - y1)

            if area > best_area:
                best_area = area
                best_box = (x1, y1, x2, y2)

        if best_box is None:
            return display

        x1, y1, x2, y2 = best_box

        # ================= CENTER =================
        cx = ((x1 + x2) / 2) - screen_cx
        cy = ((y1 + y2) / 2) - screen_cy

        # ================= SMOOTHING =================
        if self.prev_cx is None:
            self.prev_cx, self.prev_cy = cx, cy
        else:
            cx = self.alpha * self.prev_cx + (1 - self.alpha) * cx
            cy = self.alpha * self.prev_cy + (1 - self.alpha) * cy
            self.prev_cx, self.prev_cy = cx, cy

        # ================= CONTROL =================
        servo_x = norm_to_angle(cx / (w / 2))
        servo_y = norm_to_angle(-cy / (h / 2))
        z_dist = estimate_distance(best_area)

        # ================= SEND (RATE LIMIT) =================
        now = time.time()
        if now - self.last_send_time > 0.05:
            self.robot_controller.send_state(servo_x, servo_y, z_dist)
            self.last_send_time = now

        # ================= DRAW =================
        cv2.rectangle(display, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.circle(display,
                   (int((x1 + x2) / 2), int((y1 + y2) / 2)),
                   5, (0, 0, 255), -1)

        cv2.putText(display, f"X:{servo_x} Y:{servo_y}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

        cv2.putText(display, f"Z:{z_dist:.2f}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

        return display

    # ================= STOP =================
    def stop(self):
        self.running = False
        self.camera_thread.join()
        self.yolo_thread.join()
        self.robot_controller.close()