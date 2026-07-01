"""6-DOF robotics pipeline: detection geometry, IK interface, and motion planning."""

from robotics.camera_geometry import normalized_depth_to_meters, pixel_to_camera
from robotics.config import (
    CameraIntrinsics,
    DepthConfig,
    GraspOrientationConfig,
    MotionPlannerConfig,
    PipelineConfig,
    RoboticsConfig,
)
from robotics.coordinate_transform import CoordinateTransformer
from robotics.ik_solver import IKSolver, UnconfiguredIKSolver
from robotics.integration import (
    configure_logging,
    create_detection_bridge,
    create_robotics_pipeline,
    start_robotics_bridge,
)
from robotics.motion_planner import MotionPhase, MotionPlanner, MotionStep
from robotics.pipeline import DetectionRoboticsBridge, RoboticsPipeline, TargetSelector
from robotics.pose import JointAngles, Point3D, Pose
from robotics.pose_generator import DetectedObject, GraspPoseGenerator
from robotics.robot_controller import NullRobotController, RobotController

__all__ = [
    "CameraIntrinsics",
    "CoordinateTransformer",
    "DepthConfig",
    "DetectedObject",
    "DetectionRoboticsBridge",
    "GraspOrientationConfig",
    "GraspPoseGenerator",
    "IKSolver",
    "JointAngles",
    "MotionPhase",
    "MotionPlanner",
    "MotionPlannerConfig",
    "MotionStep",
    "NullRobotController",
    "PipelineConfig",
    "Point3D",
    "Pose",
    "RoboticsConfig",
    "RoboticsPipeline",
    "RobotController",
    "TargetSelector",
    "UnconfiguredIKSolver",
    "configure_logging",
    "create_detection_bridge",
    "create_robotics_pipeline",
    "normalized_depth_to_meters",
    "pixel_to_camera",
    "start_robotics_bridge",
]
