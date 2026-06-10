import cv2 as cv

aruco_config = {
    "dictionary": cv.aruco.getPredefinedDictionary(cv.aruco.DICT_7X7_250),
    "large_goal_id": 1,
    "small_goal_id": 3,
    "robot_id": 12,
}