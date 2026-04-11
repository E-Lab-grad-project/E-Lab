from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer
from webRTC.tracks import VideoTrack
from media.video_source import OpenCVCameraSource
from media.yolo.processor import YoloFrameProcessor
from media.yolo.detector import YoloDetector
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


def create_peer():
    config = RTCConfiguration(
        iceServers=[RTCIceServer(urls=STUN_SERVERS)]
    )

    pc = RTCPeerConnection(configuration=config)

    source = create_camera()
    processor = YoloFrameProcessor(detector=YoloDetector(target_class="cup", model_path="yolov8n.pt"), robot_controller=RobotController())

    pc.addTrack(VideoTrack(source, processor))
    return pc
