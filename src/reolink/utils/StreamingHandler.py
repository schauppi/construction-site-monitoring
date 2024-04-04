import cv2
import multiprocessing
from src.reolink.utils.CredentialHandler import CredentialHandler

class StreamingHandler():
    """
    A class to handle the streaming of multiple camera feeds.

    Methods:
        __init__: Initialize the StreamingHandler with a list of cameras and an optional multiprocessing queue.
        stream_camera: Stream the camera feed and put frames into the queue.
        start_streaming: Start streaming from all cameras.
        join: Wait for all streaming processes to finish.
        get_current_frames: Get the current frame from each camera.
        stop_streaming: Stop all streaming processes.
    """

    def __init__(self, cams, queue=None):
        """
        Initialize the StreamingHandler with a list of cameras and an optional multiprocessing queue.

        Args:
            cams (list): A list of camera IDs.
            queue (multiprocessing.Queue, optional): A multiprocessing queue for storing frames. Defaults to None.
        """
        self.cams = cams
        self.urls = [CredentialHandler(cam).url for cam in cams]
        self.processes = [None for _ in cams]
        self.queue = queue

    def stream_camera(self, cam, url):
        """
        Stream the camera feed and put frames into the queue.

        Args:
            cam (int): The camera ID.
            url (str): The URL of the camera feed.

        Returns:
            None
        """
        cap = cv2.VideoCapture(url)
        try:
            while True:
                ret, frame = cap.read()
                if ret and self.queue is not None:
                    self.queue.put((cam, frame))
        except Exception as e:
            print(f"An error occurred while streaming from camera {cam}: {e}")
        finally:
            cap.release()

    def start_streaming(self):
        """
        Start streaming from all cameras.

        Args:
            None

        Returns:
            None
        """
        for i in range(len(self.cams)):
            try:
                self.processes[i] = multiprocessing.Process(target=self.stream_camera, args=(self.cams[i], self.urls[i]))
                self.processes[i].start()
            except Exception as e:
                print(f"An error occurred while starting the stream for camera {self.cams[i]}: {e}")

    def join(self):
        """
        Wait for all streaming processes to finish.

        Args:
            None

        Returns:
            None
        """
        for process in self.processes:
            if process is not None:
                try:
                    process.join()
                except Exception as e:
                    print(f"An error occurred while joining the process: {e}")

    def get_current_frames(self):
        """
        Get the current frame from each camera.

        Args:
            None

        Returns:
            dict: A dictionary where the keys are the camera IDs and the values are the frames from those cameras.
        """
        frames = {}
        while len(frames) < len(self.cams):
            try:
                cam, frame = self.queue.get()
                if cam not in frames:
                    frames[cam] = frame
            except Exception as e:
                print(f"An error occurred while getting frames: {e}")
        return frames

    def stop_streaming(self):
        """
        Stop all streaming processes.

        Args:
            None

        Returns:
            None
        """
        for process in self.processes:
            if process is not None:
                try:
                    process.terminate()
                    process.join()
                except Exception as e:
                    print(f"An error occurred while stopping the stream: {e}")