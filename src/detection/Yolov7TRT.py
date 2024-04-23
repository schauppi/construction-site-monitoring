import ctypes
import os
import shutil
import random
import sys
import threading
import time
import cv2
import numpy as np
import pycuda.autoinit
import pycuda.driver as cuda
import tensorrt as trt
import logging

from src.logging.logging_config import setup_logging
from src.detection.utils.classes import categories as imported_categories

class YoLov7TRT(object):
    """
    A YOLOv7 class that warps TensorRT ops, preprocess and postprocess ops.

    Methods:
        infer: inference an image
        destroy: destroy the context
        get_raw_image: get raw image from image path
        get_raw_image_zeros: get raw image with zeros
        preprocess_image: preprocess image
        xywh2xyxy: convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
        post_process: postprocess the prediction to only return detections for class 0
        bbox_iou: compute the IoU of two bounding boxes
        non_max_suppression: removes detections with lower object confidence score than 'conf_thres' and performs
                             Non-Maximum Suppression to further filter detections
        plot_one_box: plots one bounding box on image img
    """

    def __init__(self, ):
        setup_logging()
        self.logger = logging.getLogger()
        _base_path = os.path.dirname(__file__)
        engine_file_path = os.path.join(_base_path, 'files/yolov7-e6.engine')
        self.engine_file_path_path = os.path.normpath(engine_file_path)
        self.categories = imported_categories
        self.CONF_THRESH = 0.25
        self.IOU_THRESHOLD = 0.45
        self.ctx = cuda.Device(0).make_context()
        stream = cuda.Stream()
        TRT_LOGGER = trt.Logger(trt.Logger.INFO)
        runtime = trt.Runtime(TRT_LOGGER)

        try:
            self.logger.info("Reading engine from file %s", engine_file_path)
            with open(engine_file_path, "rb") as f:
                engine = runtime.deserialize_cuda_engine(f.read())
            context = engine.create_execution_context()

            host_inputs = []
            cuda_inputs = []
            host_outputs = []
            cuda_outputs = []
            bindings = []

            for binding in engine:
                self.logger.info("binding: %s, shape: %s", binding, engine.get_binding_shape(binding))
                size = trt.volume(engine.get_binding_shape(binding)) * engine.max_batch_size
                dtype = trt.nptype(engine.get_binding_dtype(binding))
                host_mem = cuda.pagelocked_empty(size, dtype)
                cuda_mem = cuda.mem_alloc(host_mem.nbytes)
                bindings.append(int(cuda_mem))
                if engine.binding_is_input(binding):
                    self.input_w = engine.get_binding_shape(binding)[-1]
                    self.input_h = engine.get_binding_shape(binding)[-2]
                    host_inputs.append(host_mem)
                    cuda_inputs.append(cuda_mem)
                else:
                    host_outputs.append(host_mem)
                    cuda_outputs.append(cuda_mem)

            self.stream = stream
            self.context = context
            self.engine = engine
            self.host_inputs = host_inputs
            self.cuda_inputs = cuda_inputs
            self.host_outputs = host_outputs
            self.cuda_outputs = cuda_outputs
            self.bindings = bindings
            self.batch_size = engine.max_batch_size
        except Exception as e:
            logging.error(f"An error occurred: {e}")

    def infer(self, image):
        """
        Infer an image

        Args:
            image: np.ndarray, input image

        Returns:
            image_raw: np.ndarray, original image
            inference_time: float, inference time
            num_of_objects: int, number of objects detected
            result_boxes: np.ndarray, finally boxes, a boxes numpy, each row is a box [x1, y1, x2, y2]
        """
        try:
            threading.Thread.__init__(self)
            self.ctx.push()
            stream = self.stream
            context = self.context
            engine = self.engine
            host_inputs = self.host_inputs
            cuda_inputs = self.cuda_inputs
            host_outputs = self.host_outputs
            cuda_outputs = self.cuda_outputs
            bindings = self.bindings
            batch_image_raw = []
            batch_origin_h = []
            batch_origin_w = []
            batch_input_image = np.empty(shape=[1, 3, self.input_h, self.input_w])
            input_image, image_raw, origin_h, origin_w = self.preprocess_image(image)
            batch_image_raw.append(image_raw)
            batch_origin_h.append(origin_h)
            batch_origin_w.append(origin_w)
            np.copyto(batch_input_image, input_image)
            batch_input_image = np.ascontiguousarray(batch_input_image)
            np.copyto(host_inputs[0], batch_input_image.ravel())
            start = time.time()
            cuda.memcpy_htod_async(cuda_inputs[0], host_inputs[0], stream)
            context.execute_async(
                batch_size=self.batch_size, bindings=bindings, stream_handle=stream.handle
            )
            cuda.memcpy_dtoh_async(host_outputs[0], cuda_outputs[0], stream)
            stream.synchronize()
            end = time.time()
            self.ctx.pop()
            output = host_outputs[0]
            result_boxes, result_scores, result_classid = self.post_process(
                output[0:6001], batch_origin_h[0], batch_origin_w[0]
            )

            num_of_objects = len(result_classid)
            return image_raw, end - start, num_of_objects, result_boxes
        except Exception as e:
            logging.error(f"An error occurred: {e}")


    def destroy(self):
        """
        Destroy the context

        Args:
            None

        Returns:
            None
        """
        try:
            self.logger.info("Destroying the context")
            self.ctx.pop()
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    def get_raw_image(self, image_path_batch):
        """
        Get raw image from image path

        Args:
            image_path_batch: list, image path

        Returns:
            image: np.ndarray, image
        """
        try:
            self.logger.info("Reading image from path")
            for img_path in image_path_batch:
                yield cv2.imread(img_path)
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    def get_raw_image_zeros(self, image_path_batch=None):
        """
        Get raw image with zeros

        Args:
            image_path_batch: list, image path

        Returns:
            image: np.ndarray, image
        """
        try:
            self.logger.info("Reading image with zeros")
            for _ in range(self.batch_size):
                yield np.zeros([self.input_h, self.input_w, 3], dtype=np.uint8)
        except:
            self.logger.error(f"An error occurred: {e}")

    def preprocess_image(self, raw_bgr_image):
        """
        Preprocess image

        Args:
            raw_bgr_image: np.ndarray, raw image

        Returns:
            image: np.ndarray, image
            image_raw: np.ndarray, original image
            h: int, height
            w: int, width
        """
        try:
            self.logger.info("Preprocessing image")
            image_raw = raw_bgr_image
            h, w, c = image_raw.shape
            image = cv2.cvtColor(image_raw, cv2.COLOR_BGR2RGB)
            r_w = self.input_w / w
            r_h = self.input_h / h
            if r_h > r_w:
                tw = self.input_w
                th = int(r_w * h)
                tx1 = tx2 = 0
                ty1 = int((self.input_h - th) / 2)
                ty2 = self.input_h - th - ty1
            else:
                tw = int(r_h * w)
                th = self.input_h
                tx1 = int((self.input_w - tw) / 2)
                tx2 = self.input_w - tw - tx1
                ty1 = ty2 = 0
            image = cv2.resize(image, (tw, th))
            image = cv2.copyMakeBorder(
                image, ty1, ty2, tx1, tx2, cv2.BORDER_CONSTANT, None, (128, 128, 128)
            )
            image = image.astype(np.float32)
            image /= 255.0
            image = np.transpose(image, [2, 0, 1])
            image = np.expand_dims(image, axis=0)
            image = np.ascontiguousarray(image)
            return image, image_raw, h, w
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    def xywh2xyxy(self, origin_h, origin_w, x):
        """
        Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right

        Args:
            origin_h: int, height
            origin_w: int, width
            x: np.ndarray, boxes

        Returns:
            y: np.ndarray, boxes
        """
        try:
            self.logger.info("Converting nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2]")
            y = np.zeros_like(x)
            r_w = self.input_w / origin_w
            r_h = self.input_h / origin_h
            if r_h > r_w:
                y[:, 0] = x[:, 0] - x[:, 2] / 2
                y[:, 2] = x[:, 0] + x[:, 2] / 2
                y[:, 1] = x[:, 1] - x[:, 3] / 2 - (self.input_h - r_w * origin_h) / 2
                y[:, 3] = x[:, 1] + x[:, 3] / 2 - (self.input_h - r_w * origin_h) / 2
                y /= r_w
            else:
                y[:, 0] = x[:, 0] - x[:, 2] / 2 - (self.input_w - r_h * origin_w) / 2
                y[:, 2] = x[:, 0] + x[:, 2] / 2 - (self.input_w - r_h * origin_w) / 2
                y[:, 1] = x[:, 1] - x[:, 3] / 2
                y[:, 3] = x[:, 1] + x[:, 3] / 2
                y /= r_h

            return y
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    def post_process(self, output, origin_h, origin_w):
        """
        Postprocess the prediction to only return detections for class 0

        Args:
            output: np.ndarray, output
            origin_h: int, height
            origin_w: int, width

        Returns:
            result_boxes: np.ndarray, finally boxes, a boxes numpy, each row is a box [x1, y1, x2, y2]
            result_scores: np.ndarray, finally scores
            result_classid: np.ndarray, finally classid
        """
        try:
            self.logger.info("Postprocessing the prediction")
            num = int(output[0])
            pred = np.reshape(output[1:], (-1, 6))[:num, :]
            class_0_pred = pred[pred[:, 5] == 0]
            if class_0_pred.shape[0] > 0:
                boxes = self.non_max_suppression(
                    class_0_pred, origin_h, origin_w, conf_thres=self.CONF_THRESH, nms_thres=self.IOU_THRESHOLD
                )
            else:
                boxes = np.array([])  

            result_boxes = boxes[:, :4] if len(boxes) else np.array([])
            result_scores = boxes[:, 4] if len(boxes) else np.array([])
            result_classid = boxes[:, 5] if len(boxes) else np.array([])
            return result_boxes, result_scores, result_classid
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    def bbox_iou(self, box1, box2, x1y1x2y2=True):
        """
        Compute the IoU of two bounding boxes

        Args:
            box1: np.ndarray, box1
            box2: np.ndarray, box2
            x1y1x2y2: bool, whether the box is in x1y1x2y2 format

        Returns:
            iou: np.ndarray, iou
        """
        try:
            self.logger.info("Computing the IoU of two bounding boxes")
            if not x1y1x2y2:
                b1_x1, b1_x2 = box1[:, 0] - box1[:, 2] / 2, box1[:, 0] + box1[:, 2] / 2
                b1_y1, b1_y2 = box1[:, 1] - box1[:, 3] / 2, box1[:, 1] + box1[:, 3] / 2
                b2_x1, b2_x2 = box2[:, 0] - box2[:, 2] / 2, box2[:, 0] + box2[:, 2] / 2
                b2_y1, b2_y2 = box2[:, 1] - box2[:, 3] / 2, box2[:, 1] + box2[:, 3] / 2
            else:
                b1_x1, b1_y1, b1_x2, b1_y2 = box1[:, 0], box1[:, 1], box1[:, 2], box1[:, 3]
                b2_x1, b2_y1, b2_x2, b2_y2 = box2[:, 0], box2[:, 1], box2[:, 2], box2[:, 3]

            inter_rect_x1 = np.maximum(b1_x1, b2_x1)
            inter_rect_y1 = np.maximum(b1_y1, b2_y1)
            inter_rect_x2 = np.minimum(b1_x2, b2_x2)
            inter_rect_y2 = np.minimum(b1_y2, b2_y2)

            inter_area = np.clip(inter_rect_x2 - inter_rect_x1 + 1, 0, None) * np.clip(
                inter_rect_y2 - inter_rect_y1 + 1, 0, None
            )
            b1_area = (b1_x2 - b1_x1 + 1) * (b1_y2 - b1_y1 + 1)
            b2_area = (b2_x2 - b2_x1 + 1) * (b2_y2 - b2_y1 + 1)

            iou = inter_area / (b1_area + b2_area - inter_area + 1e-16)

            return iou
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")

    def non_max_suppression(
        self, prediction, origin_h, origin_w, conf_thres=0.5, nms_thres=0.4
    ):
        """
        Removes detections with lower object confidence score than 'conf_thres' and performs Non-Maximum Suppression to further filter detections

        Args:
            prediction: np.ndarray, prediction
            origin_h: int, height
            origin_w: int, width
            conf_thres: float, confidence threshold
            nms_thres: float, nms threshold

        Returns:
            boxes: np.ndarray, boxes
        """
        try:
            self.logger.info("Removing detections with lower object confidence score than 'conf_thres' and performing Non-Maximum Suppression")
            boxes = prediction[prediction[:, 4] >= conf_thres]
            boxes[:, :4] = self.xywh2xyxy(origin_h, origin_w, boxes[:, :4])
            boxes[:, 0] = np.clip(boxes[:, 0], 0, origin_w - 1)
            boxes[:, 2] = np.clip(boxes[:, 2], 0, origin_w - 1)
            boxes[:, 1] = np.clip(boxes[:, 1], 0, origin_h - 1)
            boxes[:, 3] = np.clip(boxes[:, 3], 0, origin_h - 1)
            confs = boxes[:, 4]
            boxes = boxes[np.argsort(-confs)]
            keep_boxes = []
            while boxes.shape[0]:
                large_overlap = (
                    self.bbox_iou(np.expand_dims(boxes[0, :4], 0), boxes[:, :4]) > nms_thres
                )
                label_match = boxes[0, -1] == boxes[:, -1]
                invalid = large_overlap & label_match
                keep_boxes += [boxes[0]]
                boxes = boxes[~invalid]
            boxes = np.stack(keep_boxes, 0) if len(keep_boxes) else np.array([])
            return boxes
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
    
    def plot_one_box(self, x, img, color=None, label=None, line_thickness=None):
        """
        Plots one bounding box on image img

        Args:
            x: np.ndarray, box
            img: np.ndarray, image
            color: list, color
            label: str, label
            line_thickness: int, line thickness

        Returns:
            None
        """
        try:
            self.logger.info("Plotting one bounding box on image img")
            tl = (
                line_thickness or round(0.002 * (img.shape[0] + img.shape[1]) / 2) + 1
            )  
            color = color or [random.randint(0, 255) for _ in range(3)]
            c1, c2 = (int(x[0]), int(x[1])), (int(x[2]), int(x[3]))
            cv2.rectangle(img, c1, c2, color, thickness=tl, lineType=cv2.LINE_AA)
            if label:
                tf = max(tl - 1, 1)  
                t_size = cv2.getTextSize(label, 0, fontScale=tl / 3, thickness=tf)[0]
                c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
                cv2.rectangle(img, c1, c2, color, -1, cv2.LINE_AA)  
                cv2.putText(
                    img,
                    label,
                    (c1[0], c1[1] - 2),
                    0,
                    tl / 3,
                    [225, 255, 255],
                    thickness=tf,
                    lineType=cv2.LINE_AA,
                )
        except Exception as e:
            self.logger.error(f"An error occurred: {e}")
