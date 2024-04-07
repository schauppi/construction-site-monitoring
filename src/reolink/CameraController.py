from src.reolink.utils.CredentialHandler import CredentialHandler

import cv2
import threading
import time
import os

class CameraController:
    def __init__(self, cams: list, initial_interval=300):
        self.capture_images = False
        self.save_interval = initial_interval
        self.save_path = "/media/david/DAVID"
        self.urls = [CredentialHandler(cam).url for cam in cams]
        self.state_lock = threading.Lock()
        self.thread = threading.Thread(target=self.camera_capture, daemon=True)
        self.thread.start()

    def camera_capture(self):
        while True:
            with self.state_lock:
                if self.capture_images:
                    for camera_index, url in enumerate(self.urls):
                        cap = cv2.VideoCapture(url)
                        ret, frame = cap.read()
                        if ret:
                            self.save_image(camera_index, frame)
                        cap.release()
                    time.sleep(self.save_interval)  
            time.sleep(1)

    def save_image(self, camera_index, frame):
        camera_path = os.path.join(self.save_path, f'cam_{camera_index}')
        if not os.path.exists(camera_path):
            os.makedirs(camera_path)

        timestamp = int(time.time())
        filename = f"{timestamp}.jpg"
        file_path = os.path.join(camera_path, filename)
        cv2.imwrite(file_path, frame)

    def start_capture(self):
        with self.state_lock:
            self.capture_images = True

    def stop_capture(self):
        with self.state_lock:
            self.capture_images = False

    def is_capturing(self):
        return self.capture_images

    def set_save_interval(self, interval):
        with self.state_lock:
            self.save_interval = interval

