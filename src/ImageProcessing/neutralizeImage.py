import cv2
import numpy as np

clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8, 8))

def auto_white_balance(frame):
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype("float32")
    l, a, b = cv2.split(lab)
    a -= (a.mean() - 128)
    b -= (b.mean() - 128)
    lab = np.clip(cv2.merge([l, a, b]), 0, 255).astype("uint8")
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

def normalize_frame(frame):
    # 1. Auto white balance
    frame = auto_white_balance(frame)

    # 2. CLAHE on lightness only
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = clahe.apply(l)
    frame = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    # 3. Boost saturation so HSV color masks hit more reliably
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype("float32")
    hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.4, 0, 255)  # boost saturation
    frame = cv2.cvtColor(hsv.astype("uint8"), cv2.COLOR_HSV2BGR)

    return frame