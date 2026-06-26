import cv2 as cv
import math

# ─── CONFIGURATION ───────────────────────────────────────────────────────────
# Change this to the actual size of the object you are measuring on the floor!
# For example: an A4 sheet of paper is 29.7 cm long, or a standard ruler is 30.0 cm.
REAL_WORLD_SIZE_CM = 4.0
CAMERA_INDEX = 0
# ─────────────────────────────────────────────────────────────────────────────

clicked_points = []

def click_event(event, x, y, flags, param):
    """Callback function to record mouse clicks."""
    global clicked_points
    if event == cv.EVENT_LBUTTONDOWN:
        clicked_points.append((x, y))
        print(f"[CLICK] Point {len(clicked_points)} registered at: ({x}, {y})")

def main():
    global clicked_points
    
    # 1. Initialize camera and grab dimensions automatically
    cam = cv.VideoCapture(CAMERA_INDEX)
    if not cam.isOpened():
        print(f"[ERROR] Could not open camera source {CAMERA_INDEX}")
        return

    frame_w = int(cam.get(cv.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cam.get(cv.CAP_PROP_FRAME_HEIGHT))
    
    print("\n" + "="*50)
    print(f"  CAMERA INITIALIZED SUCCESSFULLY")
    print(f"  Resolution: {frame_w}x{frame_h}")
    print("="*50)
    print(f"\nINSTRUCTIONS:\n"
          f"1. Place a {REAL_WORLD_SIZE_CM} cm object near the CENTER of the frame.\n"
          f"2. CLICK on the START point of the object.\n"
          f"3. CLICK on the END point of the object.\n"
          f"4. Press 'q' or 'ESC' to calculate calibration once finished.\n")

    cv.namedWindow("Calibration Window")
    cv.setMouseCallback("Calibration Window", click_event)

    while True:
        ret, frame = cam.getBackendName() and cam.read()
        if not ret:
            print("[ERROR] Failed to grab frame.")
            break

        # Draw visual aids (Center crosshairs)
        cx, cy = frame_w // 2, frame_h // 2
        cv.line(frame, (cx - 20, cy), (cx + 20, cy), (0, 255, 255), 1)
        cv.line(frame, (cx, cy - 20), (cx, cy + 20), (0, 255, 255), 1)

        # Draw clicked points and lines connecting them
        for i, pt in enumerate(clicked_points):
            cv.circle(frame, pt, 5, (0, 0, 255), -1)
            cv.putText(frame, f"P{i+1}", (pt[0] + 10, pt[1] - 10), 
                        cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        
        if len(clicked_points) >= 2:
            cv.line(frame, clicked_points[0], clicked_points[1], (0, 255, 0), 2)

        cv.imshow("Calibration Window", frame)

        key = cv.waitKey(1) & 0xFF
        if key == ord('q') or key == 27 or len(clicked_points) == 2:
            # Wait a split second to let the user see the drawn line
            cv.waitKey(500)
            break

    cam.release()
    cv.destroyAllWindows()

    # 2. Calculate the exact pixel per cm scale factor
    if len(clicked_points) < 2:
        print("[CANCELLED] Calibration aborted. You must select two points.")
        return

    p1, p2 = clicked_points[0], clicked_points[1]
    pixel_distance = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    
    pixels_per_cm = pixel_distance / REAL_WORLD_SIZE_CM

    # 3. Print out your ready-to-paste code block
    print("\n" + "═"*60)
    print("             CALIBRATION RESULTS CONTENT")
    print("═"*60)
    print(f"Pixel Distance Measured : {pixel_distance:.4f} pixels")
    print(f"Real World Object Size : {REAL_WORLD_SIZE_CM} cm")
    print(f"Calculated Scale Factor : {pixels_per_cm:.10f} px/cm\n")
    print("Copy and paste this directly into your 'perspectiveCorrection.py':\n")
    print("# " + "-"*50)
    print(f"PIXELS_PER_CM_FLOOR = {pixels_per_cm:.10f}")
    print("# " + "-"*50)
    print("═"*60 + "\n")
    
if __name__ == "__main__":
    main()