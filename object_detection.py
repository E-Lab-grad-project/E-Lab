from ultralytics import YOLO 
import cv2 

model = YOLO('yolov8n.pt')

'''
the target class will be extracted from user input using the NLP model

eg. "Move the cup to the left" -> 
{
 object to find: "cup"
 action: "move left
}

response -> 

{
 current_position: (x, y, z),
 target_position: (x, y, z)
 commands: ["grep" ,"move left", "down", "forward",]
}

'''
target_class = 'cup'  

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

    results = model.predict(frame, imgsz=640, verbose=False)

    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        label = class_names[cls_id]

        if label != target_class:
            continue

        # لو الكلاس هو الهدف → ارسم
        x1, y1, x2, y2 = box.xyxy[0]
        cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
        cv2.putText(frame, label, (int(x1), int(y1) - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (36, 255, 12), 2)

    cv2.imshow("Detections", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
