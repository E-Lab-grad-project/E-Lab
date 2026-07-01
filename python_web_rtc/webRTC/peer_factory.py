from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer
from webRTC.tracks import VideoTrack
from media.video_source import OpenCVCameraSource
from core.config import STUN_SERVERS
from robot_control import RobotController
from hand_robot_control import get_hand_controller
from media.webrtc_camera_source import WebRTCCameraSource

from media.pi_track_store import get_pi_track


def create_camera():
    print("📡 waiting WebRTC stream")

    track = get_pi_track()

    if track is None:
        raise RuntimeError("Pi stream not connected")

    return WebRTCCameraSource(track)


def _create_processor(processor_type: str):
    if processor_type == "hand_mirror":
        from media.hand_mirror.processor import HandMirrorProcessor

        return HandMirrorProcessor(hand_controller=get_hand_controller())

    if processor_type in ("mixed_grid", "mixedgrid", "grid"):
        from media.yolo.mixed_grid_pi import MixedGridProcessor

        return MixedGridProcessor(robot_controller=RobotController())

    from media.yolo.processor import YoloFrameProcessor

    return YoloFrameProcessor(robot_controller=RobotController())


def create_peer(processor_type: str = "yolo"):
    processor_type = (processor_type or "yolo").strip().lower()

    config = RTCConfiguration(iceServers=[RTCIceServer(urls=STUN_SERVERS)])

    pc = RTCPeerConnection(configuration=config)

    if processor_type == "hand_mirror":
        source = OpenCVCameraSource()
    else:
        source = create_camera()

    processor = _create_processor(processor_type)
    pc.addTrack(VideoTrack(source, processor))
    return pc
