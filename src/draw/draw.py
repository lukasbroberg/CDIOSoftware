import numpy as np
import cv2 as cv
from models.Ball import *
from models.Robot import *
from models.TrackedObjects import *

#Draws upon the a copy of the original image the actual detected objects
def draw_detections(output: np.ndarray, detectections: list[dict]) -> np.ndarray:
    if output is None:
        return None
        
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
                cv.putText(output,str(label),(x+30,y),1,2,color,2,None,None)
                cv.putText(output,str(x) + ", " + str(y),(x+30,y+40),1,2,color,2,None,None)
    
    return output    

def draw_lines(output: np.ndarray, lines: list = None):
    if output is None:
        return None
    
    #Draw boundary lines
    if lines is not None:
        for i, line in enumerate(lines):
            if line is None or len(line) != 5:
                continue
            
            x1,y1,x2,y2,label = line
        
            cv.line(output,(x1,y1),(x2,y2),(200,0,0),5)
            cv.putText(output, str(label),(x1,y1),1,2,(0,0,0),2,None,None)
    return output

def draw_goals(output: np.ndarray, goals: list = None):
    if output is None:
        return None
    
    if goals is not None:
        for i, goal in enumerate(goals):
            if(goal is not None):
                x1,x2,y1,y2,label = goal
                cv.rectangle(output, (x1,y1), (x2,y2),(0,120,0), 5)
                cv.putText(output,str(label),(x1,y1),1,2,(0,120,0),2,None,None)
    return output

def draw_robot(output: np.ndarray, robot: list = None, robot_angle: float = None):
    if output is None:
        return None
    
    if robot is not None:
        cv.polylines(output, [robot], isClosed=True,color=(0,255,100), thickness=5)
        cv.putText(output,"robot",[robot][0][0]+(10,0),1,2,(0,255,100),2,None,None)
        if robot_angle is not None:
            cv.putText(output,"angle: " + str(robot_angle),[robot][0][0]+(10,50),1,2,(0,0,0),2,None,None)
            cv.putText(output,"pos: " + str([robot][0][0]),[robot][0][0]+(10,100),1,2,(0,0,0),2,None,None)
    return output

def draw_cross_boundary(output: np.ndarray, cross_boundary: list = None):
    if output is None:
        return None
    
    if cross_boundary is not None:
        for i, line in enumerate(cross_boundary):
            if line is None or len(line) != 5:
                continue
            x1,y1,x2,y2,label = line
            cv.line(output,(x1,y1),(x2,y2),(255,255,0),2)
            cv.putText(output, str(label),(x1,y1),1,2,(0,0,0),2,None,None)
            
    return output

def draw_target(output: np.ndarray, targetBall: Ball, robot: Robot = None):
        
    if output is None:
        return
    
    if targetBall is None:
        return
    
    x = targetBall.x
    y = targetBall.y
    color = (255,0,0)

    if x is None or y is None:
        return output

    cv.rectangle(output, (x,y), (x+30,y+30), color, 2)
    cv.putText(output,str("target"),(x+30,y),1,2,(color),2,None,None)
    if robot is None:
        return output
    cv.line(output, (robot.x, robot.y),(targetBall.x,targetBall.y), (0,0,255), 3)
    return output


def draw_tracked_objects(output: np.ndarray, objects: list[TrackedObject]):
    if output is None:
        return
    
    if objects is None:
        return output
    
    for object in objects:
        cv.putText(output, str(object.id), (object.x, object.y),1,2,(0,0,0),2,None,None)
    
    return output