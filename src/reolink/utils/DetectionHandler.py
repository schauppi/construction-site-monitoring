import cv2
import requests
from io import BytesIO

class DetectionHandler:
    def __init__(self, ):
        self.url = "http://192.168.50.62:5000/detect"

    def send_image_for_detection(self, frame):

        _, img_encoded = cv2.imencode('.jpg', frame)

        img_stream = BytesIO(img_encoded.tobytes())

        files = {"image": ("image.jpg", img_stream, "image/jpeg")}

        response = requests.post(self.url, files=files)

        if response.status_code == 200:
            boxes = response.json()['result_boxes']
            return boxes
        else:
            return {"error": "Failed to get a valid response from the server."}

    def draw_bounding_boxes(self, frame, boxes):
        pass

    def process_frame(self, frame):
        boxes = self.send_image_for_detection(frame)
        return boxes