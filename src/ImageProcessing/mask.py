from config.config_rules import COLOR_CONFIG, MIN_AREA, MAX_AREA
import numpy as np
import cv2 as cv
import struct
import math
from ImageProcessing.aruco.arucoConfig import aruco_config

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

#Detects the actual objects based on the config color rules
#returns an array: results
#Each entry in result contains:
#   label, countour, bbox, centroid, area, color    
def detect_objects(image: np.ndarray) -> list[dict]:
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    results = []    
    
    for label, cfg in COLOR_CONFIG.items():
        mask = build_mask(hsv, cfg)
        mask = clean_mask(mask, cfg)
        contours, _ = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv.contourArea(cnt)
            
            #Ignore too small detections
            if area < MIN_AREA or area>MAX_AREA:
                continue
            
            x, y, w, h = cv.boundingRect(cnt)
            cx, cy = x + w // 2, y + h //2
            

            results.append({
                "label": label,
                "countour": cnt,
                "bbox": (x,y,w,h),
                "centroid": (cx, cy),
                "area": area,
                "color": cfg["draw_color"],
            })
            
    return results

#Detects the red boundary lines of the level
def detect_boundary_lines(image: np.ndarray) -> list[dict]:
    hsv = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    red_mask = build_mask(hsv,COLOR_CONFIG["boundary"])
    lines = cv.HoughLinesP(red_mask, rho=1, theta=np.pi/180, threshold=100, minLineLength=100, maxLineGap=20)
    
    points =    [(line[0][0],line[0][1]) for line in lines] + \
                [(line[0][2],line[0][3]) for line in lines]
                
    mid_x = sum(p[0] for p in points) / len(points)
    mid_y = sum(p[1] for p in points) / len(points)
    
    #Seperate all identify wall spaces in image based on location
    #top_points = [p for p in points if p[1]<mid_y]
    #bottom_points = [p for p in points if p[1]>=mid_y]
    #left_points = [p for p in points if p[0]<mid_x]
    #right_points = [p for p in points if p[0]>=mid_x]
    top_points    = sorted(points, key=lambda p: p[1])[:len(points)//4]  # lowest y values
    bottom_points = sorted(points, key=lambda p: p[1])[-len(points)//4:] # highest y values
    left_points   = sorted(points, key=lambda p: p[0])[:len(points)//4]  # lowest x values
    right_points  = sorted(points, key=lambda p: p[0])[-len(points)//4:] # highest x values

    
    #Define each extreme corner of masked wall identites
    #With values x1, y1, x2, y2
    top_left = min(top_points, key=lambda p: p[0])
    top_right = max(top_points, key=lambda p: p[0])
    right_top = min(right_points, key=lambda p: p[1])
    right_bottom = max(right_points, key=lambda p: p[1])
    bottom_right = max(bottom_points, key=lambda p: p[0])
    bottom_left = min(bottom_points, key=lambda p: p[0])
    left_bottom = max(left_points, key=lambda p: p[1])
    left_top = min(left_points, key=lambda p: p[1])
    
    #Create actual wall definitions
    final_boundaries = [
        [top_left[0], top_left[1], top_right[0], top_right[1], "top_wall"],
        [right_top[0], right_top[1], right_bottom[0], right_bottom[1], "right_wall"],
        [bottom_left[0], bottom_left[1], bottom_right[0], bottom_right[1], "bottom_wall"],
        [left_top[0], left_top[1], left_bottom[0], left_bottom[1], "left_wall"],
    ]    
    return lines, final_boundaries

#Detects goals from a prefixed width of the boundary lines of the level
def detect_goals_from_lines(lines: list[dict]):
    goals = []
    
    for i, line in enumerate(lines):
        x1, y1, x2, y2, label = line
        if(label == "top_wall" or label=="bottom_wall"):
            continue
        
        if(label == "right_wall"):
            right_goal_height = 150
            right_goal_width = 10
            newGoal = [
                x1 + math.floor(((x2-x1)//2-right_goal_width)),
                x1 + math.floor(((x2-x1)//2+right_goal_width)),
                y1 + math.floor(((y2-y1)//2-right_goal_height/2)),
                y1 + math.floor(((y2-y1)//2+right_goal_height/2)),
            ]
            goals.append(newGoal)
            
        if(label == "left_wall"):
            left_goal_height = 70
            left_goal_width = 10
            newGoal = [
                x1 + math.floor(((x2-x1)//2-left_goal_width/2)),
                x1 + math.floor(((x2-x1)//2+left_goal_width/2)),
                y1 + math.floor(((y2-y1)//2-left_goal_height/2)),
                y1 + math.floor(((y2-y1)//2+left_goal_height/2)),
            ]
            goals.append(newGoal)
        
    return goals

#Detects goals based on aruco markers on the level
def detect_goals_from_aruco(image: np.ndarray):
    
    large_goal_id = aruco_config["large_goal_id"]
    small_goal_id = aruco_config["small_goal_id"]
    
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    parameters = cv.aruco.DetectorParameters()
    detector = cv.aruco.ArucoDetector(dictionary=aruco_config["dictionary"],detectorParams=parameters)
    corners, marker_ids, rejected = detector.detectMarkers(gray)
    
    if(marker_ids is None):
        return
    
    flatten_ids = marker_ids.flatten()
    
    small_goal = None
    large_goal = None
    
    if(large_goal_id in flatten_ids):
        index_large_goal = list(flatten_ids).index(large_goal_id)
        large_goal_pts = corners[index_large_goal][0]  
        x1 = int(large_goal_pts[:, 0].min())
        x2 = int(large_goal_pts[:, 0].max())
        y1 = int(large_goal_pts[:, 1].min())
        y2 = int(large_goal_pts[:, 1].max())
        large_goal = (x1,x2,y1,y2)
        print("large goal")
        print(large_goal)
    
    if(small_goal_id in flatten_ids):
        index_small_goal = list(flatten_ids).index(small_goal_id)
        small_goal_pts = corners[index_small_goal][0]  
        x1 = int(small_goal_pts[:, 0].min())
        x2 = int(small_goal_pts[:, 0].max())
        y1 = int(small_goal_pts[:, 1].min())
        y2 = int(small_goal_pts[:, 1].max())
        small_goal = (x1,x2,y1,y2)
    
    return [large_goal,small_goal]

def detect_robot_from_aruco(image: np.ndarray):
        
    robot_id = aruco_config["robot_id"]
    
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    parameters = cv.aruco.DetectorParameters()
    detector = cv.aruco.ArucoDetector(dictionary=aruco_config["dictionary"],detectorParams=parameters)
    corners, marker_ids, rejected = detector.detectMarkers(gray)
    
    if(marker_ids is None):
        return
    
    flatten_ids = marker_ids.flatten()
    
    if(robot_id in flatten_ids):
        index_robot = list(flatten_ids).index(robot_id)
        robot_pcts = corners[index_robot][0]  
        x1 = int(robot_pcts[:, 0].min())
        x2 = int(robot_pcts[:, 0].max())
        y1 = int(robot_pcts[:, 1].min())
        y2 = int(robot_pcts[:, 1].max())
        robot = (x1,x2,y1,y2)
        return robot
    