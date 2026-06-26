import cv2 as cv
import math
import sys

# ─── CONFIGURATION ───────────────────────────────────────────────────────────
# Change this to the actual size of the object you are measuring in the image.
# For example: an A4 sheet of paper is 29.7 cm long, or a standard ruler is 30.0 cm.
REAL_WORLD_SIZE_CM = 4.0
IMAGE_PATH = "images/capture1.png"  # <-- Change this to your image path
# ─────────────────────────────────────────────────────────────────────────────

clicked_points = []
display_frame = None

def click_event(event, x, y, flags, param):
    """Callback function to record mouse clicks and redraw the image."""
    global clicked_points, display_frame

    if event == cv.EVENT_LBUTTONDOWN and len(clicked_points) < 2:
        clicked_points.append((x, y))
        print(f"[CLICK] Point {len(clicked_points)} registered at: ({x}, {y})")
        redraw()

def redraw():
    """Redraw the base image with all annotations."""
    global display_frame

    frame = display_frame.copy()
    frame_h, frame_w = frame.shape[:2]

    # Center crosshairs
    cx, cy = frame_w // 2, frame_h // 2
    cv.line(frame, (cx - 20, cy), (cx + 20, cy), (0, 255, 255), 1)
    cv.line(frame, (cx, cy - 20), (cx, cy + 20), (0, 255, 255), 1)

    # Draw clicked points
    for i, pt in enumerate(clicked_points):
        cv.circle(frame, pt, 5, (0, 0, 255), -1)
        cv.putText(frame, f"P{i+1}", (pt[0] + 10, pt[1] - 10),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    # Draw line between points
    if len(clicked_points) == 2:
        cv.line(frame, clicked_points[0], clicked_points[1], (0, 255, 0), 2)
        cv.putText(frame, "Press any key to confirm", (10, frame_h - 15),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    else:
        remaining = 2 - len(clicked_points)
        cv.putText(frame, f"Click {remaining} more point(s)", (10, frame_h - 15),
                   cv.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

    cv.imshow("Calibration Window", frame)

def main():
    global display_frame

    # 1. Load the image
    image = cv.imread(IMAGE_PATH)
    if image is None:
        print(f"[ERROR] Could not load image: '{IMAGE_PATH}'")
        print("        Check that the path is correct and the file exists.")
        sys.exit(1)

    display_frame = image
    frame_h, frame_w = image.shape[:2]

    print("\n" + "="*50)
    print(f"  IMAGE LOADED SUCCESSFULLY")
    print(f"  Resolution : {frame_w}x{frame_h}")
    print(f"  File       : {IMAGE_PATH}")
    print("="*50)
    print(f"\nINSTRUCTIONS:\n"
          f"1. The image shows a {REAL_WORLD_SIZE_CM} cm reference object.\n"
          f"2. CLICK on the START point of the object.\n"
          f"3. CLICK on the END point of the object.\n"
          f"4. Press any key to confirm once both points are selected.\n"
          f"   (Press 'r' at any time to reset your points.)\n")

    cv.namedWindow("Calibration Window")
    cv.setMouseCallback("Calibration Window", click_event)
    redraw()

    # 2. Event loop — static image, so we just waitKey
    while True:
        key = cv.waitKey(0) & 0xFF

        if key == ord('r'):
            clicked_points.clear()
            print("[RESET] Points cleared. Click two new points.")
            redraw()
        elif len(clicked_points) == 2:
            break
        elif key == 27:  # ESC
            print("[CANCELLED] Calibration aborted.")
            cv.destroyAllWindows()
            return

    cv.destroyAllWindows()

    # 3. Calculate the pixel-per-cm scale factor
    p1, p2 = clicked_points[0], clicked_points[1]
    pixel_distance = math.hypot(p2[0] - p1[0], p2[1] - p1[1])
    pixels_per_cm = pixel_distance / REAL_WORLD_SIZE_CM

    # 4. Print results
    print("\n" + "═"*60)
    print("   Resultat")
    print(f"  Pixel Distance Measured : {pixel_distance:.4f} pixels")
    print(f"  Real World Object Size  : {REAL_WORLD_SIZE_CM} cm")
    print(f"  Calculated Scale Factor : {pixels_per_cm:.10f} px/cm\n")
    print(f"  PIXELS_PER_CM_FLOOR = {pixels_per_cm:.10f}")

if __name__ == "__main__":
    main()