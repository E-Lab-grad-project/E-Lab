import cv2
import numpy as np
from threading import Thread, Event
from queue import Queue, Empty
from core.interface import frameProcessor
from .tracking import norm_to_angle, estimate_distance
from robot_control import RobotController
import time

class YoloFrameProcessor(frameProcessor):
    """YOLO + Tracker processor with ghost-box prevention and ESP terminal simulation."""

    def __init__(self, detector, robot_controller: RobotController, alpha=0.65, detect_every=3):
        self.detector = detector
        self.robot_controller = robot_controller
        self.alpha = alpha
        self.detect_every = detect_every

        # Tracker state
        self.tracker = None
        self.tracker_box = None
        self.tracker_ok = False
        self.object_detected = False

        # Smoothing
        self.prev_cx = None
        self.prev_cy = None

        # Frame counter
        self.frame_count = 0

        # YOLO & tracker revalidation
        self._queue = Queue(maxsize=1)
        self._frame_for_yolo = None
        self._new_frame_event = Event()
        self._running = True

        self.no_detection_count = 0
        self.max_no_detection = 3  # consecutive frames with no YOLO detection → reset

        # Command timing
        self.last_send_time = 0
        self.stopped = True

        # last known servo values (for terminal)
        self.last_servo_x = 90
        self.last_servo_y = 90
        self.last_z = 1

        # Start YOLO worker thread
        self._thread = Thread(target=self._worker, daemon=True)
        self._thread.start()

    # ----------------- YOLO WORKER -----------------
    def _worker(self):
        while self._running:
            self._new_frame_event.wait()
            self._new_frame_event.clear()

            frame = self._frame_for_yolo
            if frame is None:
                continue

            try:
                results = self.detector.detect(frame)

                if not self._queue.empty():
                    try:
                        self._queue.get_nowait()
                    except Empty:
                        pass

                self._queue.put(results)

            except Exception as e:
                print("[YOLO worker error]", e)

    # ----------------- PROCESS FRAME -----------------
    def process(self, frame: np.ndarray) -> np.ndarray:
        h, w = frame.shape[:2]
        screen_cx = w / 2
        screen_cy = h / 2
        self.frame_count += 1

        # Update tracker if exists
        if self.tracker is not None:
            self.tracker_ok, self.tracker_box = self.tracker.update(frame)

            if not self.tracker_ok:
                self._reset_tracker()

        # Determine if we need YOLO detection
        need_detection = (self.frame_count % self.detect_every == 0) or not self.tracker_ok

        if need_detection:
            self._frame_for_yolo = frame
            self._new_frame_event.set()

            try:
                results = self._queue.get_nowait()
                self._update_tracker_from_yolo(frame, results)
            except Empty:
                pass

        # If tracker invalid, return frame
        if not self.tracker_ok or self.tracker_box is None:
            return frame

        # ---------------- TRACKED BOX -----------------
        x, y, bw, bh = [int(v) for v in self.tracker_box]
        area = bw * bh
        if area < 1000 or area > (w * h * 0.8):
            self._reset_tracker()
            return frame

        x1, y1 = x, y
        x2, y2 = x + bw, y + bh

        cx = ((x1 + x2) / 2) - screen_cx
        cy = ((y1 + y2) / 2) - screen_cy

        # Smoothing
        if self.prev_cx is None:
            self.prev_cx, self.prev_cy = cx, cy
        else:
            cx = self.alpha * self.prev_cx + (1 - self.alpha) * cx
            cy = self.alpha * self.prev_cy + (1 - self.alpha) * cy
            self.prev_cx, self.prev_cy = cx, cy

        servo_x = norm_to_angle(cx / (w / 2))
        servo_y = norm_to_angle(-cy / (h / 2))
        z_dist = estimate_distance(area=area)

        # ---------------- DRAW -----------------
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(frame, ((x1 + x2)//2, (y1 + y2)//2), 5, (0, 0, 255), -1)
        cv2.putText(frame, f"X:{servo_x} Y:{servo_y} Z:{z_dist:.2f}",
                    (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)

        # ---------------- SEND COMMAND -----------------
        now = time.time()
        if now - self.last_send_time > 0.05 and self.tracker_ok:
            self.last_servo_x = servo_x
            self.last_servo_y = servo_y
            self.last_z = z_dist

            # Terminal simulation
            print("🤖 ROBOT COMMAND")
            print(f"Base (X)        : {servo_x}")
            print(f"Shoulder (Y)    : {servo_y}")
            print(f"Distance (Z)    : {z_dist:.2f}")
            print("Serial Message  :", f"X:{servo_x},Y:{servo_y},Z:{z_dist:.2f}")
            print("============================================================")

            # Send to ESP if connected
            try:
                self.robot_controller.send_state(servo_x, servo_y, z_dist)
            except Exception:
                print("[NO SERIAL] Skipping send")

            self.last_send_time = now

        return frame

    # ----------------- UPDATE TRACKER FROM YOLO -----------------
    def _update_tracker_from_yolo(self, frame, results):
        if results is None or len(results) == 0:
            self.no_detection_count += 1
            if self.no_detection_count >= self.max_no_detection:
                self._reset_tracker()
            return

        best_box = None
        best_area = 0

        try:
            for box in results[0].boxes:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])

                if self.detector.class_names[cls_id] != self.detector.target_class:
                    continue

                if conf < 0.4:  # only high-confidence
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                area = (x2 - x1) * (y2 - y1)

                if area > best_area:
                    best_area = area
                    best_box = (x1, y1, x2, y2)

        except Exception as e:
            print("[YOLO PROCESS ERROR]", e)
            return

        if best_box is None:
            self.no_detection_count += 1
            if self.no_detection_count >= self.max_no_detection:
                self._reset_tracker()
            return
        else:
            self.no_detection_count = 0

        # Initialize tracker
        x1, y1, x2, y2 = best_box
        bbox = (x1, y1, x2 - x1, y2 - y1)
        self.tracker = cv2.legacy.TrackerMOSSE_create()
        self.tracker.init(frame, bbox)
        self.tracker_box = bbox
        self.tracker_ok = True
        self.object_detected = True
        self.tracker_fail_count = 0
        self.stopped = False
        print("TRACKER INITIALIZED")

    # ----------------- RESET TRACKER -----------------
    def _reset_tracker(self):
        if not self.stopped:
            print("TRACK LOST → Holding last position")
        self.tracker = None
        self.tracker_box = None
        self.tracker_ok = False
        self.object_detected = False
        self.prev_cx = None
        self.prev_cy = None
        self.tracker_fail_count = 0
        self.no_detection_count = 0
        self.stopped = True

    # ----------------- STOP THREAD -----------------
    def stop(self):
        self._running = False
        self._new_frame_event.set()
        self._thread.join()
        self.robot_controller.close()