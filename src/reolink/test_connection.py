import os
import datetime
import cv2
import time
from src.reolink.utils.StreamingHandler import StreamingHandler

class CameraFrameSaver:
    def __init__(self, cams, save_interval=20):
        self.streamer = StreamingHandler(cams=cams)
        self.save_path = "/media/david/DAVID"
        self.save_interval = save_interval

    def start_saving(self):
        self.streamer.start_streaming()
        last_save_time = None 
        try:
            while True:
                current_time = time.time()
                if last_save_time is None or (current_time - last_save_time) >= self.save_interval:
                    frames = self.streamer.get_current_frames()
                    if len(frames) == len(self.streamer.cams):
                        formatted_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        for cam, frame in frames.items():
                            self.save_frame(cam, frame, formatted_time)
                        last_save_time = current_time 
                time.sleep(0.1) 
        except KeyboardInterrupt:
            print("Stopping the streaming...")
            self.streamer.stop_streaming()
        finally:
            print("Streaming stopped.")

    def save_frame(self, cam, frame, formatted_time):
        cam_dir = os.path.join(self.save_path, f"cam_{cam}")
        if not os.path.exists(cam_dir):
            os.makedirs(cam_dir)
        filename = os.path.join(cam_dir, f"{formatted_time}.jpg")
        cv2.imwrite(filename, frame)
        print(f"Frame saved for camera {cam} at {formatted_time}.")


cams = [1, 2]
saver = CameraFrameSaver(cams)
saver.start_saving()