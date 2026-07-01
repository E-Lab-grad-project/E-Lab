import os

import cv2
from core.interface import VideoSource
from core.config import CAMERA_INDEX, FRAME_WIDTH, FRAME_HEIGHT


def _open_capture(index: int, backend: int | None) -> cv2.VideoCapture | None:
    cap = cv2.VideoCapture(index) if backend is None else cv2.VideoCapture(index, backend)
    if not cap.isOpened():
        cap.release()
        return None
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


def open_webcam(index: int = CAMERA_INDEX) -> cv2.VideoCapture:
    """Try common Windows/Linux backends until one opens the camera."""
    attempts: list[tuple[str, int | None]] = [("default", None)]

    if os.name == "nt":
        attempts.extend(
            [
                ("MSMF", cv2.CAP_MSMF),
                ("DSHOW", cv2.CAP_DSHOW),
            ]
        )

    errors: list[str] = []
    for label, backend in attempts:
        cap = _open_capture(index, backend)
        if cap is not None:
            print(f"Webcam opened: index={index}, backend={label}")
            return cap
        errors.append(label)

    raise RuntimeError(
        f"Camera not accessible at index {index}. Tried backends: {', '.join(errors)}"
    )


class OpenCVCameraSource(VideoSource):
    def __init__(self):
        self.cap = open_webcam(CAMERA_INDEX)

    def read(self):
        ret, frame = self.cap.read()
        if not ret:
            raise RuntimeError("Failed to read frame from camera")
        return frame
