
from config.config_rules import COLOR_CONFIG, MIN_AREA, MAX_AREA
import numpy as np
import cv2 as cv
import struct
import math
from config.arucoConfig import aruco_config
from ImageProcessing.image import mask_image_by_walls


#Cleanup noise using morphological image processing
MORPH_KERNEL = cv.getStructuringElement(cv.MORPH_ELLIPSE, (3,3))

#Creates a mask around the object
def build_mask(hsv: np.ndarray, cfg: dict) -> np.ndarray:
    mask = cv.inRange(hsv, cfg["lower"], cfg["upper"])
    if "lower2" in cfg:
        mask2 = cv.inRange(hsv, cfg["lower2"], cfg["upper2"])
        mask = cv.bitwise_or(mask, mask2)
    return mask

#cleans up the mask
def clean_mask(mask: np.ndarray, cfg: dict) -> np.ndarray:
    
    kernel = cfg.get("kernel", MORPH_KERNEL)
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=1)
    mask = cv.erode(mask, kernel, iterations=1)
    mask = cv.dilate(mask, kernel, iterations=3)
    
    return mask

#Specificaly cleanup for boundary detectons.
def clean_mask_boundary(mask: np.ndarray, cfg: dict) -> np.ndarray:
    kernel = cfg.get("kernel", MORPH_KERNEL)
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=2)
    return mask
