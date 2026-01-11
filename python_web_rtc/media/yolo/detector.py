from ultralytics import YOLO

class YoloDetector:
    def __init__(self, model_path: str, target_class="person"):
        self.model = YOLO(model_path)
        self.class_names = self.model.names
        self.target_class = target_class
    
    def detect(self, frame):
        results = self.model(frame, imgsz=320, conf=0.4, verbose = False)
        return results
