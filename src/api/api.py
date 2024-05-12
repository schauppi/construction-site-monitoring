import logging
from flask import Flask, jsonify, request
from multiprocessing import Process

from src.reolink.CameraController import CameraController
from src.telegram.TelegramBot import Bot
from src.logging.logging_config import setup_logging
from src.api.utils.get_latest_image import get_latest_image
from src.api.utils.get_disk_space import get_disk_space
import tempfile
import cv2
from datetime import datetime, timedelta
import os
import imageio.v2 as imageio

setup_logging()
logger = logging.getLogger()

app = Flask(__name__)

bot = Bot()
camera_controller = CameraController(cams=[1,2], bot=bot)

@app.before_request
def initialize_capture():
    if not camera_controller.is_capturing():
        try:
            camera_controller.start_capture()
            logger.info("Started capturing images automatically.")
        except Exception as e:
            logger.error(f"Failed to start image capture automatically: {str(e)}")


@app.route('/start', methods=['POST'])
def start_capture():
    try:
        camera_controller.start_capture()
        return jsonify({"status": "Started capturing images."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stop', methods=['POST'])
def stop_capture():
    try:
        camera_controller.stop_capture()
        return jsonify({"status": "Stopped capturing images."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status', methods=['GET'])
def status():
    try:
        current_status = "Capturing" if camera_controller.is_capturing() else "Not Capturing"
        current_interval = camera_controller.save_interval
        return jsonify({"status": current_status, "save_interval": current_interval})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/set_interval', methods=['POST'])
def set_interval():
    try:
        new_interval = request.json.get('interval')
        if not isinstance(new_interval, int) or new_interval < 1:
            raise ValueError("Interval must be a positive integer")
        camera_controller.set_save_interval(new_interval)
        return jsonify({"status": f"Save interval updated to {new_interval} seconds."})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/get_image', methods=['GET'])
def get_image():
    try:
        save_path = camera_controller.save_path
        if save_path is not None:
            latest_image_path_0 = get_latest_image(save_path=str(save_path), cam="/cam_0")
            latest_image_path_1 = get_latest_image(save_path=str(save_path), cam="/cam_1")
            return jsonify({"image_path_0": latest_image_path_0, "image_path_1": latest_image_path_1})
        else:
            return jsonify({"error": "Save path is not set"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/get_current_images', methods=['GET'])
def get_all_images():
    try:
        frames = camera_controller.get_current_frames()
        image_paths = {}
        for camera_index, frame in frames.items():
            if frame is not None:
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                temp_file_path = temp_file.name
                cv2.imwrite(temp_file_path, frame)
                image_paths[camera_index] = temp_file_path
        return jsonify({"image_paths": image_paths})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/disk_space', methods=['GET'])
def disk_space():
    try:
        save_path = camera_controller.save_path
        if save_path is not None:
            total, used, free = get_disk_space(path=str(save_path))
            return jsonify({"total": total, "used": used, "free": free})
        else:
            return jsonify({"error": "Save path is not set"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/arm', methods=['POST'])
def arm_cameras():
    try:
        camera_controller.arm_system()
        return jsonify({"status": "System armed."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/disarm', methods=['POST'])
def disarm_cameras():
    try:
        camera_controller.disarm_system()
        return jsonify({"status": "System disarmed."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def run_bot():

    logger.info("Running bot")
    try:
        bot.run()
    except Exception as e:
        logger.error(f"An error occurred while running the bot: {str(e)}")

def run_flask_app():

    try:
        logger.info("Running Flask app")
        app.run(debug=True)
    except Exception as e:
        logger.error(f"An error occurred while running the Flask app: {str(e)}")


if __name__ == '__main__':

    try:
        logger.info("Starting application")
        bot_process = Process(target=run_bot)
        bot_process.start()
        run_flask_app()
    except Exception as e:
        logger.error(f"An error occurred while starting the application: {str(e)}")