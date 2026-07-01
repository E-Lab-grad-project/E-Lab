"""Pinhole camera geometry: pixel + depth to camera-frame 3D coordinates."""

from __future__ import annotations

import logging

from robotics.config import CameraIntrinsics, DepthConfig
from robotics.pose import Point3D

logger = logging.getLogger(__name__)


def pixel_to_camera(
    u: float,
    v: float,
    depth_m: float,
    intrinsics: CameraIntrinsics,
) -> Point3D:
    """
    Convert image pixel (u, v) and metric depth Z into camera-frame coordinates.

    Pinhole model:
        X = (u - cx) * Z / fx
        Y = (v - cy) * Z / fy
        Z = depth

    Camera frame convention (OpenCV):
        +X right, +Y down, +Z forward (into the scene).
    """
    if depth_m <= 0.0:
        raise ValueError(f"Depth must be positive, got {depth_m}")

    z = depth_m
    x = (u - intrinsics.cx) * z / intrinsics.fx
    y = (v - intrinsics.cy) * z / intrinsics.fy

    point = Point3D(x=x, y=y, z=z)
    logger.debug(
        "pixel_to_camera: (u=%.1f, v=%.1f, Z=%.3f) -> (X=%.3f, Y=%.3f, Z=%.3f)",
        u,
        v,
        depth_m,
        point.x,
        point.y,
        point.z,
    )
    return point


def normalized_depth_to_meters(z_normalized: float, depth_config: DepthConfig) -> float:
    """Map API normalized depth [0, 1] to metric depth for pinhole projection."""
    return depth_config.normalized_to_meters(z_normalized)
