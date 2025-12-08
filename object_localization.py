from ultralytics import YOLO    
import cv2    
import numpy as np   
   
model = YOLO('yolov8n.pt')   
   
target_class = 'cup'   
   
# Tracking variables   
prev_center = None   
alpha = 0.65   # smoothing factor   
   
cap = cv2.VideoCapture(0)   
if not cap.isOpened():   
    print("Error: Could not open video.")   
    exit()   
   
class_names = model.names   
   
while True:   
    ret, frame = cap.read()   
    if not ret:   
        print("Error: Could not read frame.")   
        break   
   
    results = model(frame, imgsz=640, verbose=False)   
    frame_h, frame_w = frame.shape[:2]   
   
    best_target = None  
    best_area = 0   
   
    # -------- pick best detection --------   
    for box in results[0].boxes:   
        cls_id = int(box.cls[0])   
        label = class_names[cls_id]   
   
        if label != target_class:   
            continue   
   
        x1, y1, x2, y2 = map(int, box.xyxy[0])   
        area = (x2 - x1) * (y2 - y1)   
   
        if area > best_area:   
            best_area = area   
            best_target = (x1, y1, x2, y2)   
   
    if best_target:   
        x1, y1, x2, y2 = best_target   
        w = x2 - x1   
        h = y2 - y1   
   
        # -------- raw center --------   
        raw_cx = x1 + w / 2   
        # raw_cy = y1 + h / 2        # ❌ Y axis disabled   
   
        # ----- smoothing for X only -----   
        cx = raw_cx   
        if prev_center is None:   
            prev_center = (cx,)      # store only X   
        else:   
            cx = alpha * prev_center[0] + (1 - alpha) * cx   
            prev_center = (cx,)   
   
        # -------- normalized X only --------   
        cx_norm = cx / frame_w   
        # cy_norm = cy / frame_h       # ❌ disabled   
   
        # -------- print X only --------  
        print("\n=== CUP DETECTED ===")   
        print(f"Raw X: {raw_cx:.2f}")   
        print(f"Normalized X: {cx_norm:.3f}")   
        print(f"Box W: {w} px   H: {h} px")   
   
        # -------- draw box --------   
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0,255,0), 2)   
        cv2.circle(frame, (int(cx), int(y1 + h/2)), 6, (0,0,255), -1)  # marker centered vertically   
   
        # -------- show RAW X only --------   
        display_text = f"X:{raw_cx:.1f}"   
        cv2.putText(frame, display_text,    
                    (x1, y1 - 10),    
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)   
   
    cv2.imshow("YOLO Tracking X Only", frame)   
   
    if cv2.waitKey(1) & 0xFF == ord('q'):   
        break   
   
cap.release()   
cv2.destroyAllWindows()
