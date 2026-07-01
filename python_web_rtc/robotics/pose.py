"""Pose and spatial primitive types."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Point3D:
    """A 3D point in metres."""

    x: float
    y: float
    z: float


@dataclass(frozen=True)
class Pose:
    """6-DOF end-effector pose in the robot-base frame."""

    x: float
    y: float
    z: float
    roll: float
    pitch: float
    yaw: float

    def with_position(self, x: float, y: float, z: float) -> Pose:
        return Pose(x=x, y=y, z=z, roll=self.roll, pitch=self.pitch, yaw=self.yaw)

    def with_offset(self, x: float = 0.0, y: float = 0.0, z: float = 0.0) -> Pose:
        return Pose(
            x=self.x + x,
            y=self.y + y,
            z=self.z + z,
            roll=self.roll,
            pitch=self.pitch,
            yaw=self.yaw,
        )

    def position(self) -> Point3D:
        return Point3D(self.x, self.y, self.z)


@dataclass(frozen=True)
class JointAngles:
    """Six revolute joint angles in degrees."""

    j1: float
    j2: float
    j3: float
    j4: float
    j5: float
    j6: float

    def as_tuple(self) -> tuple[float, float, float, float, float, float]:
        return (self.j1, self.j2, self.j3, self.j4, self.j5, self.j6)

    def with_gripper(self, gripper_angle_deg: float) -> JointAngles:
        return JointAngles(
            j1=self.j1,
            j2=self.j2,
            j3=self.j3,
            j4=self.j4,
            j5=self.j5,
            j6=gripper_angle_deg,
        )


def degrees_to_radians(angle_deg: float) -> float:
    return math.radians(angle_deg)
