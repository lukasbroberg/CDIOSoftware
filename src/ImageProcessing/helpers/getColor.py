import cv2 as cv

def on_mouse_click(event, x, y, flags, params):
    if event == cv.EVENT_LBUTTONDOWN:
        image = params["image"]
        hsv = params["hsv"]
        
        bgr_pixel = image[y, x]
        hsv_pixel = hsv[y, x]
        
        print(f"Clicked at ({x}, {y})")
        print(f"  BGR: {bgr_pixel}")
        print(f"  HSV: {hsv_pixel}")