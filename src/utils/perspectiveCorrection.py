import cv2 as cv

CAMERA_HEIGHT_CM = 164.0

# Define your known object heights (Z-axis values)
HEIGHT_FLOOR = 0.0
HEIGHT_ROBOT = 26.0

# Calibrate this precisely by placing a ruler directly in the center of the frame
# on the floor plane (Z = 0)
PIXELS_PER_CM_FLOOR = 6.5048059156

# Initialize camera capture globally
cam = cv.VideoCapture(1)

# Fetch resolution properties directly from the hardware stream
FRAME_W = 1920 #cam.get(cv.CAP_PROP_FRAME_WIDTH)
FRAME_H = 1080 #cam.get(cv.CAP_PROP_FRAME_HEIGHT)

# Fallback defaults in case the camera takes a moment to initialize

def pixel_to_world(px, py, object_height_cm=0.0):
    """
    Convert pixel coordinates to real-world cm coordinates relative to the 
    camera center, taking into account the object's physical height (Z-axis).
    """
    cx = FRAME_W / 2
    cy = FRAME_H / 2
    
    # 1. Calculate raw offset from center in pixels
    dx_px = px - cx
    dy_px = py - cy
    
    # 2. Map to ground floor centimeters first
    dx_cm_floor = dx_px / PIXELS_PER_CM_FLOOR
    dy_cm_floor = dy_px / PIXELS_PER_CM_FLOOR
    
    # 3. Apply radial perspective correction based on object height.
    # Higher objects project further outward from the camera center.
    if object_height_cm > 0:
        scale = (CAMERA_HEIGHT_CM - object_height_cm) / CAMERA_HEIGHT_CM
        dx_cm_corrected = dx_cm_floor * scale
        dy_cm_corrected = dy_cm_floor * scale
        return dx_cm_corrected, dy_cm_corrected
        
    return dx_cm_floor, dy_cm_floor


def world_to_pixel(dx_cm, dy_cm, object_height_cm=0.0):
    """Inverse — convert real-world cm back to pixels based on object height."""
    cx = FRAME_W / 2
    cy = FRAME_H / 2
    
    if object_height_cm > 0:
        scale = CAMERA_HEIGHT_CM / (CAMERA_HEIGHT_CM - object_height_cm)
        dx_cm = dx_cm * scale
        dy_cm = dy_cm * scale
        
    px = cx + (dx_cm * PIXELS_PER_CM_FLOOR)
    py = cy + (dy_cm * PIXELS_PER_CM_FLOOR)
    return px, py
