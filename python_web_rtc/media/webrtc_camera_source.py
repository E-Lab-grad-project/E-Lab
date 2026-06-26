import cv2
import asyncio

class WebRTCCameraSource:

    def __init__(self, track):

       self.track = track
       self.frame = None

       loop = asyncio.get_running_loop()
    
       loop.create_task(
       self.reader()
    )

    async def reader(self):

        while True:

            video = await self.track.recv()

            img = video.to_ndarray(
                format="bgr24"
            )

            self.frame = img

    def read(self):

        if self.frame is None:
            return None

        return self.frame.copy()