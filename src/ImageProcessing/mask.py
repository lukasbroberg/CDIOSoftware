from config.config_rules import COLOR_CONFIG, MIN_AREA
import numpy as np
import cv2 as cv

#Cleanup noise using morphological image processing
MORPH_KERNEL = cv.getStructuringElement(cv.MORPH_RECT, (7,7))

#Creates a mask around the object
def build_mask(hsv: np.ndarray, cfg: dict) -> np.ndarray:
    mask = cv.inRange(hsv, cfg["lower"], cfg["upper"])
    if "lower2" in cfg:
        mask2 = cv.inRange(hsv, cfg["lower2"], cfg["upper2"])
        mask = cv.bitwise_or(mask, mask2)
    return mask

#cleans up the mask
def clean_mask(mask: np.ndarray) -> np.ndarray:
    mask = cv.erode(mask, MORPH_KERNEL, iterations=2)
    mask = cv.dilate(mask, MORPH_KERNEL, iterations=3)
    return mask

#Detects the actual objects based on the config color rules
#returns an array: results
#Each entry in result contains:
#   label, countour, bbox, centroid, area, color    
def detect_objects(image: np.ndarray) -> list[dict]:
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    results = []
    
    for label, cfg in COLOR_CONFIG.items():
        mask = build_mask(hsv, cfg)
        mask = clean_mask(mask)
        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv.contourArea(cnt)
            
            #Ignore too small detections
            if area < MIN_AREA:
                continue
            
            x, y, w, h = cv.boundingRect(cnt)
            cx, cy = x + w // 2, y + h //2
            

            results.append({
                "label": label,
                "countour": cnt,
                "bbox": (x,y,w,h),
                "centroid": (cx, cy),
                "area": area,
                "color": cfg["draw_color"],
            })
            
    return results