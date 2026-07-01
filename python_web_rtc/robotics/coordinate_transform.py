"""Rigid transforms between camera and robot coordinate frames."""

from __future__ import annotations

import logging

import numpy as np

from robotics.pose import Point3D

logger = logging.getLogger(__name__)


class CoordinateTransformer:
    """
    Apply a fixed 4x4 homogeneous transform from camera frame to robot-base frame.

    Homogeneous multiplication:
        [X_r]   [R  t] [X_c]
        [Y_r] = [    ] [Y_c]
        [Z_r]   [0  1] [Z_c]
        [ 1 ]          [ 1 ]
    """

    def __init__(self, camera_to_robot_transform: np.ndarray) -> None:
        matrix = np.asarray(camera_to_robot_transform, dtype=np.float64)
        if matrix.shape != (4, 4):
            raise ValueError("camera_to_robot_transform must be shape (4, 4)")
        self._transform = matrix

    @property
    def transform(self) -> np.ndarray:
        return self._transform.copy()

    def camera_to_robot(self, camera_point: Point3D) -> Point3D:
        homogeneous = np.array(
            [camera_point.x, camera_point.y, camera_point.z, 1.0],
            dtype=np.float64,
        )
        robot_h = self._transform @ homogeneous
        robot_point = Point3D(
            x=float(robot_h[0]),
            y=float(robot_h[1]),
            z=float(robot_h[2]),
        )
        logger.debug(
            "camera_to_robot: (%.3f, %.3f, %.3f) -> (%.3f, %.3f, %.3f)",
            camera_point.x,
            camera_point.y,
            camera_point.z,
            robot_point.x,
            robot_point.y,
            robot_point.z,
        )
        return robot_point
