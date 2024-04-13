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
        
    def scale_coordinates(self, frame, boxes, input_size=(640, 640)):
        orig_h, orig_w = frame.shape[:2]
        scale_w, scale_h = orig_w / input_size[0], orig_h / input_size[1]
        for box in boxes:
            x1, y1, x2, y2 = box  # Extract coordinates
            # Scale box back to original image size
            x1 = int(x1 * scale_w)
            y1 = int(y1 * scale_h)
            x2 = int(x2 * scale_w)
            y2 = int(y2 * scale_h)
        return boxes

    def draw_bounding_boxes(self, frame, boxes,):
        for box in boxes:
            x1, y1, x2, y2 = box 
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        return frame

    def process_frame(self, frame):
        boxes = self.send_image_for_detection(frame)
        boxes = self.scale_coordinates(frame, boxes)
        bb_frame = self.draw_bounding_boxes(frame, boxes)
        return bb_frame