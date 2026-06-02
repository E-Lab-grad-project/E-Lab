from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer
from webRTC.tracks import VideoTrack
from media.video_source import OpenCVCameraSource
from media.yolo.processor import YoloFrameProcessor
from media.yolo.mixeg_grid_pi import MixedGridProcessor
from core.config import STUN_SERVERS, CAMERA_TYPE
from robot_control import RobotController

def create_camera():
    if CAMERA_TYPE == "picamera":
        try:
            from media.pi_camera_source import PiCamera2Source
            print("🍓 Using Raspberry Pi Camera")
            return PiCamera2Source()
        except ImportError:
            print("⚠ Picamera2 not available. Falling back to OpenCV camera.")
            print("💻 Using OpenCV Camera")
            return OpenCVCameraSource()
    else:
        print("💻 Using OpenCV Camera")
        return OpenCVCameraSource()


def create_peer(processor_type: str = "yolo"):
    processor_type = (processor_type or "yolo").strip().lower()

    config = RTCConfiguration(
        iceServers=[RTCIceServer(urls=STUN_SERVERS)]
    )

    pc = RTCPeerConnection(configuration=config)
    source = create_camera()

    if processor_type == "mixed_grid" or processor_type == "mixedgrid" or processor_type == "grid":
        processor = MixedGridProcessor(robot_controller=RobotController())
    else:
        processor = YoloFrameProcessor(robot_controller=RobotController())

    pc.addTrack(VideoTrack(source, processor))
    return pc
