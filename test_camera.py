import cv2
import time

# Replace 'YOUR_NEW_INDEX' with the number pygrabber gave you
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

# Force compression so the USB doesn't bottleneck and freeze
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

time.sleep(1)

if not cap.isOpened():
    print("Still failing to open stream.")
    exit()

print("Camera connected!")

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    cv2.imshow('Brio Feed', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()