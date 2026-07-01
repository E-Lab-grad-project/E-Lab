"""Hardware-agnostic robot controller interface."""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

from robotics.ik_solver import IKSolver
from robotics.pose import JointAngles, Pose

logger = logging.getLogger(__name__)


class RobotController(ABC):
    """
    Abstract 6-DOF arm controller.

    Concrete drivers (serial, ROS, vendor SDK) implement the transport layer only.
    """

    def __init__(self, ik_solver: Optional[IKSolver] = None) -> None:
        self._ik_solver = ik_solver

    def bind_ik_solver(self, ik_solver: IKSolver) -> None:
        self._ik_solver = ik_solver

    @abstractmethod
    def move_joints(self, joints: JointAngles) -> None:
        """Command the arm to the given joint angles."""

    def move_pose(self, pose: Pose) -> None:
        """Solve IK and command joint angles (requires a bound IK solver)."""
        if self._ik_solver is None:
            raise RuntimeError("move_pose requires an IK solver; call bind_ik_solver() first")
        joints = self._ik_solver.solve(pose)
        self.move_joints(joints)

    @abstractmethod
    def home(self) -> None:
        """Move the arm to a safe home configuration."""

    @abstractmethod
    def stop(self) -> None:
        """Emergency stop / cancel active motion."""

    @abstractmethod
    def close(self) -> None:
        """Release hardware resources."""


class NullRobotController(RobotController):
    """
    Development controller that logs commands without touching hardware.

    Useful while IK and calibration are still being tuned.
    """

    def __init__(self, ik_solver: Optional[IKSolver] = None) -> None:
        super().__init__(ik_solver=ik_solver)
        self._last_joints: Optional[JointAngles] = None

    def move_joints(self, joints: JointAngles) -> None:
        self._last_joints = joints
        logger.info(
            "NullRobotController.move_joints: [%.1f, %.1f, %.1f, %.1f, %.1f, %.1f]",
            joints.j1,
            joints.j2,
            joints.j3,
            joints.j4,
            joints.j5,
            joints.j6,
        )
        time.sleep(0.05)

    def home(self) -> None:
        logger.info("NullRobotController.home()")
        time.sleep(0.05)

    def stop(self) -> None:
        logger.warning("NullRobotController.stop()")

    def close(self) -> None:
        logger.info("NullRobotController.close()")

    @property
    def last_joints(self) -> Optional[JointAngles]:
        return self._last_joints
