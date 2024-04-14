import logging
import cv2
import threading
import time
import os
import queue
from src.reolink.utils.CredentialHandler import CredentialHandler
from src.logging.logging_config import setup_logging
from src.reolink.utils.DetectionHandler import DetectionHandler

class CameraController:
    def __init__(self, cams: list, initial_interval: int = 300) -> None:
        setup_logging()
        self.logger = logging.getLogger(__name__)
        self.capture_images = False
        self.save_interval = initial_interval
        self.save_path = "/media/david/DAVID"
        self.urls = [CredentialHandler(cam).url for cam in cams]
        self.state_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.detect = DetectionHandler()
        self.frame_queue = queue.Queue(maxsize=10)  # Adjust size as necessary
        self.detection_thread = threading.Thread(target=self.run_detection, daemon=True)

    def camera_capture(self) -> None:
        last_capture_time = [time.time()] * len(self.urls)
        while not self.stop_event.is_set():
            for camera_index, url in enumerate(self.urls):
                if time.time() - last_capture_time[camera_index] >= self.save_interval:
                    cap = cv2.VideoCapture(url)
                    ret, frame = cap.read()
                    if ret:
                        self.frame_queue.put((camera_index, frame))
                    cap.release()
                    last_capture_time[camera_index] = time.time()
                if self.stop_event.is_set():
                    break
            time.sleep(1)

    def run_detection(self) -> None:
        while not self.stop_event.is_set() or not self.frame_queue.empty():
            try:
                camera_index, frame = self.frame_queue.get(timeout=3)
                bb_frame = self.detect.process_frame(frame)
                self.save_image(camera_index, bb_frame)
            except queue.Empty:
                continue  # Handle empty queue

    def start_capture(self) -> None:
        with self.state_lock:
            if self.capture_images:
                self.logger.info("Image capturing is already running.")
                return
            self.capture_images = True
            self.stop_event.clear()
            self.detection_thread.start()
            self.thread = threading.Thread(target=self.camera_capture, daemon=True)
            self.thread.start()
            self.logger.info("Camera capture and detection started.")

    def stop_capture(self) -> None:
        with self.state_lock:
            if not self.capture_images:
                self.logger.info("Image capturing is not running.")
                return
            self.capture_images = False
            self.stop_event.set()
            self.thread.join()
            self.detection_thread.join()
            self.logger.info("Camera capture stopped immediately.")

    def save_image(self, camera_index: int, frame) -> None:
        """
        Saves an image to the file system, with error handling.
        """
        try:
            camera_path = os.path.join(self.save_path, f'cam_{camera_index}')
            if not os.path.exists(camera_path):
                os.makedirs(camera_path)

            timestamp = int(time.time())
            filename = f"{timestamp}.jpg"
            file_path = os.path.join(camera_path, filename)
            cv2.imwrite(file_path, frame)
            self.logger.info(f"Saved image {filename} for camera {camera_index}")
        except Exception as e:
            self.logger.error(f"Error saving image for camera {camera_index}: {e}")

    def is_capturing(self) -> bool:
        """
        Checks if the image capturing process is running.
        """
        return self.capture_images

    def set_save_interval(self, interval: int) -> None:
        """
        Sets the interval between image captures, with better validation.
        """
        if interval < 1:
            self.logger.error("Invalid save interval. It must be a positive integer.")
            return
        with self.state_lock:
            self.save_interval = interval
        self.logger.info(f"Set save interval to {interval} seconds.")
