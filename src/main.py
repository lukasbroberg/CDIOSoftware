import numpy as np
import cv2 as cv
from config.config_rules import COLOR_CONFIG, MIN_AREA
from ImageProcessing.image import loadImage, mask_image_by_walls
from ImageProcessing.detection import detect_objects, detect_boundary_lines, detect_goals_from_lines, detect_goals_from_aruco, detect_robot_from_aruco, detect_boundary_cross
from draw.draw import draw_results
from controller.mainController import *
from config.arucoConfig import aruco_config 

#Doesnt work right now
def on_mouse_click(event, x, y, flags, params):
    if event == cv.EVENT_LBUTTONDOWN:
        image = params["image"]
        hsv = params["hsv"]
        
        bgr_pixel = image[y, x]
        hsv_pixel = hsv[y, x]
        
        print(f"Clicked at ({x}, {y})")
        print(f"  BGR: {bgr_pixel}")
        print(f"  HSV: {hsv_pixel}")

def generate_aruco_marker():
    size_of_marker = 400
    id = 3
    dictionary = aruco_config["dictionary"]
    
    img = cv.aruco.generateImageMarker(dictionary, id, size_of_marker)
    cv.imshow("Marker", img)
    cv.imwrite("aruco"+str(id)+".png", img)
    cv.waitKey(0)

def main():
    
    image_rec_active = True
    image_rec_from_live_video(image_rec_active)
    #image_rec_from_static_image()
    
    #generate_aruco_marker()
    
    
    #image_path = "images/capture3.png"
    #picture = loadImage(image_path)
    
    #Raw picture
    #cv.imshow("Displayed image",picture)
    #image_hsv = cv.cvtColor(picture, cv.COLOR_BGR2HSV)    
    
    #Detection pictures
    #detections = detect_objects(picture)
    #lines, final_boundaries = detect_boundary_lines(picture)
    #goals = detect_goals_from_lines(final_boundaries)
    
    #output = draw_results(picture, detections, final_boundaries, goals)
    
    #cv.imshow("Detections", output)
    #cv.setMouseCallback("Detections", on_mouse_click, param={"image": picture, "hsv": image_hsv})
    
    #cv.waitKey(0)
    #cv.destroyAllWindows()

#Static function get objects from a static image - use for testing.
def image_rec_from_static_image():
    image_path = "images/test_image_aruco1.png"
    picture = loadImage(image_path)
    
    #Raw picture
    cv.imshow("Displayed image",picture)
    image_hsv = cv.cvtColor(picture, cv.COLOR_BGR2HSV)    
    
    #Detection pictures
    lines, final_boundaries = detect_boundary_lines(picture)
    image_cropped_by_boundaries = mask_image_by_walls(picture,final_boundaries)
    
    detections = detect_objects(image_cropped_by_boundaries)

    goals = detect_goals_from_aruco(picture)
    robot_pos, robot_angle, raw_pts = detect_robot_from_aruco(image_cropped_by_boundaries)
    cross_boundary = detect_boundary_cross(image_cropped_by_boundaries)
    robot_pos_formatted = np.array(raw_pts,dtype=np.int32)
    output = draw_results(picture, detections, final_boundaries, goals, robot_pos_formatted, robot_angle, cross_boundary)
    
    cv.imshow("Detections", output)
    cv.setMouseCallback("Detections", on_mouse_click, param={"image": picture, "hsv": image_hsv})
    
    cv.waitKey(0)
    cv.destroyAllWindows()

#Live loop of camera
def image_rec_from_live_video(image_rec_active: bool):
    cam = cv.VideoCapture(1)
    frame_width = int(cam.get(cv.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cam.get(cv.CAP_PROP_FRAME_HEIGHT))

    #Define codec
    fourcc = cv.VideoWriter.fourcc(*'mp4v')
    out = cv.VideoWriter('output.mp4',fourcc,2.0,(frame_width,frame_height))
    
    #Start camera
    while True:
        #Get camera frame
        ret, frame = cam.read()    

        # Write the frame to the output file
        out.write(frame)
        
        #Detecetions
        if image_rec_active:
            detections = detect_objects(frame)
            lines, final_boundaries = detect_boundary_lines(frame)
            image_cropped_by_boundaries = mask_image_by_walls(frame,final_boundaries)
            goals = detect_goals_from_aruco(frame)
            robot_pos, robot_angle, raw_pts = detect_robot_from_aruco(image_cropped_by_boundaries)
            cross_boundary = detect_boundary_cross(image_cropped_by_boundaries)
            
            #Format robot_pos for drawing
            robot_pos_formatted = None
            if(raw_pts is not None):
                robot_pos_formatted = np.array(raw_pts,dtype=np.int32)
            
            output = draw_results(frame, detections, final_boundaries, goals, robot_pos_formatted, robot_angle, cross_boundary)
                
            # Display the captured frame
            cv.imshow('Camera', output)
        else:
            cv.imshow('Camera', frame)


        # Press 'q' to exit the loop
        if cv.waitKey(1) == ord('q'):
            break
        if cv.waitKey(1) == ord('d'):
            if image_rec_active==False:
                image_rec_active=True
            else:
                image_rec_active=False
            print(image_rec_active)

    cam.release()
    out.release()
    cv.destroyAllWindows()

if __name__ == "__main__":
    main()
    
