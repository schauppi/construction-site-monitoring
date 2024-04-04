from src.reolink.utils.CredentialHandler import CredentialHandler
import multiprocessing
import cv2
from typing import Any

class StreamingHandler():
    """
    A class to handle the streaming of multiple camera feeds.

    Methods:
        stream: Stream the camera feeds.
    """

    def __init__(self, cams, queue=None) -> None:
        self.cams = cams
        self.urls = [CredentialHandler(cam).url for cam in cams]
        self.processes = [None for _ in cams]
        self.queue = queue

    def stream(self, url) -> Any:
        """
        Stream the camera feed.

        Args:
            None

        Returns:
            cv2.frame: The frame from the camera feed.
        """
        try:
            cap = cv2.VideoCapture(url)
            ret, frame = cap.read()
            if ret:
                return frame
            else:
                return None
        except Exception as e:
            print(f"An error occurred while streaming: {e}")
            return None

    def stream_camera(self, cam, url):
        cap = cv2.VideoCapture(url)
        try:
            while True:
                ret, frame = cap.read()
                if ret and self.queue is not None:
                    self.queue.put((cam, frame))
        finally:
            cap.release()

    def start_streaming(self,):
        for i in range(len(self.cams)):
            self.processes[i] = multiprocessing.Process(target=self.stream_camera, args=(self.cams[i], self.urls[i]))
            self.processes[i].start()

    def join(self):
        for process in self.processes:
            if process is not None:
                process.join()
            
    def get_current_frames(self):
        frames = {}
        while len(frames) < len(self.cams):
            cam, frame = self.queue.get()
            if cam not in frames:
                frames[cam] = frame
        return frames
    

    def stop_streaming(self):
        for process in self.processes:
            if process is not None:
                process.terminate()
                process.join()