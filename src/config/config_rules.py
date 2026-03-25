#Color config is for defining the color rules of each object in the picture
COLOR_CONFIG = {
    "orange_ball": {
        # Orange sits near red's high edge → hue 5-18 works well for a ping-pong ball
        "lower": np.array([8,  150,  150]),
        "upper": np.array([18, 255, 255]),
        "draw_color": (0, 140, 255),   # BGR – orange for display
    },
    "white_ball": {
        # White = very low saturation, high brightness
        "lower": np.array([0,   0, 200]),
        "upper": np.array([180, 40, 255]),
        "draw_color": (200, 200, 200),  # BGR – light gray for display
    },
    "boundary": {
        # Red wraps around 0 in OpenCV HSV; handle both lobes
        "lower":  np.array([0,   120, 80]),
        "upper":  np.array([5,   255, 255]),
        "lower2": np.array([165, 120, 80]),
        "upper2": np.array([180, 255, 255]),
        "draw_color": (0, 0, 220),      # BGR – red for display
    },
}

#Doesnt recognize objects small than (in pxs):
MIN_AREA = 350