import cv2
import numpy as np
from sklearn.cluster import KMeans # You may need to run: pip install scikit-learn

manual_points = []

def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN and len(manual_points) < 4:
        manual_points.append([x, y])

# 1. Setup
cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
cv2.namedWindow("Step 1: Calibration")
cv2.setMouseCallback("Step 1: Calibration", mouse_callback)

while len(manual_points) < 4:
    ret, frame = cap.read()
    if not ret: break
    display = frame.copy()
    for p in manual_points:
        cv2.circle(display, (p[0], p[1]), 5, (0, 255, 0), -1)
    cv2.imshow("Step 1: Calibration", display)
    cv2.waitKey(1)

cv2.destroyWindow("Step 1: Calibration")

warp_size = 800
src_pts = np.float32(manual_points)
dst_pts = np.float32([[0, 0], [warp_size, 0], [warp_size, warp_size], [0, warp_size]])
matrix = cv2.getPerspectiveTransform(src_pts, dst_pts)

while True:
    ret, frame = cap.read()
    if not ret: break

    warped = cv2.warpPerspective(frame, matrix, (warp_size, warp_size))
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    
    # A. Detect Raw Lines
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi/180, 80, minLineLength=100, maxLineGap=50)

    horizontals = []
    verticals = []

    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = np.abs(np.arctan2(y2 - y1, x2 - x1) * 180 / np.pi)
            
            # Group lines by orientation
            if angle < 10 or angle > 170:
                horizontals.append((y1 + y2) / 2)
            elif 80 < angle < 100:
                verticals.append((x1 + x2) / 2)

    # B. Clean up the grid (Cluster the messy lines into "Perfect" averages)
    def get_clusters(data, count):
        if len(data) < count: return []
        kmeans = KMeans(n_clusters=count, n_init=10).fit(np.array(data).reshape(-1, 1))
        return sorted(kmeans.cluster_centers_.flatten())

    # IMPORTANT: Change '2' to the number of internal grid lines you drew
    # Your photo shows 2 horizontal and 3 vertical internal lines
    v_headers = get_clusters(verticals, 3) 
    h_headers = get_clusters(horizontals, 1)

    # C. Draw the Perfect Grid
    # Draw Vertical Lines
    for vx in v_headers:
        cv2.line(warped, (int(vx), 0), (int(vx), warp_size), (255, 0, 0), 2)
    
    # Draw Horizontal Lines
    for hy in h_headers:
        cv2.line(warped, (0, int(hy)), (warp_size, int(hy)), (255, 0, 0), 2)

    # D. Marker Detection
    _, thresh = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if 800 < cv2.contourArea(cnt) < 15000:
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx, cy = int(M["m10"]/M["m00"]), int(M["m01"]/M["m00"])
                if cx < 100 or cx > 700 or cy < 100 or cy > 700:
                    cv2.drawContours(warped, [cnt], -1, (0, 0, 255), 3)

    cv2.imshow("Perfect Grid View", warped)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()