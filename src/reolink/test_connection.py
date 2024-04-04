from src.reolink.utils.StreamingHandler import StreamingHandler
import os
import datetime
import cv2
import time

save_path = "/media/david/DAVID"

streamer = StreamingHandler(cams=[1, 2])

streamer.start_streaming()

save_interval = 20  

try:
    last_save_time = None 
    while True:
        current_time = time.time()
        if last_save_time is None or (current_time - last_save_time) >= save_interval:
            frames = streamer.get_current_frames()
            if len(frames) == len(streamer.cams):
                formatted_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                for cam, frame in frames.items():
                    cam_dir = os.path.join(save_path, f"cam_{cam}")
                    if not os.path.exists(cam_dir):
                        os.makedirs(cam_dir)
                    filename = os.path.join(cam_dir, f"{formatted_time}.jpg")
                    cv2.imwrite(filename, frame)
                    print(f"Frame saved for camera {cam} at {formatted_time}.")
                last_save_time = current_time 
        time.sleep(0.1) 
except KeyboardInterrupt:
    print("Stopping the streaming...")
    streamer.stop_streaming()
finally:
    print("Streaming stopped.")
