"""Inverse kinematics solver interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from robotics.pose import JointAngles, Pose


class IKSolver(ABC):
    """
    Abstract inverse kinematics interface.

    Plug in your own 6-DOF IK implementation by subclassing and overriding solve().
  """

    @abstractmethod
    def solve(self, target_pose: Pose) -> JointAngles:
        """Return joint angles (degrees) that reach target_pose."""


class UnconfiguredIKSolver(IKSolver):
    """Placeholder that fails fast until a real solver is wired in."""

    def solve(self, target_pose: Pose) -> JointAngles:
        raise NotImplementedError(
            "No IK solver configured. Subclass IKSolver and register your implementation "
            "via robotics.integration.create_robotics_pipeline(ik_solver=YourIKSolver())."
        )
