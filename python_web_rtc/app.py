from aiohttp import web
from aiortc import RTCSessionDescription
from webRTC.peer_factory import create_peer

pcs = set()

async def offer(request):
    data = await request.json()

    pc = create_peer()
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

if __name__ == "__main__":
    web.run_app(app, port=8080)
