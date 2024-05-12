# Project Overview

This project is a robust surveillance system utilizing two Reolink cameras connected to an NVIDIA Jetson Nano. It features a Flask API and storage on an external NAS to save images. System control and monitoring are achieved through a Telegram bot, and an additional Jetson Xavier runs a custom-trained object detection model using a Flask Detection API with TensorRT engine for YOLO models.

# Architecture
![Architecture](images/architecture.svg)

# System Components

1. Hardware
* NVIDIA Jetson Nano
* NVIDIA Jetson Xavier
* Two Reolink cameras
* External NAS for storage

2. Software
* Backend + Flask API for camera control and image storage
* Telegram Bot for remote system control
* Backend + Flask Detection API running on Jetson Xavier for person detection using YOLO

# Installation and Setup

Wire the hardware components according to the architecture diagram. The software components are divided into two parts: the Jetson Nano and the Jetson Xavier.

## For Jetson Nano and Xavier

1. **Environment Setup**
* Ensure you have Python 3.8 or higher installed
* Create an virtual environment and activate it
```bash
python3 -m venv venv
source venv/bin/activate
```
* Install the required packages
* {} is either nano or xavier
```bash
pip install -r requirements_{}.txt
```

2. **Configuration**
* Create a new Telegram bot and get the API token
* Change the .env example into .env and fill in the required information
    * TELEGRAM: Telegram API token
    * TELEGRAM_CHAT_ID: Chat ID for the bot
* Setup the Reolink cameras with username, password and static ip
* Change the reolink_credentials_example.json into reolink_credentials.json and fill in the required information
    * Username, Password, IP-address

3. **Running the system**
* Run the Flask API
```bash
python -m src.api.api
```

## Jetson Xavier

2. **Configuration**
* Train a custom Yolov7 model or use an existing one
* Clone the following repos inside the detecion folder
    * TensorRTX: https://github.com/wang-xinyu/tensorrtx
    * Yolov7: https://github.com/WongKinYiu/yolov7
* Convert the trained model using the TensorRTX repo and save it in an directory called 'files'

3. **Running the system**
* Run the Flask Detection API
```bash
python -m src.detection.detection_api
```

# Usage

* **Camera Control:** Use Telegram commands to start/stop capturing, arm/disarm the cameras, and set the image capture interval.
* **Monitoring:** Check system status, disk space, and get latest images through the Telegram bot.
* **Object Detection:** Send images to the detection API running on Xavier to detect persons in real-time.

# API Endpoints

* **Flask API on Jetson Nano**
    * **/start:** Start image capturing.
    * **/stop:** Stop image capturing.
    * **/status:** Get system status.
    * **/set_interval:** Set image capture interval.
    * **/get_image:** Fetch latest captured images.
    * **/disk_space:** Check disk space usage.
    * **/arm:** Arm the system.
    * **/disarm:** Disarm the system.
    * **/get_current_images:** Get the latest images.

* **Object Detection API on Jetson Xavier**
    * **/detect:** Endpoint to upload images for object detection.