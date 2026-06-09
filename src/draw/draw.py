import numpy as np
import cv2 as cv

#Draws upon the a copy of the original image the actual detected objects
def draw_results(image: np.ndarray, detectections: list[dict], lines: list = None, goals: list = None, robot: list = None) -> np.ndarray:
    
    output = image.copy()
    
    #Draw object detection
    for det in detectections:
        x,y,w,h = det["bbox"]
        cx,cy = det["centroid"]
        color = det["color"]
        label = det["label"]
        
        cv.rectangle(output, (x,y), (x+w,y+h), color, 2)
        cv.circle(output,(cx, cy), 5, color, -1)
    
    horizontal, vertical = [], []
    
    
    #Draw boundary lines
    if lines is not None:
        for i, line in enumerate(lines):
            x1,y1,x2,y2,label = line
           
            cv.line(output,(x1,y1),(x2,y2),(255,255,0),2)
            cv.putText(output, str(label),(x1,y1),1,2,(0,0,0),2,None,None)
            
    if goals is not None:
        for i, goal in enumerate(goals):
            if(goal is not None):
                x1,x2,y1,y2 = goal
                cv.rectangle(output, (x1,y1), (x2,y2),(0,255,0), 5)
            
    if robot is not None:
        x1,x2,y1,y2 = robot
        cv.rectangle(output, (x1,y1), (x2,y2),(0,0,255), 5)
    
    return output