import math
import time

import cv2
import numpy as np
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
from mediapipe.tasks.python.vision.core import image as mp_image

from core.interface import frameProcessor
from hand_robot_control import HandRobotController
from media.hand_mirror.model_utils import ensure_hand_landmarker_model
from media.hand_mirror.state import SERVO_LABELS, hand_mirror_state

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (0, 9), (9, 10), (10, 11), (11, 12),
    (0, 13), (13, 14), (14, 15), (15, 16),
    (0, 17), (17, 18), (18, 19), (19, 20),
    (5, 9), (9, 13), (13, 17),
]


def map_value(value, in_min, in_max, out_min, out_max):
    value = max(in_min, min(in_max, value))
    return int((value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


def get_angle_between_points(p1, p2, p3):
    v1 = (p1[0] - p2[0], p1[1] - p2[1])
    v2 = (p3[0] - p2[0], p3[1] - p2[1])
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    mag1 = math.sqrt(v1[0] ** 2 + v1[1] ** 2)
    mag2 = math.sqrt(v2[0] ** 2 + v2[1] ** 2)
    if mag1 * mag2 == 0:
        return 90
    cos_angle = dot / (mag1 * mag2)
    cos_angle = max(-1, min(1, cos_angle))
    return int(math.degrees(math.acos(cos_angle)))


def smooth_angle(current, target, factor=0.25):
    return int(current + (target - current) * factor)


def get_all_servo_angles(lm):
    def pt(idx):
        return (lm[idx].x, lm[idx].y)

    wrist_x = lm[0].x
    base_angle = map_value(wrist_x, 0.1, 0.9, 0, 180)

    wrist_y = lm[0].y
    shoulder_angle = map_value(wrist_y, 0.1, 0.9, 150, 30)

    elbow_angle = get_angle_between_points(pt(0), pt(5), pt(8))
    elbow_servo = map_value(elbow_angle, 90, 180, 0, 180)

    wrist_pitch_angle = get_angle_between_points(pt(0), pt(9), pt(12))
    wrist_pitch_servo = map_value(wrist_pitch_angle, 90, 180, 0, 180)

    index_mcp_y = lm[5].y
    pinky_mcp_y = lm[17].y
    tilt = index_mcp_y - pinky_mcp_y
    wrist_roll_servo = map_value(tilt, -0.15, 0.15, 0, 180)

    open_fingers = sum(
        1 for tip, base in [(8, 6), (12, 10), (16, 14), (20, 18)]
        if lm[tip].y < lm[base].y
    )
    gripper_angle = 180 if open_fingers > 2 else 0

    return base_angle, shoulder_angle, elbow_servo, wrist_pitch_servo, wrist_roll_servo, gripper_angle


def draw_hand_landmarks(frame, lm, width: int, height: int) -> None:
    points = []
    for landmark in lm:
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        points.append((x, y))
        cv2.circle(frame, (x, y), 4, (0, 255, 0), -1)

    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, points[start], points[end], (0, 200, 255), 2)


class HandMirrorProcessor(frameProcessor):
    def __init__(self, hand_controller: HandRobotController):
        self.hand_controller = hand_controller
        self.prev_angles = [90, 90, 90, 90, 90, 90]
        self._frame_ts = 0

        model_path = ensure_hand_landmarker_model()
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=model_path),
            running_mode=RunningMode.VIDEO,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.7,
            min_tracking_confidence=0.7,
        )
        self.landmarker = HandLandmarker.create_from_options(options)

    def process(self, frame):
        display = cv2.flip(frame, 1)
        h, w = display.shape[:2]
        rgb = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        rgb = np.ascontiguousarray(rgb)

        mp_frame = mp_image.Image(image_format=mp_image.ImageFormat.SRGB, data=rgb)
        self._frame_ts += 33
        result = self.landmarker.detect_for_video(mp_frame, self._frame_ts)

        hand_mirror_state.serial_connected = self.hand_controller.connected
        hand_mirror_state.hand_detected = False

        if result.hand_landmarks:
            for hand_lm in result.hand_landmarks:
                hand_mirror_state.hand_detected = True
                draw_hand_landmarks(display, hand_lm, w, h)

                target_angles = list(get_all_servo_angles(hand_lm))
                smoothed = [
                    smooth_angle(self.prev_angles[i], target_angles[i], factor=0.25)
                    for i in range(6)
                ]
                self.prev_angles = smoothed
                hand_mirror_state.last_angles = smoothed

                base, shoulder, elbow, wrist_pitch, wrist_roll, gripper = smoothed

                if hand_mirror_state.mirroring_enabled:
                    self.hand_controller.send_angles(
                        base, shoulder, elbow, wrist_pitch, wrist_roll, gripper
                    )
                    hand_mirror_state.serial_connected = self.hand_controller.connected

                for i, (label, angle) in enumerate(zip(SERVO_LABELS, smoothed)):
                    color = (0, 255, 0) if i < 5 else (0, 165, 255)
                    cv2.putText(
                        display,
                        f"{label}: {angle}",
                        (10, 30 + i * 32),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        2,
                        cv2.LINE_AA,
                    )

        mirror_label = "MIRRORING" if hand_mirror_state.mirroring_enabled else "PREVIEW"
        label_color = (0, 255, 0) if hand_mirror_state.mirroring_enabled else (200, 200, 200)
        cv2.putText(
            display,
            mirror_label,
            (display.shape[1] - 180, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            label_color,
            2,
            cv2.LINE_AA,
        )

        if not hand_mirror_state.hand_detected:
            cv2.putText(
                display,
                "Show your hand to the camera",
                (10, display.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (180, 180, 180),
                2,
                cv2.LINE_AA,
            )

        return display
