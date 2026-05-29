import cv2
import numpy as np

# =====================================================
# BOARD CONFIGURATION
# =====================================================

BOARD_WIDTH_CM = 100
BOARD_HEIGHT_CM = 200
CELL_SIZE_CM = 5

# =====================================================
# CAMERA SETUP
# =====================================================
url = 'http://192.168.1.111:8080/video'

cap = cv2.VideoCapture(url)

# Optional resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# =====================================================
# MANUALLY MEASURE THESE 4 POINTS FROM CAMERA IMAGE
# ORDER:
# top-left
# top-right
# bottom-right
# bottom-left
# =====================================================

image_points = np.float32([
    [180, 95],    # top-left
    [1080, 100],  # top-right
    [1100, 620],  # bottom-right
    [160, 630]    # bottom-left
])

# =====================================================
# REAL WORLD COORDINATES (CM)
# =====================================================

real_points = np.float32([
    [0, 0],
    [BOARD_WIDTH_CM, 0],
    [BOARD_WIDTH_CM, BOARD_HEIGHT_CM],
    [0, BOARD_HEIGHT_CM]
])

# =====================================================
# COMPUTE PERSPECTIVE MATRIX
# =====================================================

matrix = cv2.getPerspectiveTransform(image_points, real_points)

# =====================================================
# MOUSE CALLBACK
# =====================================================

clicked_point = None

def mouse_callback(event, x, y, flags, param):
    global clicked_point

    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_point = (x, y)

cv2.namedWindow("Board Mapper")
cv2.setMouseCallback("Board Mapper", mouse_callback)

# =====================================================
# MAIN LOOP
# =====================================================

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # Draw board corners
    for point in image_points:
        px, py = point.astype(int)
        cv2.circle(frame, (px, py), 8, (0, 255, 0), -1)

    # If user clicked
    if clicked_point is not None:

        px, py = clicked_point

        # Convert pixel -> real world
        pixel = np.array([[[px, py]]], dtype=np.float32)

        real = cv2.perspectiveTransform(pixel, matrix)

        x_cm = real[0][0][0]
        y_cm = real[0][0][1]

        # Convert cm -> grid cell
        grid_x = int(x_cm // CELL_SIZE_CM)
        grid_y = int(y_cm // CELL_SIZE_CM)

        text = f"CM: ({x_cm:.1f}, {y_cm:.1f})  CELL: ({grid_x}, {grid_y})"

        cv2.circle(frame, (px, py), 6, (0, 0, 255), -1)

        cv2.putText(
            frame,
            text,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        print(text)

    cv2.imshow("Board Mapper", frame)

    key = cv2.waitKey(1)

    if key == 27:
        break

cap.release()
cv2.destroyAllWindows()