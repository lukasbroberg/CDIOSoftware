import cv2 as cv
from config.arucoConfig import aruco_config

def generate_aruco_marker():
    size_of_marker = 400
    id = 3
    dictionary = aruco_config["dictionary"]
    
    img = cv.aruco.generateImageMarker(dictionary, id, size_of_marker)
    cv.imshow("Marker", img)
    cv.imwrite("aruco"+str(id)+".png", img)
    cv.waitKey(0)