import cv2
import multiprocessing
import time
from src.reolink.utils.CredentialHandler import CredentialHandler

class StreamingHandler:
    """
    A class to handle the streaming of multiple camera feeds.

    Methods:
        stream_camera: Stream the camera feed and put frames into the queue.
        start_streaming: Start streaming from all cameras.
        join: Wait for all streaming processes to finish.
        get_current_frames: Get the current frame from each camera.
        stop_streaming: Stop all streaming processes.
    """

    def __init__(self, cams: list, queue: multiprocessing.Queue = None) -> None:
        """
        Initialize the StreamingHandler with a list of cameras and an optional multiprocessing queue.

        Args:
            cams (list): A list of camera IDs.
            queue (multiprocessing.Queue, optional): A multiprocessing queue for storing frames. Defaults to None.
        """
        self.cams = cams
        self.urls = [CredentialHandler(cam).url for cam in cams]
        self.processes = []
        self.queue = multiprocessing.Queue(maxsize=10) if queue is None else queue
        self.stopped = multiprocessing.Event() 

    def stream_camera(self, cam: int, url: str, stopped: multiprocessing.Event) -> None:
        """
        Stream the camera feed and put frames into the queue.

        Args:
            cam (int): The camera ID.
            url (str): The camera URL.
            stopped (multiprocessing.Event): An event to stop the process.

        Returns:
            None
        """
        cap = cv2.VideoCapture(url)
        while not stopped.is_set():
            ret, frame = cap.read()
            if ret:
                try:
                    self.queue.put_nowait((cam, frame))  
                except multiprocessing.queues.Full:
                    pass 
            time.sleep(1 / self.FRAME_PROCESS_INTERVAL)  
        cap.release()

    def start_streaming(self):
        """
        Start streaming from all cameras.
        """
        for cam_id, cam_url in zip(self.cams, self.urls):
            process = multiprocessing.Process(
                target=self.stream_camera,
                args=(cam_id, cam_url, self.stopped)
            )
            process.start()
            self.processes.append(process)

    def join(self):
        """
        Wait for all streaming processes to finish.
        """
        for process in self.processes:
            process.join()

    def get_current_frames(self):
        """
        Get the current frame from each camera.
        """
        frames = {}
        while not all(cam in frames for cam in self.cams):
            try:
                cam, frame = self.queue.get_nowait()  
                frames[cam] = frame
            except multiprocessing.queues.Empty:
                break  
        return frames

    def stop_streaming(self):
        """
        Stop all streaming processes.
        """
        self.stopped.set()  
        for process in self.processes:
            process.terminate()  
            process.join(timeout=5)  
            if process.is_alive():
                print("Force killing the process.")
                process.kill()
        while not self.queue.empty():
            self.queue.get_nowait()  

    @property
    def FRAME_PROCESS_INTERVAL(self):
        return 5  

    @property
    def MAX_QUEUE_SIZE(self):
        return 10  

    @property
    def CPU_CORES(self):
        return multiprocessing.cpu_count()  
