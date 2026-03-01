from ultralytics import YOLO
import cv2
class YoloDetector:
    def __init__(self, model_path: str, target_class="cup",imgsz=320):
        self.model = YOLO(model_path)
        self.class_names = self.model.names
        self.target_class = target_class
        self.imgsz = imgsz
    
    def detect(self, frame):
        results = self.model(frame, imgsz=self.imgsz, conf=0.4, verbose=False)
        return results