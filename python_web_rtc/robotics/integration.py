"""Factory wiring for the robotics stack."""

from __future__ import annotations

import logging
from typing import Callable, Optional

from robotics.config import RoboticsConfig
from robotics.coordinate_transform import CoordinateTransformer
from robotics.ik_solver import IKSolver, UnconfiguredIKSolver
from robotics.motion_planner import MotionPlanner
from robotics.pipeline import DetectionRoboticsBridge, RoboticsPipeline
from robotics.pose_generator import GraspPoseGenerator
from robotics.robot_controller import NullRobotController, RobotController

logger = logging.getLogger(__name__)


def _default_detection_source() -> list[dict]:
    from media.yolo.mixed_grid_pi import get_latest_detections

    return get_latest_detections()


def create_robotics_pipeline(
    config: Optional[RoboticsConfig] = None,
    ik_solver: Optional[IKSolver] = None,
    robot_controller: Optional[RobotController] = None,
) -> RoboticsPipeline:
    config = config or RoboticsConfig.from_env()
    ik_solver = ik_solver or UnconfiguredIKSolver()
    robot = robot_controller or NullRobotController()
    robot.bind_ik_solver(ik_solver)

    coordinate_transformer = CoordinateTransformer(config.camera_to_robot_transform)
    pose_generator = GraspPoseGenerator(config.grasp_orientation)
    motion_planner = MotionPlanner(
        robot=robot,
        ik_solver=ik_solver,
        config=config.motion,
    )

    return RoboticsPipeline(
        config=config,
        robot=robot,
        motion_planner=motion_planner,
        pose_generator=pose_generator,
        coordinate_transformer=coordinate_transformer,
    )


def create_detection_bridge(
    config: Optional[RoboticsConfig] = None,
    ik_solver: Optional[IKSolver] = None,
    robot_controller: Optional[RobotController] = None,
    detection_source: Optional[Callable[[], list[dict]]] = None,
) -> DetectionRoboticsBridge:
    config = config or RoboticsConfig.from_env()
    pipeline = create_robotics_pipeline(
        config=config,
        ik_solver=ik_solver,
        robot_controller=robot_controller,
    )
    source = detection_source or _default_detection_source
    return DetectionRoboticsBridge(
        pipeline=pipeline,
        detection_source=source,
        config=config,
    )


def start_robotics_bridge(
    config: Optional[RoboticsConfig] = None,
    ik_solver: Optional[IKSolver] = None,
    robot_controller: Optional[RobotController] = None,
    detection_source: Optional[Callable[[], list[dict]]] = None,
) -> DetectionRoboticsBridge:
    bridge = create_detection_bridge(
        config=config,
        ik_solver=ik_solver,
        robot_controller=robot_controller,
        detection_source=detection_source,
    )
    bridge.start()
    return bridge


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
