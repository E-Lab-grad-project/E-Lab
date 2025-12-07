import cv2
import numpy as np
from picamera2 import Picamera2
import time

# Initialize camera
picam2 = Picamera2()

# Configure preview
preview_config = picam2.create_preview_configuration(
    main={"size": (640, 480)},
    controls={"AwbEnable": True, "AeEnable": True}
)
picam2.configure(preview_config)

# Start camera
picam2.start()

# Warm up
time.sleep(2)

print("Camera started. Press 'q' to quit.")

while True:
    # Capture frame
    frame = picam2.capture_array()
    
    # Convert from RGB to BGR for OpenCV
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # Display
    cv2.imshow("Pi Camera", frame_bgr)
    
    # Your color detection code here
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    
    # Example: detect red
    lower_red = np.array([0, 100, 100])
    upper_red = np.array([10, 255, 255])
    mask = cv2.inRange(hsv, lower_red, upper_red)
    
    # Show mask
    cv2.imshow("Mask", mask)
    
    # Check for quit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Cleanup
picam2.stop()
cv2.destroyAllWindows()