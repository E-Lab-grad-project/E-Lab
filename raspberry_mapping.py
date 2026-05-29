import cv2
import numpy as np
from picamera2 import Picamera2

# =========================================================
# BOARD CONFIGURATION
# =========================================================

BOARD_WIDTH_CM = 30
BOARD_HEIGHT_CM = 15
CELL_SIZE_CM = 5

# Number of cells
GRID_COLS = BOARD_WIDTH_CM // CELL_SIZE_CM   # 6
GRID_ROWS = BOARD_HEIGHT_CM // CELL_SIZE_CM  # 3

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
# STORAGE
# =========================================================

clicked_point = None
homography_matrix = None

# =========================================================
# MOUSE CALLBACK
# =========================================================

def mouse_callback(event, x, y, flags, param):

    global clicked_point

    if event == cv2.EVENT_LBUTTONDOWN:
        clicked_point = (x, y)

cv2.namedWindow("Grid Mapper")
cv2.setMouseCallback("Grid Mapper", mouse_callback)

# =========================================================
# MAIN LOOP
# =========================================================

while True:

    # =====================================================
    # GET FRAME
    # =====================================================

    frame = picam2.capture_array()

    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

    display = frame.copy()

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # =====================================================
    # EDGE DETECTION
    # =====================================================

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(blur, 50, 150)

    # =====================================================
    # FIND LINES
    # =====================================================

    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 180,
        threshold=100,
        minLineLength=100,
        maxLineGap=10
    )

    vertical_lines = []
    horizontal_lines = []

    if lines is not None:

        for line in lines:

            x1, y1, x2, y2 = line[0]

            dx = x2 - x1
            dy = y2 - y1

            # Vertical line
            if abs(dx) < abs(dy):

                vertical_lines.append((x1, y1, x2, y2))

                cv2.line(
                    display,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

            # Horizontal line
            else:

                horizontal_lines.append((x1, y1, x2, y2))

                cv2.line(
                    display,
                    (x1, y1),
                    (x2, y2),
                    (0, 255, 0),
                    2
                )

    # =====================================================
    # SORT GRID LINES
    # =====================================================

    vertical_lines = sorted(
        vertical_lines,
        key=lambda l: l[0]
    )

    horizontal_lines = sorted(
        horizontal_lines,
        key=lambda l: l[1]
    )

    # =====================================================
    # REMOVE DUPLICATE LINES
    # =====================================================

    def filter_lines(lines, axis=0, threshold=20):

        filtered = []

        previous = None

        for line in lines:

            value = line[axis]

            if previous is None or abs(value - previous) > threshold:

                filtered.append(line)

                previous = value

        return filtered

    vertical_lines = filter_lines(vertical_lines, axis=0)
    horizontal_lines = filter_lines(horizontal_lines, axis=1)

    # =====================================================
    # NEED ENOUGH LINES
    # =====================================================

    if (
        len(vertical_lines) >= GRID_COLS + 1 and
        len(horizontal_lines) >= GRID_ROWS + 1
    ):

        # Use outermost lines
        left = vertical_lines[0]
        right = vertical_lines[-1]

        top = horizontal_lines[0]
        bottom = horizontal_lines[-1]

        # =================================================
        # FIND CORNERS
        # =================================================

        def line_intersection(vline, hline):

            x = vline[0]
            y = hline[1]

            return [x, y]

        top_left = line_intersection(left, top)
        top_right = line_intersection(right, top)
        bottom_right = line_intersection(right, bottom)
        bottom_left = line_intersection(left, bottom)

        image_points = np.float32([
            top_left,
            top_right,
            bottom_right,
            bottom_left
        ])

        # =================================================
        # DRAW CORNERS
        # =================================================

        for point in image_points:

            px, py = point.astype(int)

            cv2.circle(
                display,
                (px, py),
                10,
                (0, 0, 255),
                -1
            )

        # =================================================
        # REAL WORLD POINTS
        # =================================================

        real_points = np.float32([
            [0, 0],
            [BOARD_WIDTH_CM, 0],
            [BOARD_WIDTH_CM, BOARD_HEIGHT_CM],
            [0, BOARD_HEIGHT_CM]
        ])

        # =================================================
        # HOMOGRAPHY
        # =================================================

        homography_matrix = cv2.getPerspectiveTransform(
            image_points,
            real_points
        )

        cv2.putText(
            display,
            "GRID DETECTED",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2
        )

    else:

        cv2.putText(
            display,
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

        # Convert pixel -> real-world cm
        real = cv2.perspectiveTransform(
            pixel,
            homography_matrix
        )

        x_cm = real[0][0][0]
        y_cm = real[0][0][1]

        # Convert to grid cell
        grid_x = int(x_cm // CELL_SIZE_CM)
        grid_y = int(y_cm // CELL_SIZE_CM)

        # Draw clicked point
        cv2.circle(
            display,
            (px, py),
            8,
            (0, 255, 255),
            -1
        )

        text1 = f"CM: ({x_cm:.2f}, {y_cm:.2f})"
        text2 = f"CELL: ({grid_x}, {grid_y})"

        cv2.putText(
            display,
            text1,
            (20, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        cv2.putText(
            display,
            text2,
            (20, 120),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 255),
            2
        )

        print("=" * 40)
        print(f"Pixel : ({px}, {py})")
        print(f"CM    : ({x_cm:.2f}, {y_cm:.2f})")
        print(f"CELL  : ({grid_y}, {grid_x})")

    # =====================================================
    # SHOW
    # =====================================================

    cv2.imshow("Grid Mapper", display)

    key = cv2.waitKey(1)

    if key == ord('q'):
        break

# =========================================================
# CLEANUP
# =========================================================

cv2.destroyAllWindows()
