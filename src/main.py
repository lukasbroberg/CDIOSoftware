import numpy as np
import cv2 as cv
from config.config_rules import COLOR_CONFIG, MIN_AREA
from ImageProcessing.mask import detect_objects
from ImageProcessing.image import loadImage
from draw.draw import draw_results
from controller.mainController import *

#Doesnt work right now
def on_click(event, x, y, hsv, flags, param):
    print(event)
    if event == cv.EVENT_LBUTTONDOWN:
        print(f"HSV for ({x,y}): {hsv[y,x]}")

def main():
    image_path = "images/capture3.png"
    picture = loadImage(image_path)
    
    #Raw picture
    cv.imshow("Displayed image",picture)
    image_hsv = cv.cvtColor(picture, cv.COLOR_BGR2HSV)
    cv.setMouseCallback("Pick color", lambda event, x, y, flags, param: on_click(event,x,y,flags,param,hsv=image_hsv))
    
    
    #Detection pictures
    detections = detect_objects(picture)
    #for det in detections:
    #    print(
    #        f"[{det['label']}]"
    #        f"centroid=({[det['centroid'][0]]},{[det['centroid'][1]]})"
    #        f"bbox={det['bbox']}"
    #        f"area={det['area']:.0f}px"
    #    )
    
    mainController = MainController()
    mainController.initializeObjects(detections)
    
    output = draw_results(picture, detections)
    
    cv.imshow("Detections", output)
    cv.waitKey(0)
    cv.destroyAllWindows()
    
if __name__ == "__main__":
    main()