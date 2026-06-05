import cv2
import numpy as np
import sys
import pickle
import os
import time  # Added for Brio initialization delay

# ==========================================
# CONFIGURATION
# ==========================================
ROWS = 9
COLS = 16
CELL_SIZE = 40  # Resolution scaler: pixels per cell in the warped image
# ==========================================

points = []

def empty(a):
    pass

def click_event(event, x, y, flags, params):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        if len(points) < 4:
            points.append([x, y])
            print(f"Point selected: ({x}, {y})")

def setup_source():
    """Helper function to cleanly request and initialize a camera or image."""
    camera_index = 1
    source_choice = input("1. Live Camera\n2. Test Image\nEnter 1 or 2: ")
    mode = 'camera' if source_choice == '1' else 'image'
    
    if mode == 'camera':
        # 1. Initialize with DirectShow
        source = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        
        # 2. BRIO FIX: Force MJPG compression to prevent USB bus freezing
        source.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        
        # 3. BRIO FIX: Force a high resolution for accurate calibration
        source.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        source.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        # 4. Give the Brio's hardware a second to apply settings
        time.sleep(1)
        
        if not source.isOpened():
            print("Error: Could not open the Brio camera stream.")
            sys.exit()
            
        # Read a few frames to let the webcam sensor adjust to lighting
        for _ in range(5): 
            source.read()
    else:
        source = input("Enter image path/filename: ")
        
    return mode, source

def calibrate_grid_corners(mode, source):
    global points
    cv2.namedWindow("Grid Calibration")
    cv2.setMouseCallback("Grid Calibration", click_event)
    
    print("\n--- PHASE 1: GRID CALIBRATION ---")
    print("Click the 4 corners of the grid in a clockwise order.")
    print("Press 'c' to confirm.")

    while True:
        if mode == 'camera':
            ret, frame = source.read()
            if not ret: break
        else:
            frame = cv2.imread(source)
            if frame is None:
                print("Error: Could not load image.")
                sys.exit()
                
        display_frame = frame.copy()
        for pt in points:
            cv2.circle(display_frame, tuple(pt), 5, (0, 0, 255), -1)
            
        if len(points) == 4:
            pts = np.array(points, np.int32).reshape((-1, 1, 2))
            cv2.polylines(display_frame, [pts], True, (0, 255, 0), 2)

        cv2.imshow("Grid Calibration", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('c') and len(points) == 4:
            break
        elif key == ord('r'):
            points = []
            
    cv2.destroyWindow("Grid Calibration")
    return points, frame

def calibrate_grid_lines(warped_img, rows, cols):
    print("\n--- PHASE 1.5: GRID LINE CALIBRATION ---")
    print("Adjust the sliders until the grid lines are solid WHITE and background is BLACK.")
    print("Red dots will appear where the system detects the true center of each cell.")
    print("Press 'n' when the red dots are perfectly centered in your drawn squares.")

    cv2.namedWindow("Line Calibration")
    cv2.resizeWindow("Line Calibration", 640, 150)
    
    cv2.createTrackbar("Thickness", "Line Calibration", 10, 50, empty)
    cv2.createTrackbar("Noise Filter", "Line Calibration", 35, 50, empty)

    gray = cv2.cvtColor(warped_img, cv2.COLOR_BGR2GRAY)
    h, w = warped_img.shape[:2]
    
    expected_cell_w = w / float(cols)
    expected_cell_h = h / float(rows)

    while True:
        block_pos = cv2.getTrackbarPos("Thickness", "Line Calibration")
        c_pos = cv2.getTrackbarPos("Noise Filter", "Line Calibration")

        block_size = (block_pos * 2) + 3 
        c_val = c_pos - 25

        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block_size, c_val)

        x_proj = np.sum(thresh, axis=0)
        y_proj = np.sum(thresh, axis=1)

        x_lines, y_lines = [], []
        
        for i in range(cols + 1):
            exp_x = int(i * expected_cell_w)
            margin = int(expected_cell_w * 0.3)
            start_x, end_x = max(0, exp_x - margin), min(w, exp_x + margin)
            
            if start_x >= end_x: x_lines.append(exp_x)
            else: x_lines.append(start_x + np.argmax(x_proj[start_x:end_x]))
                
        for i in range(rows + 1):
            exp_y = int(i * expected_cell_h)
            margin = int(expected_cell_h * 0.3)
            start_y, end_y = max(0, exp_y - margin), min(h, exp_y + margin)
            
            if start_y >= end_y: y_lines.append(exp_y)
            else: y_lines.append(start_y + np.argmax(y_proj[start_y:end_y]))

        centers = []
        display_img = warped_img.copy()
        
        for row in range(rows):
            row_centers = []
            for col in range(cols):
                cx = (x_lines[col] + x_lines[col+1]) // 2
                cy = (y_lines[row] + y_lines[row+1]) // 2
                row_centers.append((cx, cy))
                cv2.circle(display_img, (cx, cy), 4, (0, 0, 255), -1) 
            centers.append(row_centers)

        cv2.imshow("Line Calibration - Mask", thresh)
        cv2.imshow("Line Calibration - Centers", display_img)
        
        if cv2.waitKey(1) & 0xFF == ord('n'):
            cv2.destroyWindow("Line Calibration")
            cv2.destroyWindow("Line Calibration - Mask")
            cv2.destroyWindow("Line Calibration - Centers")
            return centers

