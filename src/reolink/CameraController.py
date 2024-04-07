from src.reolink.utils.CredentialHandler import CredentialHandler
from src.logging.logging_config import setup_logging

import logging
import cv2
import threading
import time
import os

class CameraController:
    """
    Class to control the cameras and handle image capturing.

    Methods:
        camera_capture: Continuously captures images from the cameras.
        save_image: Saves an image to the file system.
        start_capture: Starts the image capturing process.
        stop_capture: Stops the image capturing process.
        is_capturing: Checks if the image capturing process is running.
        set_save_interval: Sets the interval between image captures.
    """
    def __init__(self, cams: list, initial_interval: int = 300) -> None:
        """
        Initialize the CameraController with a list of cameras and an initial capture interval.
        """
        setup_logging()
        self.logger = logging.getLogger(__name__)
        self.capture_images = False
        self.save_interval = initial_interval
        self.save_path = "/media/david/DAVID"
        self.urls = [CredentialHandler(cam).url for cam in cams]
        self.state_lock = threading.Lock()
        self.thread = threading.Thread(target=self.camera_capture, daemon=True)
        self.thread.start()

    def camera_capture(self) -> None:
        """
        Continuously captures images from the cameras.

        Returns:
            None
        """
        while True:
            with self.state_lock:
                if self.capture_images:
                    for camera_index, url in enumerate(self.urls):
                        try:
                            cap = cv2.VideoCapture(url)
                            ret, frame = cap.read()
                            if ret:
                                self.save_image(camera_index, frame)
                            cap.release()
                        except Exception as e:
                            self.logger.error(f"Error capturing image from camera {camera_index}: {e}")
                    time.sleep(self.save_interval)  
            time.sleep(1)

    def save_image(self, camera_index: int, frame) -> None:
        """
        Saves an image to the file system.

        Args: 
            camera_index (int): Index of the camera.
            frame: Image frame to save.

        Returns:
            None
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
            self.logger.error(f"Error saving image from camera {camera_index}: {e}")

    def start_capture(self) -> None:
        """
        Starts the image capturing process.
        """
        with self.state_lock:
            self.capture_images = True
        self.logger.info("Started image capturing")

    def stop_capture(self) -> None:
        """
        Stops the image capturing process.
        """
        with self.state_lock:
            self.capture_images = False
        self.logger.info("Stopped image capturing")

    def is_capturing(self) -> bool:
        """
        Checks if the image capturing process is running.

        Returns:
            bool: True if the image capturing process is running, False otherwise.
        """
        return self.capture_images

    def set_save_interval(self, interval: int) -> None:
        """
        Sets the interval between image captures.

        Args:
            interval (int): The interval between image captures in seconds.

        Returns:
            None
        """
        with self.state_lock:
            self.save_interval = interval
        self.logger.info(f"Set save interval to {interval} seconds")