from src.reolink.utils.CredentialHandler import CredentialHandler
from src.logging.logging_config import setup_logging
from src.reolink.utils.DetectionHandler import DetectionHandler

import logging
import cv2
import threading
import time
import os

class CameraController:
    """
    Class to control the cameras and handle image capturing.

    Updated to allow immediate stopping of the image capturing process.
    """
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

    def camera_capture(self) -> None:
        """
        Continuously captures images from the cameras, adjusting dynamically to changes in the save_interval.
        """
        last_capture_time = [time.time()] * len(self.urls)  # Initialize the last capture time for each camera
        while not self.stop_event.is_set():
            for camera_index, url in enumerate(self.urls):
                current_time = time.time()
                if current_time - last_capture_time[camera_index] >= self.save_interval:
                    if self.stop_event.is_set():  
                        break
                    try:
                        cap = cv2.VideoCapture(url)
                        ret, frame = cap.read()
                        print(self.detect.process_frame(frame))
                        if ret:
                            self.save_image(camera_index, frame)
                        cap.release()
                        last_capture_time[camera_index] = current_time  # Update the last capture time for the current camera
                    except Exception as e:
                        self.logger.error(f"Error capturing image from camera {camera_index}: {e}")
            time.sleep(1)

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

    def start_capture(self) -> None:
        """
        Starts the image capturing process, with immediate start capability.
        """
        with self.state_lock:
            if self.capture_images:
                self.logger.info("Image capturing is already running.")
                return
            self.capture_images = True
            self.stop_event.clear()  # Ensure the stop event is reset.
            self.thread = threading.Thread(target=self.camera_capture, daemon=True)
            self.thread.start()
            self.logger.info("Camera capture started.")

    def stop_capture(self) -> None:
        """
        Stops the image capturing process immediately.
        """
        with self.state_lock:
            if not self.capture_images:
                self.logger.info("Image capturing is not running.")
                return
            self.capture_images = False
            self.stop_event.set()  # Signal the thread to stop.
            self.thread.join()  # Wait for the thread to finish.
            self.logger.info("Camera capture stopped immediately.")

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
