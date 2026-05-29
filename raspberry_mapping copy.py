import cv2
import numpy as np
from picamera2 import Picamera2

# =========================================================
# CONFIGURATION
# =========================================================

# Number of INNER corners in the checkerboard
# Example:
# If your board has 9x7 squares:
# inner corners = 8x6
CHECKERBOARD = (8, 6)

# Each square size in CM
SQUARE_SIZE_CM = 5

# =========================================================
# PI CAMERA SETUP
# =========================================================

picam2 = Picamera2()

config = picam2.create_preview_configuration(
    main={"size": (1280, 720)}
)

picam2.configure(config)
picam2.start()

# =========================================================
# PREPARE REAL-WORLD POINTS
# =========================================================

objp = np.zeros(
    (CHECKERBOARD[0] * CHECKERBOARD[1], 3),
    np.float32
)

objp[:, :2] = np.mgrid[
    0:CHECKERBOARD[0],
    0:CHECKERBOARD[1]
].T.reshape(-1, 2)

# Multiply by real square size (5 cm)
objp *= SQUARE_SIZE_CM

# =========================================================
# STORAGE
# =========================================================

clicked_point = None
homography_matrix = None
detected_corners = None

# =========================================================
# MOUSE CALLBACK
# =========================================================

def mouse_callback(event, x, y, flags, param):
    global clicked_point

    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_point = (x, y)

cv2.namedWindow("Grid Mapping")
cv2.setMouseCallback("Grid Mapping", mouse_callback)

# =========================================================
# MAIN LOOP
# =========================================================

while True:

    # =====================================================
    # GET FRAME
    # =====================================================

    frame = picam2.capture_array()

    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # =====================================================
    # FIND CHECKERBOARD
    # =====================================================

    found, corners = cv2.findChessboardCorners(
        gray,
        CHECKERBOARD,
        None
    )

    if found:

        # Improve accuracy
        criteria = (
            cv2.TERM_CRITERIA_EPS +
            cv2.TERM_CRITERIA_MAX_ITER,
            30,
            0.001
        )

        corners2 = cv2.cornerSubPix(
            gray,
            corners,
            (11, 11),
            (-1, -1),
            criteria
        )

        detected_corners = corners2

        # Draw corners
        cv2.drawChessboardCorners(
            frame,
            CHECKERBOARD,
            corners2,
            found
        )

        # =================================================
        # HOMOGRAPHY
        # =================================================

        image_points = corners2.reshape(-1, 2)

        real_points = objp[:, :2]

        homography_matrix, _ = cv2.findHomography(
            image_points,
            real_points
        )

        cv2.putText(
            frame,
            "GRID DETECTED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    else:

        cv2.putText(
            frame,
            "GRID NOT DETECTED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2
        )

    # =====================================================
    # CLICK MAPPING
    # =====================================================

    if clicked_point is not None and homography_matrix is not None:

        px, py = clicked_point

        pixel = np.array(
            [[[px, py]]],
            dtype=np.float32
        )

        # Convert pixel -> real world
        real = cv2.perspectiveTransform(
            pixel,
            homography_matrix
        )

        x_cm = real[0][0][0]
        y_cm = real[0][0][1]

        # Convert to grid cell
        grid_x = int(x_cm // SQUARE_SIZE_CM)
        grid_y = int(y_cm // SQUARE_SIZE_CM)

        # Draw clicked point
        cv2.circle(
            frame,
            (px, py),
            8,
            (0, 0, 255),
            -1
        )

        text1 = f"CM: ({x_cm:.2f}, {y_cm:.2f})"
        text2 = f"CELL: ({grid_x}, {grid_y})"

        cv2.putText(
            frame,
            text1,
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2
        )

        cv2.putText(
            frame,
            text2,
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 0),
            2
        )

        print("=" * 40)
        print(f"Pixel : ({px}, {py})")
        print(f"CM    : ({x_cm:.2f}, {y_cm:.2f})")
        print(f"CELL  : ({grid_x}, {grid_y})")

    # =====================================================
    # SHOW
    # =====================================================

    cv2.imshow("Grid Mapping", frame)

    key = cv2.waitKey(1)

    if key == ord('q'):
        break

# =========================================================
# CLEANUP
# =========================================================

cv2.destroyAllWindows()