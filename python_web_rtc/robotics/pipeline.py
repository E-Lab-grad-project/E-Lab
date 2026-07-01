"""Orchestrates detection -> geometry -> IK -> motion without blocking YOLO."""

from __future__ import annotations

import logging
import queue
import threading
import time
from typing import Callable, Optional, Protocol

from robotics.camera_geometry import normalized_depth_to_meters, pixel_to_camera
from robotics.config import RoboticsConfig
from robotics.coordinate_transform import CoordinateTransformer
from robotics.motion_planner import MotionPlanner
from robotics.pose_generator import DetectedObject, GraspPoseGenerator
from robotics.robot_controller import RobotController

logger = logging.getLogger(__name__)


class DetectionSource(Protocol):
    def __call__(self) -> list[dict]:
        """Return the latest detection dictionaries."""


class TargetSelector:
    """Selects the best detection for manipulation."""

    def __init__(self, min_confidence: float) -> None:
        self._min_confidence = min_confidence

    def choose_target(self, detections: list[DetectedObject]) -> Optional[DetectedObject]:
        eligible = [d for d in detections if d.confidence >= self._min_confidence]
        if not eligible:
            return None
        return max(eligible, key=lambda item: item.confidence)


class RoboticsPipeline:
    """
    Converts a single detection into robot motion commands.

    Geometry chain:
        pixel (u,v) + depth -> camera (X,Y,Z) -> robot (X,Y,Z) -> grasp pose -> IK -> joints
    """

    def __init__(
        self,
        config: RoboticsConfig,
        robot: RobotController,
        motion_planner: MotionPlanner,
        pose_generator: GraspPoseGenerator,
        coordinate_transformer: CoordinateTransformer,
    ) -> None:
        self._config = config
        self._robot = robot
        self._motion_planner = motion_planner
        self._pose_generator = pose_generator
        self._coordinate_transformer = coordinate_transformer
        self._target_selector = TargetSelector(config.pipeline.min_confidence)

    @property
    def robot(self) -> RobotController:
        return self._robot

    def process_detections(self, raw_detections: list[dict]) -> bool:
        """
        Process the latest detections and enqueue a pick if a valid target exists.

        Returns True when a pick was scheduled.
        """
        detections = [DetectedObject.from_dict(item) for item in raw_detections]
        target = self._target_selector.choose_target(detections)
        if target is None:
            return False

        depth_m = normalized_depth_to_meters(target.z, self._config.depth)
        camera_point = pixel_to_camera(
            u=float(target.x),
            v=float(target.y),
            depth_m=depth_m,
            intrinsics=self._config.intrinsics,
        )
        robot_point = self._coordinate_transformer.camera_to_robot(camera_point)
        grasp_pose = self._pose_generator.generate_grasp_pose(robot_point)

        logger.info(
            "Target '%s' conf=%.2f pixel=(%d,%d) depth_norm=%.3f",
            target.name,
            target.confidence,
            target.x,
            target.y,
            target.z,
        )
        self._motion_planner.execute_pick(grasp_pose)
        return True


class DetectionRoboticsBridge:
    """
    Background bridge between the YOLO detection API and the robotics stack.

    Two threads:
      - polling thread: reads detections, schedules work when idle
      - motion thread: executes pick sequences without blocking detection
    """

    def __init__(
        self,
        pipeline: RoboticsPipeline,
        detection_source: DetectionSource,
        config: RoboticsConfig,
    ) -> None:
        self._pipeline = pipeline
        self._detection_source = detection_source
        self._config = config
        self._motion_queue: queue.Queue[Optional[dict]] = queue.Queue(maxsize=1)
        self._stop_event = threading.Event()
        self._busy = threading.Event()
        self._poll_thread: Optional[threading.Thread] = None
        self._motion_thread: Optional[threading.Thread] = None
        self._last_pick_time = 0.0

    def start(self) -> None:
        if self._poll_thread and self._poll_thread.is_alive():
            return
        self._stop_event.clear()
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            name="robotics-detection-poll",
            daemon=True,
        )
        self._motion_thread = threading.Thread(
            target=self._motion_loop,
            name="robotics-motion-worker",
            daemon=True,
        )
        self._poll_thread.start()
        self._motion_thread.start()
        logger.info("DetectionRoboticsBridge started")

    def stop(self) -> None:
        self._stop_event.set()
        try:
            self._motion_queue.put_nowait(None)
        except queue.Full:
            pass
        if self._poll_thread:
            self._poll_thread.join(timeout=2.0)
        if self._motion_thread:
            self._motion_thread.join(timeout=5.0)
        self._pipeline.robot.stop()
        logger.info("DetectionRoboticsBridge stopped")

    def _poll_loop(self) -> None:
        while not self._stop_event.is_set():
            if self._busy.is_set():
                time.sleep(self._config.pipeline.polling_interval_s)
                continue

            cooldown = self._config.pipeline.cooldown_after_pick_s
            if time.time() - self._last_pick_time < cooldown:
                time.sleep(self._config.pipeline.polling_interval_s)
                continue

            detections = self._detection_source()
            if detections:
                try:
                    self._motion_queue.put_nowait({"detections": detections})
                    self._busy.set()
                except queue.Full:
                    pass

            time.sleep(self._config.pipeline.polling_interval_s)

    def _motion_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                job = self._motion_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if job is None:
                break

            try:
                self._pipeline.process_detections(job["detections"])
                self._last_pick_time = time.time()
            except NotImplementedError as exc:
                logger.error("IK not configured: %s", exc)
            except Exception:
                logger.exception("Robotics motion failed")
            finally:
                self._busy.clear()
                self._motion_queue.task_done()
