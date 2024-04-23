from typing import List, Tuple
import cv2
import requests
import logging
from io import BytesIO
import numpy as np

from src.logging.logging_config import setup_logging

class DetectionHandler:
    """
    DetectionHandler class for sending

    Methods:
        send_image_for_detection: Sends image for detection.
        scale_coordinates: Scales the coordinates of the bounding boxes.
        draw_bounding_boxes: Draws bounding boxes on the image frame.
        process_frame: Processes the image frame.
    """
    def __init__(self):
        self.url = "http://192.168.50.62:5000/detect"
        setup_logging()
        self.logger = logging.getLogger()

    def send_image_for_detection(self, frame: np.ndarray) -> List[List[int]]:
        """
        Sends image for detection.

        Args:
            frame (np.ndarray): The image frame to be sent for detection.

        Returns:
            List[List[int]]: The list of bounding boxes.
        """
        try:
            _, img_encoded = cv2.imencode('.jpg', frame)
            img_stream = BytesIO(img_encoded.tobytes())
            files = {"image": ("image.jpg", img_stream, "image/jpeg")}
            response = requests.post(self.url, files=files)
            response.raise_for_status()
            return response.json().get('result_boxes', [])
        except Exception as e:
            self.logger.error(f"Error sending image for detection: {e}")
            return []

    def scale_coordinates(self, frame: np.ndarray, boxes: List[List[int]], input_size: Tuple[int, int] = (640, 640)) -> List[List[int]]:
        """
        Scales the coordinates of the bounding boxes.

        Args:
            frame (np.ndarray): The image frame.
            boxes (List[List[int]]): The list of bounding boxes.
            input_size (Tuple[int, int], optional): The input size. Defaults to (640, 640).

        Returns:
            List[List[int]]: The list of scaled bounding boxes.
        """
        try:
            orig_h, orig_w = frame.shape[:2]
            scale_w, scale_h = orig_w / input_size[0], orig_h / input_size[1]
            scaled_boxes = []
            for box in boxes:
                x1, y1, x2, y2 = box
                x1 = int(x1 * scale_w)
                y1 = int(y1 * scale_h)
                x2 = int(x2 * scale_w)
                y2 = int(y2 * scale_h)
                scaled_boxes.append([x1, y1, x2, y2])
            return scaled_boxes
        except Exception as e:
            self.logger.error(f"Error scaling coordinates: {e}")
            return []

    def draw_bounding_boxes(self, frame: np.ndarray, boxes: List[List[int]]) -> np.ndarray:
        """
        Draws bounding boxes on the image frame.

        Args:
            frame (np.ndarray): The image frame.
            boxes (List[List[int]]): The list of bounding boxes.

        Returns:
            np.ndarray: The image frame with bounding boxes.
        """
        try:
            for box in boxes:
                x1, y1, x2, y2 = box
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            return frame
        except Exception as e:
            self.logger.error(f"Error drawing bounding boxes: {e}")
            return frame

    def process_frame(self, frame: np.ndarray) -> Tuple[np.ndarray, List[List[int]]]:
        """
        Processes the image frame.

        Args:
            frame (np.ndarray): The image frame.

        Returns:
            Tuple[np.ndarray, List[List[int]]]: The image frame and the list of bounding boxes.
        """
        try:
            boxes = self.send_image_for_detection(frame)
            if boxes:  
                boxes = self.scale_coordinates(frame, boxes)
            return frame, boxes
        except Exception as e:
            self.logger.error(f"Error processing frame: {e}")
            return frame, []

