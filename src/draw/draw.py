import numpy as np
import cv2 as cv

#Draws upon the a copy of the original image the actual detected objects
def draw_results(image: np.ndarray, detectections: list[dict], lines: list = None, goals: list = None, robot: list = None, robot_angle: float = None, cross_boundary: list = None) -> np.ndarray:
    
    if image is None:
        return None
    
    output = image.copy()
    
    #Draw object detection
    if detectections is not None:
        for det in detectections:
            x,y,w,h = det["bbox"]
            cx,cy = det["centroid"]
            color = det["color"]
            label = det["label"]
            
            cv.rectangle(output, (x,y), (x+w,y+h), color, 2)
            cv.circle(output,(cx, cy), 5, color, -1)
            if label is not None:
                cv.putText(output,str(label),(x+10,y),1,2,color,2,None,None)
        
        horizontal, vertical = [], []
    
    
    #Draw boundary lines
    if lines is not None:
        for i, line in enumerate(lines):
            if line is None or len(line) != 5:
                continue
            x1,y1,x2,y2,label = line
        
            cv.line(output,(x1,y1),(x2,y2),(200,0,0),5)
            cv.putText(output, str(label),(x1,y1),1,2,(0,0,0),2,None,None)
            
    if goals is not None:
        for i, goal in enumerate(goals):
            if(goal is not None):
                x1,x2,y1,y2,label = goal
                cv.rectangle(output, (x1,y1), (x2,y2),(0,120,0), 5)
                cv.putText(output,str(label),(x1,y1),1,2,(0,120,0),2,None,None)
            
    if robot is not None:
        cv.polylines(output, [robot], isClosed=True,color=(0,255,100), thickness=5)
        cv.putText(output,"robot",[robot][0][0]+(10,0),1,2,(0,255,100),2,None,None)
        if robot_angle is not None:
            cv.putText(output,"angle: " + str(robot_angle),[robot][0][0]+(10,50),1,2,(0,255,100),2,None,None)
        
    if cross_boundary is not None:
        for i, line in enumerate(cross_boundary):
            x1,y1,x2,y2,label = line
            cv.line(output,(x1,y1),(x2,y2),(255,255,0),2)
            cv.putText(output, str(label),(x1,y1),1,2,(0,0,0),2,None,None)
            
    return output