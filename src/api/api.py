from src.reolink.CameraController import CameraController

from flask import Flask, jsonify, request
app = Flask(__name__)

camera_controller = CameraController(cams=[1])

@app.route('/start', methods=['POST'])
def start_capture():
    camera_controller.start_capture()
    return jsonify({"status": "Started capturing images."})

@app.route('/stop', methods=['POST'])
def stop_capture():
    camera_controller.stop_capture()
    return jsonify({"status": "Stopped capturing images."})

@app.route('/status', methods=['GET'])
def status():
    current_status = "Capturing" if camera_controller.is_capturing() else "Not Capturing"
    return jsonify({"status": current_status})

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

if __name__ == '__main__':
    app.run(debug=True)
