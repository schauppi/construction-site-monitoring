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

#pip freeze requirements.