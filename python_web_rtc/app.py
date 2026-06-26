from aiohttp import web
from aiortc import RTCSessionDescription
from webRTC.peer_factory import create_peer

from media.pi_track_store import set_pi_track
from aiortc import RTCPeerConnection

pcs = set()


pi_pcs = set()

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


app = web.Application()
app.router.add_post("/offer", offer)
app.router.add_post("/pi-offer", pi_offer)

if __name__ == "__main__":
    print("routes loaded")
    web.run_app(app, port=8080)
