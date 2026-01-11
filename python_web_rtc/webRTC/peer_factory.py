from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer
from webRTC.tracks import VideoTrack
from media.video_source import OpenCVCameraSource
from media.yolo.processor import YoloFrameProcessor
from media.yolo.detector import YoloDetector
from core.config import STUN_SERVERS
from robot_control import RobotController

def create_peer():
    config = RTCConfiguration(
        iceServers=[RTCIceServer(urls=STUN_SERVERS)]
    )

    pc = RTCPeerConnection(configuration=config)

    source = OpenCVCameraSource()
    processor = YoloFrameProcessor(detector=YoloDetector(target_class="cup", model_path="yolov8n.pt"), robot_controller=RobotController())

    pc.addTrack(VideoTrack(source, processor))
    return pc
