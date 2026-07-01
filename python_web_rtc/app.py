from aiohttp import web
from aiortc import RTCSessionDescription
from webRTC.peer_factory import create_peer

from media.pi_track_store import set_pi_track
from media.hand_mirror.state import hand_mirror_state
from media.yolo.mixed_grid_pi import get_latest_detections
from aiortc import RTCPeerConnection
import os

pcs = set()
pi_pcs = set()
_robotics_bridge = None


async def _start_robotics(_app: web.Application) -> None:
    global _robotics_bridge
    if os.environ.get("ROBOTICS_ENABLED", "").lower() not in ("1", "true", "yes"):
        return
    from robotics.integration import configure_logging, start_robotics_bridge

    configure_logging()
    _robotics_bridge = start_robotics_bridge()


async def _stop_robotics(_app: web.Application) -> None:
    global _robotics_bridge
    if _robotics_bridge is not None:
        _robotics_bridge.stop()
        _robotics_bridge = None

async def pi_offer(request):

    data = await request.json()

    pc = RTCPeerConnection()

    pi_pcs.add(pc)

    @pc.on("track")
    def on_track(track):

        print("Track received:", track.kind)

        if track.kind == "video":

            set_pi_track(track)

        @track.on("ended")
        async def ended():

            print("PI TRACK ENDED")

    await pc.setRemoteDescription(

        RTCSessionDescription(
            sdp=data["sdp"],
            type=data["type"]
        )
    )

    answer = await pc.createAnswer()

    await pc.setLocalDescription(
        answer
    )

    return web.json_response({

        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type
    })

async def offer(request):
    data = await request.json()
    processor_type = data.get("processor") or data.get("processorType") or "yolo"

    pc = create_peer(processor_type=processor_type)
    pcs.add(pc)

    @pc.on("connectionstatechange")
    async def on_state():
        print("Connection state is %s" % pc.connectionState)
        if pc.connectionState in ["failed", "closed"]:
            pcs.discard(pc)
            await pc.close()
    await pc.setRemoteDescription(
        RTCSessionDescription(sdp=data["sdp"], type=data["type"])
    )

    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response({
        "sdp": pc.localDescription.sdp,
        "type": pc.localDescription.type}
    )


async def hand_mirror_set(request):
    data = await request.json()
    hand_mirror_state.mirroring_enabled = bool(data.get("enabled", False))
    return web.json_response({"mirroring": hand_mirror_state.mirroring_enabled})


async def hand_mirror_status(_request):
    return web.json_response(hand_mirror_state.to_dict())


async def detections_status(_request):
    return web.json_response({"detections": get_latest_detections()})


app = web.Application()
app.on_startup.append(_start_robotics)
app.on_cleanup.append(_stop_robotics)
app.router.add_post("/offer", offer)
app.router.add_post("/pi-offer", pi_offer)
app.router.add_post("/hand-mirror/mirror", hand_mirror_set)
app.router.add_get("/hand-mirror/status", hand_mirror_status)
app.router.add_get("/detections/status", detections_status)

if __name__ == "__main__":
    print("routes loaded")
    web.run_app(app, port=8080)
