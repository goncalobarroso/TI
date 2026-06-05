import cv2
import numpy as np
import sys
import pickle
import os
import threading
import time
import mido

# ==========================================
# MIDI SEQUENCER CONFIGURATION
# ==========================================
BPM = 60
STEP_DELAY = (60.0 / BPM) / 2.0 

PITCH_SCALE = [72, 70, 67, 65, 63, 60, 58, 55, 53] 

SHARED_GRID = []

def midi_sequencer_loop():
    try:
        outport = mido.open_output('python_to_reaper 1')
        print("\n[MIDI SUCCESS] Virtual port 'python_to_reaper 1'' is open and running!\n")
    except Exception as e:
        print(f"\n[MIDI ERROR] Could not create virtual port.\n{e}")
        return

    current_col = 0

    while True:
        if not SHARED_GRID:
            time.sleep(0.1)
            continue
            
        rows = len(SHARED_GRID)
        cols = len(SHARED_GRID[0])
        notes_playing = []

        # DEBUG: Print the current step/column
        print(f"\n--- STEP: Column {current_col} ---")

        # 1. PLAY THE CURRENT COLUMN
        for row in range(rows):
            cell_value = SHARED_GRID[row][current_col]
            
            if cell_value != '0':
                pitch = PITCH_SCALE[row % len(PITCH_SCALE)]
                
                # MIDI channels are 0-indexed in code (0=Ch1, 1=Ch2, 2=Ch3)
                channel = int(cell_value) - 1 
                
                msg = mido.Message('note_on', note=pitch, velocity=100, channel=channel)
                outport.send(msg)
                notes_playing.append((pitch, channel))
                
                # DEBUG: Print exact message sent
                color_name = {1: "Blue", 2: "Pink", 3: "Green"}.get(int(cell_value), "Unknown")
                print(f"  -> [NOTE ON]  Pitch: {pitch} | Reaper Channel: {channel + 1} | Color: {color_name}")

        # 2. WAIT FOR THE NEXT BEAT
        time.sleep(STEP_DELAY)

        # 3. TURN OFF THE NOTES
        for pitch, channel in notes_playing:
            msg = mido.Message('note_off', note=pitch, velocity=0, channel=channel)
            outport.send(msg)
            print(f"  <- [NOTE OFF] Pitch: {pitch} | Reaper Channel: {channel + 1}")

        # 4. MOVE TO NEXT COLUMN
        current_col = (current_col + 1) % cols

def detect_grid_state(warped_img, color_thresholds, true_centers, rows, cols):
    hsv_warped = cv2.cvtColor(warped_img, cv2.COLOR_BGR2HSV)
    masks = {}
    for color, bounds in color_thresholds.items():
        masks[color] = cv2.inRange(hsv_warped, bounds['lower'], bounds['upper'])

    grid_state = []
    output_display = warped_img.copy()

    for row in range(rows):
        row_state = []
        for col in range(cols):
            cx, cy = true_centers[row][col]
            box = 12 
            y1, y2 = max(0, cy - box), min(warped_img.shape[0], cy + box)
            x1, x2 = max(0, cx - box), min(warped_img.shape[1], cx + box)
            
            cell_value = "0"
            display_color = (255, 255, 255) 
            
            if cv2.countNonZero(masks['Blue'][y1:y2, x1:x2]) > 20:
                cell_value = "1"
                display_color = (255, 0, 0) 
            elif cv2.countNonZero(masks['Pink'][y1:y2, x1:x2]) > 20:
                cell_value = "2"
                display_color = (203, 192, 255) 
            elif cv2.countNonZero(masks['Green'][y1:y2, x1:x2]) > 20:
                cell_value = "3"
                display_color = (0, 255, 0) 
                
            row_state.append(cell_value)
            cv2.circle(output_display, (cx, cy), 5, display_color, -1)
            
        grid_state.append(row_state)
        
    return grid_state, output_display

if __name__ == "__main__":
    save_dir = "calibration_data"
    try:
        with open(os.path.join(save_dir, "grid_calib.pkl"), 'rb') as f:
            grid_data = pickle.load(f)
            matrix = grid_data['matrix']
            width, height = grid_data['width'], grid_data['height']
            true_centers = grid_data['centers']
            rows = grid_data.get('rows')
            cols = grid_data.get('cols')
            if rows is None or cols is None:
                rows = int(input("Enter number of rows: "))
                cols = int(input("Enter number of columns: "))
        with open(os.path.join(save_dir, "color_calib.pkl"), 'rb') as f:
            color_thresholds = pickle.load(f)
    except Exception as e:
        print(f"\n[ERROR] Calibration files missing. Run calibrate.py first.\n{e}")
        sys.exit()

    source_choice = input("1. Live Camera\n2. Test Image\nEnter 1 or 2: ")
    mode = 'camera' if source_choice == '1' else 'image'
    
    # --- BRIO CAMERA FIX INJECTED HERE ---
    if mode == 'camera':
        camera_index = 0
        source = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        
        # Force compression and high resolution to prevent freezing
        source.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        source.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        source.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        
        time.sleep(1) # Give hardware time to spin up
        
        if not source.isOpened():
            print("Error: Could not open the Brio camera stream.")
            sys.exit()
    else:
        source = input("Image path: ")
    # -------------------------------------

    threading.Thread(target=midi_sequencer_loop, daemon=True).start()

    print("\n--- SCRIPT RUNNING: Check the Live Detection window and watch this console for MIDI logs. ---")
    print("Press 'q' in the visual window to quit.")

    while True:
        if mode == 'camera':
            ret, frame = source.read()
            if not ret: break
        else:
            frame = cv2.imread(source)

        warped = cv2.warpPerspective(frame, matrix, (width, height))
        final_array, debug_view = detect_grid_state(warped, color_thresholds, true_centers, rows, cols)
        
        SHARED_GRID = final_array
        
        cv2.imshow("Live Detection", debug_view)
        
        delay = 1 if mode == 'camera' else 100 
        if cv2.waitKey(delay) & 0xFF == ord('q'):
            break

    if mode == 'camera': source.release()
    cv2.destroyAllWindows()