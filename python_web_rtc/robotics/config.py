"""Configurable parameters for the robotics pipeline."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class CameraIntrinsics:
    """Pinhole camera intrinsic parameters (pixels + focal lengths)."""

    fx: float
    fy: float
    cx: float
    cy: float

    def as_matrix(self) -> np.ndarray:
        """Return the 3x3 intrinsic matrix K."""
        return np.array(
            [
                [self.fx, 0.0, self.cx],
                [0.0, self.fy, self.cy],
                [0.0, 0.0, 1.0],
            ],
            dtype=np.float64,
        )


@dataclass(frozen=True)
class DepthConfig:
    """Maps normalized detection depth to metric camera-frame depth (metres)."""

    z_near_m: float = 0.15
    z_far_m: float = 0.80

    def normalized_to_meters(self, z_normalized: float) -> float:
        z = float(np.clip(z_normalized, 0.0, 1.0))
        return self.z_near_m + z * (self.z_far_m - self.z_near_m)


@dataclass(frozen=True)
class GraspOrientationConfig:
    """Default grasp orientation in degrees (easy to tune later)."""

    roll_deg: float = 180.0
    pitch_deg: float = 0.0
    yaw_deg: float = 90.0


@dataclass(frozen=True)
class MotionPlannerConfig:
    """Pick-and-place motion parameters."""

    approach_height_m: float = 0.10
    grasp_depth_offset_m: float = 0.0
    retreat_height_m: float = 0.12
    gripper_open_angle_deg: float = 90.0
    gripper_close_angle_deg: float = 10.0
    step_delay_s: float = 0.5
    move_home_before_pick: bool = True


@dataclass(frozen=True)
class PipelineConfig:
    """Detection polling and target-selection settings."""

    polling_interval_s: float = 0.15
    min_confidence: float = 0.40
    cooldown_after_pick_s: float = 3.0
    enabled: bool = False


@dataclass
class RoboticsConfig:
    """Root configuration object for the robotics stack."""

    intrinsics: CameraIntrinsics = field(
        default_factory=lambda: CameraIntrinsics(fx=615.0, fy=615.0, cx=320.0, cy=240.0)
    )
    depth: DepthConfig = field(default_factory=DepthConfig)
    grasp_orientation: GraspOrientationConfig = field(default_factory=GraspOrientationConfig)
    motion: MotionPlannerConfig = field(default_factory=MotionPlannerConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    # 4x4 homogeneous transform: maps camera-frame points into robot-base frame.
    camera_to_robot_transform: np.ndarray = field(
        default_factory=lambda: np.eye(4, dtype=np.float64)
    )

    def __post_init__(self) -> None:
        matrix = np.asarray(self.camera_to_robot_transform, dtype=np.float64)
        if matrix.shape != (4, 4):
            raise ValueError("camera_to_robot_transform must be 4x4")
        self.camera_to_robot_transform = matrix

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RoboticsConfig:
        intrinsics_data = data.get("intrinsics", {})
        depth_data = data.get("depth", {})
        grasp_data = data.get("grasp_orientation", {})
        motion_data = data.get("motion", {})
        pipeline_data = data.get("pipeline", {})

        transform = data.get("camera_to_robot_transform")
        if transform is None:
            transform_matrix = np.eye(4, dtype=np.float64)
        else:
            transform_matrix = np.asarray(transform, dtype=np.float64)

        return cls(
            intrinsics=CameraIntrinsics(
                fx=float(intrinsics_data.get("fx", 615.0)),
                fy=float(intrinsics_data.get("fy", 615.0)),
                cx=float(intrinsics_data.get("cx", 320.0)),
                cy=float(intrinsics_data.get("cy", 240.0)),
            ),
            depth=DepthConfig(
                z_near_m=float(depth_data.get("z_near_m", 0.15)),
                z_far_m=float(depth_data.get("z_far_m", 0.80)),
            ),
            grasp_orientation=GraspOrientationConfig(
                roll_deg=float(grasp_data.get("roll_deg", 180.0)),
                pitch_deg=float(grasp_data.get("pitch_deg", 0.0)),
                yaw_deg=float(grasp_data.get("yaw_deg", 90.0)),
            ),
            motion=MotionPlannerConfig(
                approach_height_m=float(motion_data.get("approach_height_m", 0.10)),
                grasp_depth_offset_m=float(motion_data.get("grasp_depth_offset_m", 0.0)),
                retreat_height_m=float(motion_data.get("retreat_height_m", 0.12)),
                gripper_open_angle_deg=float(
                    motion_data.get("gripper_open_angle_deg", 90.0)
                ),
                gripper_close_angle_deg=float(
                    motion_data.get("gripper_close_angle_deg", 10.0)
                ),
                step_delay_s=float(motion_data.get("step_delay_s", 0.5)),
                move_home_before_pick=bool(motion_data.get("move_home_before_pick", True)),
            ),
            pipeline=PipelineConfig(
                polling_interval_s=float(pipeline_data.get("polling_interval_s", 0.15)),
                min_confidence=float(pipeline_data.get("min_confidence", 0.40)),
                cooldown_after_pick_s=float(pipeline_data.get("cooldown_after_pick_s", 3.0)),
                enabled=bool(pipeline_data.get("enabled", False)),
            ),
            camera_to_robot_transform=transform_matrix,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> RoboticsConfig:
        with open(path, encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))

    @classmethod
    def from_env(cls) -> RoboticsConfig:
        """Load optional JSON config path and apply environment overrides."""
        config_path = os.environ.get("ROBOTICS_CONFIG_PATH")
        if config_path and Path(config_path).is_file():
            config = cls.from_file(config_path)
        else:
            config = cls()

        enabled = os.environ.get("ROBOTICS_ENABLED", "").lower() in ("1", "true", "yes")
        pipeline = PipelineConfig(
            polling_interval_s=config.pipeline.polling_interval_s,
            min_confidence=config.pipeline.min_confidence,
            cooldown_after_pick_s=config.pipeline.cooldown_after_pick_s,
            enabled=enabled or config.pipeline.enabled,
        )
        return RoboticsConfig(
            intrinsics=config.intrinsics,
            depth=config.depth,
            grasp_orientation=config.grasp_orientation,
            motion=config.motion,
            pipeline=pipeline,
            camera_to_robot_transform=config.camera_to_robot_transform,
        )
