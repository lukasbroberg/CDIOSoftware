import numpy as np
import cv2 as cv

#Color config is for defining the color rules of each object in the picture
COLOR_CONFIG = {
    "orange_ball": {
        # Orange sits near red's high edge → hue 5-18 works well for a ping-pong ball
        "kernel": cv.getStructuringElement(cv.MORPH_RECT, (5,5)),
        "lower": np.array([12,  60,  160]),
        "upper": np.array([30, 255, 255]),
        "draw_color": (0, 140, 255),   # BGR – orange for display
    },
    "white_ball": {
        # White = very low saturation, high brightness
        "kernel": cv.getStructuringElement(cv.MORPH_ELLIPSE, (5,5)),
        "lower": np.array([0,   0, 200]),
        "upper": np.array([180, 40, 255]),
        "draw_color": (240, 240, 200),  # BGR – light gray for display
    },
    "boundary": {
        # Red wraps around 0 in OpenCV HSV; handle both lobes
        "kernel": cv.getStructuringElement(cv.MORPH_RECT, (2,2)),
        "lower":  np.array([0,   100, 130]),
        "upper":  np.array([20,   255, 255]),
        "lower2": np.array([165, 50, 80]),
        "upper2": np.array([180, 255, 255]),
        "draw_color": (0, 0, 220),      # BGR – red for display
    },
}

#Doesnt recognize objects small than (in pxs):
MIN_AREA = 800
MAX_AREA = 2000