import cv2 as cv
import numpy as np
from config.arucoConfig import aruco_config

#Loads the image and returns image
def loadImage(imagePath):
    image = cv.imread(imagePath)
    if image is None:
        raise FileNotFoundError("Couldnt load image")
    return image

def mask_image_by_walls(image: np.ndarray, lines: list):
    
    if image is None or lines is None:
        return None
    
    wall_map = {}
    for x1,y1,x2,y2, label in lines:
        wall_map[label] = (int(x1), int(y1), int(x2), int(y2))
    
    offset = 20
    
    top = min(wall_map['top_wall'][1], wall_map['top_wall'][3])+offset
    bottom = max(wall_map['bottom_wall'][1], wall_map['bottom_wall'][3])-offset
    left = min(wall_map['left_wall'][0], wall_map['left_wall'][2])+offset
    right = max(wall_map['right_wall'][0], wall_map['right_wall'][2])-offset
    
    masked = np.zeros_like(image)
    masked[top:bottom,left:right] = image[top:bottom,left:right]
    
    
    #h, w = image.shape[:2]
    #top = max(0,top)+offset
    #bottom = min(h,bottom)-offset
    #left = max(0,left)+offset
    #right = min(w,right)-offset
    
    return masked #image[top:bottom,left:right]


def color_correct_with_reference(image, ref_roi):
    """
    image: Det originale BGR billede
    ref_roi: En tuple med (x, y, bredde, højde) på dit hvide referenceobjekt
    """
    x, y, w, h = ref_roi
    roi = image[y:y+h, x:x+w]
    
    # Find gennemsnitsfarven (B, G, R) af det, der BURDE være hvidt
    avg_channels = cv.mean(roi)[:3]
    avg_b, avg_g, avg_r = avg_channels
    
    # Det maksimale mål for hvidt (255)
    # Vi finder skaleringsfaktorer for hver kanal
    scale_b = 255.0 / avg_b if avg_b > 0 else 1.0
    scale_g = 255.0 / avg_g if avg_g > 0 else 1.0
    scale_r = 255.0 / avg_r if avg_r > 0 else 1.0
    
    # Split billedet i kanaler og tildel de nye vægte
    b, g, r = cv.split(image)
    b = np.clip(b * scale_b, 0, 255).astype(np.uint8)
    g = np.clip(g * scale_g, 0, 255).astype(np.uint8)
    r = np.clip(r * scale_r, 0, 255).astype(np.uint8)
    
    # Saml billedet igen
    corrected_image = cv.merge([b, g, r])
    return corrected_image