from src.reolink.utils.StreamingHandler import StreamingHandler
import multiprocessing

queue = multiprocessing.Queue()

streamer = StreamingHandler(cams=[1, 2], queue=queue)

streamer.start_streaming()


frames = streamer.get_current_frames()
print(f"frame1")
print(f"frame2")
print("--------")

# Join the streaming processes
streamer.stop_streaming()