def calibrate_color(image, color_name):
    print(f"\n--- PHASE 2: CALIBRATING {color_name.upper()} ---")
    print("Adjust sliders until ONLY the target color is WHITE. Press 'n' to save.")
    
    cv2.namedWindow("Trackbars")
    cv2.resizeWindow("Trackbars", 640, 240)
    
    cv2.createTrackbar("Hue Min", "Trackbars", 0, 179, empty)
    cv2.createTrackbar("Hue Max", "Trackbars", 179, 179, empty)
    cv2.createTrackbar("Sat Min", "Trackbars", 0, 255, empty)
    cv2.createTrackbar("Sat Max", "Trackbars", 255, 255, empty)
    cv2.createTrackbar("Val Min", "Trackbars", 0, 255, empty)
    cv2.createTrackbar("Val Max", "Trackbars", 255, 255, empty)

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    while True:
        h_min = cv2.getTrackbarPos("Hue Min", "Trackbars")
        h_max = cv2.getTrackbarPos("Hue Max", "Trackbars")
        s_min = cv2.getTrackbarPos("Sat Min", "Trackbars")
        s_max = cv2.getTrackbarPos("Sat Max", "Trackbars")
        v_min = cv2.getTrackbarPos("Val Min", "Trackbars")
        v_max = cv2.getTrackbarPos("Val Max", "Trackbars")
        
        lower, upper = np.array([h_min, s_min, v_min]), np.array([h_max, s_max, v_max])
        mask = cv2.inRange(hsv, lower, upper)
        result = cv2.bitwise_and(image, image, mask=mask)
        
        cv2.imshow("Mask", mask)
        cv2.imshow("Result", result)
        
        if cv2.waitKey(1) & 0xFF == ord('n'):
            cv2.destroyWindow("Trackbars")
            cv2.destroyWindow("Mask")
            cv2.destroyWindow("Result")
            return lower, upper

if __name__ == "__main__":
    print("--- CALIBRATION SCRIPT ---")
    
    save_dir = "calibration_data"
    if not os.path.exists(save_dir): 
        os.makedirs(save_dir)

    # ---------------------------------------------------------
    # PART A: GRID GEOMETRY (Requires EMPTY Grid)
    # ---------------------------------------------------------
    print("\n[STEP A] Setup source for GRID CALIBRATION (Use an EMPTY grid)")
    mode, source = setup_source()

    # 1. Calibrate Corners
    clicked_points, base_frame = calibrate_grid_corners(mode, source)
    
    # Prompt for variables in the terminal
    print("\n--- GRID DIMENSIONS ---")
    try:
        rows = input(f"Enter number of rows (press Enter for default {ROWS}): ")
        rows = int(rows) if rows.strip() else ROWS
        
        cols = input(f"Enter number of columns (press Enter for default {COLS}): ")
        cols = int(cols) if cols.strip() else COLS
        
        cell_size = input(f"Enter cell size in pixels (press Enter for default {CELL_SIZE}): ")
        cell_size = int(cell_size) if cell_size.strip() else CELL_SIZE
    except ValueError:
        print(f"[!] Invalid input. Defaulting to {ROWS}x{COLS} grid with {CELL_SIZE}px cells.")
        rows, cols, cell_size = ROWS, COLS, CELL_SIZE

    # Calculate Warp Matrix
    width, height = cols * cell_size, rows * cell_size 
    pts1 = np.float32(clicked_points)
    pts2 = np.float32([[0, 0], [width, 0], [width, height], [0, height]])
    matrix = cv2.getPerspectiveTransform(pts1, pts2)
    
    # 2. Calibrate True Lines/Centers
    warped_snapshot = cv2.warpPerspective(base_frame, matrix, (width, height))
    true_centers = calibrate_grid_lines(warped_snapshot, rows, cols)
    
    with open(os.path.join(save_dir, "grid_calib.pkl"), 'wb') as f:
        pickle.dump({
            'matrix': matrix, 
            'width': width, 
            'height': height, 
            'centers': true_centers,
            'rows': rows,
            'cols': cols
        }, f)

    # ---------------------------------------------------------
    # PART B: COLOR ISOLATION (Requires SQUARES on Grid)
    # ---------------------------------------------------------
    print("\n[STEP B] Setup source for COLOR CALIBRATION (Place colored squares on grid)")
    swap = input("Do you want to switch to a different image or camera? (y/n): ").strip().lower()
    
    if swap == 'y':
        if mode == 'camera': source.release()
        mode, source = setup_source()
        
    print("\nPreparing frame for color detection...")
    if mode == 'camera':
        if swap != 'y':
            input("Press 'Enter' when you have placed the colored squares on the grid...")
            # Flush old frames out of the buffer to get a fresh picture
            for _ in range(5): source.read()
            
        ret, color_frame = source.read()
        if not ret:
            print("Failed to grab new camera frame.")
            sys.exit()
    else:
        color_frame = cv2.imread(source)
        if color_frame is None:
            print("Failed to load new image.")
            sys.exit()

    # Warp the NEW frame using the previously calculated matrix
    color_warped_snapshot = cv2.warpPerspective(color_frame, matrix, (width, height))
    
    # 3. Calibrate Colors
    color_thresholds = {}
    for color in ['Blue', 'Pink', 'Green']:
        lower_bound, upper_bound = calibrate_color(color_warped_snapshot, color)
        color_thresholds[color] = {'lower': lower_bound, 'upper': upper_bound}
        
    with open(os.path.join(save_dir, "color_calib.pkl"), 'wb') as f:
        pickle.dump(color_thresholds, f)
        
    print(f"\n[SUCCESS] Calibration completely saved! You can now run detect.py.")
    
    if mode == 'camera': source.release()
    cv2.destroyAllWindows()