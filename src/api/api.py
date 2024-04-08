import logging
from flask import Flask, jsonify, request
from multiprocessing import Process

from src.reolink.CameraController import CameraController
from src.telegram.TelegramBot import Bot
from src.logging.logging_config import setup_logging
from src.api.utils.get_latest_image import get_latest_image
from src.api.utils.get_disk_space import get_disk_space

setup_logging()
logger = logging.getLogger()

app = Flask(__name__)

camera_controller = CameraController(cams=[1])

bot = Bot()

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
            latest_image_path = get_latest_image(save_path=str(save_path), cam="/cam_0")
            return jsonify({"image_path": latest_image_path})
        else:
            return jsonify({"error": "Save path is not set"}), 400
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