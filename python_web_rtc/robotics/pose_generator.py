"""Grasp pose generation from detected objects."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from robotics.config import GraspOrientationConfig
from robotics.pose import Point3D, Pose, degrees_to_radians

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DetectedObject:
    """Detection payload consumed by the robotics pipeline (matches the API)."""

    name: str
    color: str
    confidence: float
    x: int
    y: int
    z: float

    @classmethod
    def from_dict(cls, data: dict) -> DetectedObject:
        return cls(
            name=str(data["name"]),
            color=str(data.get("color", "unknown")),
            confidence=float(data["confidence"]),
            x=int(data["x"]),
            y=int(data["y"]),
            z=float(data["z"]),
        )


class GraspPoseGenerator:
    """Build a 6-DOF grasp pose from a robot-frame target position."""

    def __init__(self, orientation: GraspOrientationConfig) -> None:
        self._orientation = orientation

    def generate_grasp_pose(self, robot_point: Point3D) -> Pose:
        """
        Create a grasp pose at the robot-frame target position.

        Orientation defaults are configurable (roll/pitch/yaw in degrees).
        """
        pose = Pose(
            x=robot_point.x,
            y=robot_point.y,
            z=robot_point.z,
            roll=degrees_to_radians(self._orientation.roll_deg),
            pitch=degrees_to_radians(self._orientation.pitch_deg),
            yaw=degrees_to_radians(self._orientation.yaw_deg),
        )
        logger.info(
            "Generated grasp pose at (%.3f, %.3f, %.3f) rad orient (r=%.2f, p=%.2f, y=%.2f)",
            pose.x,
            pose.y,
            pose.z,
            pose.roll,
            pose.pitch,
            pose.yaw,
        )
        return pose
