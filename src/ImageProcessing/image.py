import cv2 as cv
import numpy as np

#Loads the image and returns image
def loadImage(imagePath):
    image = cv.imread(imagePath)
    if image is None:
        raise FileNotFoundError("Couldnt load image")
    return image

def mask_image_by_walls(image: np.ndarray, lines: list):
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