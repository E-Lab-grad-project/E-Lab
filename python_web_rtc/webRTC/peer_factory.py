from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer
from webRTC.tracks import VideoTrack
from media.video_source import OpenCVCameraSource
from media.yolo.processor import YoloFrameProcessor
from media.yolo.mixed_grid_pi import MixedGridProcessor
from core.config import STUN_SERVERS, CAMERA_TYPE
from robot_control import RobotController
from media.webrtc_camera_source import WebRTCCameraSource


# from media.udp_camera_source import UDPCameraSource
from media.pi_track_store import get_pi_track

def create_camera():

    print("📡 waiting WebRTC stream")

    track = get_pi_track()

    if track is None:
        raise RuntimeError(
            "Pi stream not connected"
        )

    return WebRTCCameraSource(track)


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
