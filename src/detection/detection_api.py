import logging
from flask import Flask, jsonify, request
import os
import ctypes
from werkzeug.utils import secure_filename
import tempfile
import cv2

from src.detection.Yolov7TRT import YoLov7TRT

from src.logging.logging_config import setup_logging


setup_logging()
logger = logging.getLogger()

app = Flask(__name__)

_base_path = os.path.dirname(__file__)
lib_path = os.path.join(_base_path, 'files/libmyplugins.so')
lib_path = os.path.normpath(lib_path)

ctypes.CDLL(lib_path)

yolov7 = YoLov7TRT()

def with_cuda_context(func):
    def wrapper(*args, **kwargs):
        yolov7.ctx.push()
        try:
            return func(*args, **kwargs)
        finally:
            yolov7.ctx.pop()
    return wrapper

@app.route('/detect', methods=['POST'])
@with_cuda_context
def detect():
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No image selected"}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            temp_path = os.path.join(tempfile.gettempdir(), filename)
            file.save(temp_path)

            image = cv2.imread(temp_path)
            if image is None:
                return jsonify({"error": "Invalid image format"}), 422

            image = cv2.resize(image, (640, 640)) 

            _, inference_time, num_objects, result_boxes = yolov7.infer(image)

            return jsonify({
                "num_objects": num_objects,
                "inference_time": inference_time,
                "result_boxes": result_boxes.tolist() if result_boxes.size else []
            })
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return jsonify({"error": "An error occurred while processing the image"}), 500

def allowed_file(filename):
    try:
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return False

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)