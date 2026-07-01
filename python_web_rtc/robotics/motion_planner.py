"""Pick-and-place motion sequencing."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum, auto

from robotics.config import MotionPlannerConfig
from robotics.ik_solver import IKSolver
from robotics.pose import JointAngles, Pose
from robotics.robot_controller import RobotController

logger = logging.getLogger(__name__)


class MotionPhase(Enum):
    HOME = auto()
    APPROACH = auto()
    DESCEND = auto()
    GRASP = auto()
    RETREAT = auto()
    COMPLETE = auto()


@dataclass(frozen=True)
class MotionStep:
    phase: MotionPhase
    target_pose: Pose


class MotionPlanner:
    """
    Plans and executes a vertical pick sequence:

        Home -> Above object -> Down -> Close gripper -> Up
    """

    def __init__(
        self,
        robot: RobotController,
        ik_solver: IKSolver,
        config: MotionPlannerConfig,
    ) -> None:
        self._robot = robot
        self._ik = ik_solver
        self._config = config

    def plan_pick_sequence(self, grasp_pose: Pose) -> list[MotionStep]:
        approach_z = grasp_pose.z + self._config.approach_height_m
        grasp_z = grasp_pose.z + self._config.grasp_depth_offset_m
        retreat_z = grasp_pose.z + self._config.retreat_height_m

        return [
            MotionStep(MotionPhase.HOME, grasp_pose),
            MotionStep(
                MotionPhase.APPROACH,
                grasp_pose.with_position(grasp_pose.x, grasp_pose.y, approach_z),
            ),
            MotionStep(
                MotionPhase.DESCEND,
                grasp_pose.with_position(grasp_pose.x, grasp_pose.y, grasp_z),
            ),
            MotionStep(
                MotionPhase.GRASP,
                grasp_pose.with_position(grasp_pose.x, grasp_pose.y, grasp_z),
            ),
            MotionStep(
                MotionPhase.RETREAT,
                grasp_pose.with_position(grasp_pose.x, grasp_pose.y, retreat_z),
            ),
        ]

    def execute_pick(self, grasp_pose: Pose) -> None:
        """
        Run the pick sequence (blocking).

        Must be called from the robotics worker thread, never from the YOLO thread.
        """
        steps = self.plan_pick_sequence(grasp_pose)
        logger.info("Starting pick sequence with %d steps", len(steps))

        if self._config.move_home_before_pick:
            logger.info("Phase HOME")
            self._robot.home()
            self._wait()

        for step in steps:
            if step.phase == MotionPhase.HOME:
                continue

            logger.info("Phase %s -> pose (%.3f, %.3f, %.3f)", step.phase.name, step.target_pose.x, step.target_pose.y, step.target_pose.z)
            joints = self._ik.solve(step.target_pose)

            if step.phase == MotionPhase.GRASP:
                joints = joints.with_gripper(self._config.gripper_close_angle_deg)
            else:
                joints = joints.with_gripper(self._config.gripper_open_angle_deg)

            self._robot.move_joints(joints)
            self._wait()

        logger.info("Pick sequence complete")

    def _wait(self) -> None:
        if self._config.step_delay_s > 0:
            time.sleep(self._config.step_delay_s)
