import cv2
import numpy as np
from threading import Thread
from queue import Queue, Empty
from core.interface import frameProcessor
from .tracking import norm_to_angle, estimate_distance
from robot_control import RobotController

class YoloFrameProcessor(frameProcessor):
    """
    WebRTC-safe YOLO frame processor with Arduino/ESP32 control.
    Runs YOLO inference in a background thread and draws bounding boxes,
    red dot, X/Y/Z tracking info, and sends commands to robot controller.
    """

    def __init__(self, detector, robot_controller: RobotController, alpha=0.65, frame_skip=2):
        self.detector = detector
        self.robot_controller = robot_controller
        self.alpha = alpha
        self.frame_skip = frame_skip

        # smoothing state
        self.prev_cx = None
        self.prev_cy = None

        # frame counter
        self.frame_count = 0

        # last YOLO results
        self.last_results = []

        # thread-safe queue for YOLO inference
        self._queue = Queue(maxsize=1)
        self._running = True
        self._frame_for_yolo = None

        # start background YOLO worker thread
        self._thread = Thread(target=self._worker, daemon=True)
        self._thread.start()

    # ------------------------- WORKER THREAD -------------------------
    def _worker(self):
        """Background thread that runs YOLO inference."""
        while self._running:
            if self._frame_for_yolo is None:
                continue  # wait until a frame is available
            frame = self._frame_for_yolo.copy()
            try:
                results = self.detector.detect(frame)
                # keep only the latest result in queue
                if not self._queue.empty():
                    try:
                        self._queue.get_nowait()
                    except Empty:
                        pass
                self._queue.put(results)
            except Exception as e:
                print("[YOLO WORKER ERROR]:", e)
            finally:
                self._frame_for_yolo = None

    # ------------------------- PROCESS FRAME -------------------------
    def process(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        screen_cx = w / 2
        screen_cy = h / 2

        self.frame_count += 1

        # Send frame to YOLO worker
        if self.frame_count % self.frame_skip == 0:
            self._frame_for_yolo = frame.copy()
            try:
                self.last_results = self._queue.get_nowait()
            except Empty:
                pass

        best_box = None
        best_area = 0

        if self.last_results:
            try:
                for box in self.last_results[0].boxes:
                    cls_id = int(box.cls[0])
                    if self.detector.class_names[cls_id] != self.detector.target_class:
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    area = (x2 - x1) * (y2 - y1)
                    if area > best_area:
                        best_area = area
                        best_box = (x1, y1, x2, y2)
            except Exception as e:
                print("[YOLO PROCESSING ERROR]:", e)
                best_box = None

        if not best_box:
            return frame

        x1, y1, x2, y2 = best_box
        cx = ((x1 + x2) / 2) - screen_cx
        cy = ((y1 + y2) / 2) - screen_cy

        if self.prev_cx is None:
            self.prev_cx, self.prev_cy = cx, cy
        else:
            cx = self.alpha * self.prev_cx + (1 - self.alpha) * cx
            cy = self.alpha * self.prev_cy + (1 - self.alpha) * cy
            self.prev_cx, self.prev_cy = cx, cy

        # Compute servo angles / normalized coordinates
        servo_x = norm_to_angle(cx / (w / 2))
        servo_y = norm_to_angle(-cy / (h / 2))
        z_dist = estimate_distance(best_area)

        # ================= DRAWING =================
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        # Red dot at object center
        cx_pix = int((x1 + x2) / 2)
        cy_pix = int((y1 + y2) / 2)
        cv2.circle(frame, (cx_pix, cy_pix), 5, (0, 0, 255), -1)
        # Draw X/Y/Z near box
        cv2.putText(
            frame,
            f"X:{servo_x} Y:{servo_y} Z:{z_dist:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2,
        )

        # ================= SEND TO ROBOT =================
        self.robot_controller.send_state(servo_x, servo_y, z_dist)

        return frame

    # ------------------------- STOP THREAD -------------------------
    def stop(self):
        """Call this to cleanly stop the background thread."""
        self._running = False
        self._thread.join()
        self.robot_controller.close()