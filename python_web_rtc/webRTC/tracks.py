import cv2
from aiortc import VideoStreamTrack
from av import VideoFrame
from core.interface import VideoSource, frameProcessor


class VideoTrack(VideoStreamTrack):
    def __init__(self, source: VideoSource, processor: frameProcessor = frameProcessor):
        super().__init__()
        self.source = source
        self.processor = processor

    async def recv(self):
        pts, time_base = await self.next_timestamp()

        frame = self.source.read()
        frame = self.processor.process(frame)


        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        video_frame = VideoFrame.from_ndarray(frame, format="rgb24")
        video_frame.pts = pts
        video_frame.time_base = time_base

        return video_frame
