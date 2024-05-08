import logging
import cv2
import threading
import asyncio
import time
import os
import queue
import csv
from src.reolink.utils.CredentialHandler import CredentialHandler
from src.logging.logging_config import setup_logging
from src.reolink.utils.DetectionHandler import DetectionHandler
from typing import List, Tuple, Any

class CameraController:
    """
    Class to control the camera capturing process, including starting and stopping the process, setting the interval.

    Methods:
        camera_capture: Captures images from the cameras.
        run_detection: Runs the detection process.
        start_capture: Starts the camera capture and detection process.
        stop_capture: Stops the camera capture and detection process.
        arm_system: Arms the system for detection.
        disarm_system: Disarms the system for detection.
        save_image: Saves an image to the file system, with error handling, and sends alerts if the system is armed.
        write_detection_record: Writes detection data to CSV.
        send_detection_alert: Sends an alert message with an image if detections are found and the system is armed.
        is_capturing: Checks if the image capturing process is running.
        set_save_interval: Sets the interval between image captures, with better validation.
    """

    def __init__(self, cams: List[str], bot: Any, initial_interval: int = 300) -> None:
        """
        Initializes the CameraController class with logging, credential management, and detection setup.

        Args:
            cams (List[str]): List of camera identifiers.
            bot (Any): Bot instance for alert messaging.
            initial_interval (int): Initial interval between image captures.

        Return:
            None
        """
        setup_logging()
        self.logger = logging.getLogger()
        self.capture_images = True
        self.save_interval = initial_interval
        self.save_path = "/media/david/DAVID"
        self.urls = [CredentialHandler(cam).url for cam in cams]
        self.state_lock = threading.Lock()
        self.stop_event = threading.Event()
        self.detect = DetectionHandler()
        self.frame_queue = queue.Queue(maxsize=10) 
        self.detection_thread = threading.Thread(target=self.run_detection, daemon=True)
        self.bot = bot
        self.armed = False 
        self.frame_buffer = {index: [] for index in range(len(self.urls))}
        

    def camera_capture(self) -> None:
        """
        Captures images from the cameras at the specified interval and stores them in a buffer.

        Args:
            None

        Return:
            None
        """
        last_capture_time = time.time()
        while not self.stop_event.is_set():
            current_time = time.time()
            if current_time - last_capture_time >= self.save_interval:
                for camera_index, url in enumerate(self.urls):
                    cap = cv2.VideoCapture(url)
                    ret, frame = cap.read()
                    if ret:
                        timestamp = time.time()
                        self.frame_buffer[camera_index].append((timestamp, frame))
                    else:
                        self.logger.error(f"Failed to capture image from camera {camera_index}")
                    cap.release()
                if len(min(self.frame_buffer.values(), key=len)) > 0:  
                    self.align_and_process_frames()
                last_capture_time = current_time
            time.sleep(0.1)  

    def align_and_process_frames(self):
        """
        Aligns frames from the buffer and processes them for detection.

        Args:
            None

        Return:
            None
        """
        try:
            min_time = min([frames[0][0] for frames in self.frame_buffer.values() if frames])
            aligned_frames = []
            for index in self.frame_buffer:
                closest_frame = min(self.frame_buffer[index], key=lambda x: abs(x[0] - min_time))
                aligned_frames.append((index, closest_frame[1]))
                self.frame_buffer[index].clear()
            for camera_index, frame in aligned_frames:
                self.frame_queue.put((camera_index, frame))
        except Exception as e:
            self.logger.error(f"Error aligning and processing frames: {e}")

    def run_detection(self) -> None:
        """
        Processes frames from the queue, performs object detection, and saves images and alerts if conditions are met.

        Args:
            None

        Return:
            None
        """
        while not self.stop_event.is_set() or not self.frame_queue.empty():
            try:
                camera_index, frame = self.frame_queue.get(timeout=3)
                frame, boxes = self.detect.process_frame(frame)
                self.save_image(camera_index, frame, boxes)
            except queue.Empty:
                continue 
            except Exception as e:
                self.logger.error(f"Error processing detection: {e}")

    def start_capture(self) -> None:
        """
        Starts the image capturing and detection process using threading.

        Args:
            None

        Return:
            None
        """
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
        """
        Stops the image capturing and detection process, ensuring all threads are joined.

        Args:
            None

        Return:
            None
        """
        with self.state_lock:
            if not self.capture_images:
                self.logger.info("Image capturing is not running.")
                return
            self.capture_images = False
            self.stop_event.set()
            self.thread.join()
            self.detection_thread.join()
            self.logger.info("Camera capture stopped immediately.")

    def arm_system(self) -> None:
        """
        Arms the detection system to allow for alert sending when detections occur.

        Args:
            None

        Return:
            None
        """
        self.armed = True
        self.logger.info("System armed.")

    def disarm_system(self) -> None:
        """
        Disarms the detection system to prevent alert sending when detections occur.

        Args:
            None

        Return:
            None
        """
        self.armed = False
        self.logger.info("System disarmed.")


    def save_image(self, camera_index: int, frame: Any, boxes: List[Tuple]) -> None:
        """
        Saves an image file to the specified directory and handles errors during the save process.

        Args:
            camera_index (int): Index of the camera.
            frame (Any): Image frame captured from the camera.
            boxes (List[Tuple]): Bounding boxes of detected objects.

        Return:
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

            self.write_detection_record(camera_index, filename, boxes)
            if boxes and self.armed:
                self.send_detection_alert(camera_index, frame, boxes)

        except Exception as e:
            self.logger.error(f"Error saving image for camera {camera_index}: {e}")

    def write_detection_record(self, camera_index: int, filename: str, boxes: List[Tuple]) -> None:
        """
        Writes detection data to a CSV file.

        Args:
            camera_index (int): Index of the camera.
            filename (str): Filename of the image.
            boxes (List[Tuple]): Bounding boxes of detected objects.

        Return:
            None
        """
        csv_file_path = os.path.join(self.save_path, f'detections_{camera_index}.csv')
        with open(csv_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([filename, boxes])

    def send_detection_alert(self, camera_index: int, frame: Any, boxes: List[Tuple]) -> None:
        """
        Sends an alert message if detections are found and the system is armed.

        Args:
            camera_index (int): Index of the camera.
            frame (Any): Image frame with detected objects.
            boxes (List[Tuple]): Bounding boxes of detected objects.

        Return:
            None
        """
        alert_message = f"Detected an object in camera {camera_index}"
        bbox_frame = self.detect.draw_bounding_boxes(frame, boxes)
        if not self.bot.loop.is_closed():
            self.bot.loop.call_soon_threadsafe(
                self.bot.loop.create_task,
                self.bot.send_alert(alert_message, bbox_frame)
            )
        else:
            self.logger.error("Attempted to send alert, but the event loop is closed.")

    def is_capturing(self) -> bool:
        """
        Checks if the image capturing process is currently running.

        Args:
            None

        Return:
            bool: True if capturing is active, False otherwise.
        """
        return self.capture_images

    def set_save_interval(self, interval: int) -> None:
        """
        Sets the interval between image captures with validation.

        Args:
            interval (int): New interval time in seconds.

        Return:
            None
        """
        if interval < 1:
            self.logger.error("Invalid save interval. It must be a positive integer.")
            return
        with self.state_lock:
            self.save_interval = interval
        self.logger.info(f"Set save interval to {interval} seconds.")
