import numpy as np
import cv2 as cv

#Draws upon the a copy of the original image the actual detected objects
def draw_results(image: np.ndarray, detectections: list[dict]) -> np.ndarray:
    output = image.copy()
    
    for det in detectections:
        x,y,w,h = det["bbox"]
        cx,cy = det["centroid"]
        color = det["color"]
        label = det["label"]
        
        cv.rectangle(output, (x,y), (x+w,y+h), color, 2)
        cv.circle(output,(cx, cy), 5, color, -1)
        
    return output