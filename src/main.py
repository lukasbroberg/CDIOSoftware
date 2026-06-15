
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
    print("MAIN STARTED")
    
    image_rec_active = True
    image_rec_from_live_video(image_rec_active)
    
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
    

def setup_trackbars(window_name: str = "Camera") -> None:
    """Call once after the first cv.imshow(window_name, …)."""
 
    def _noop(_): pass   # OpenCV requires a callback
 
    # ── White ball (HSV) ──────────────────────
    cv.createTrackbar("W H-min", window_name,   0, 179, _noop)
    cv.createTrackbar("W H-max", window_name, 179, 179, _noop)
    cv.createTrackbar("W S-min", window_name,   0, 255, _noop)
    cv.createTrackbar("W S-max", window_name,  50, 255, _noop)
    cv.createTrackbar("W V-min", window_name, 200, 255, _noop)
    cv.createTrackbar("W V-max", window_name, 255, 255, _noop)
 
    # ── Orange ball (HSV) ─────────────────────
    cv.createTrackbar("O H-min", window_name,   5, 179, _noop)
    cv.createTrackbar("O H-max", window_name,  20, 179, _noop)
    cv.createTrackbar("O S-min", window_name, 150, 255, _noop)
    cv.createTrackbar("O S-max", window_name, 255, 255, _noop)
    cv.createTrackbar("O V-min", window_name, 150, 255, _noop)
    cv.createTrackbar("O V-max", window_name, 255, 255, _noop)

def get_params(window_name: str = "Camera") -> dict:
    """
    Returns a dict with two sub-dicts:
 
      params["hsv"]["white"]  → (h_min, h_max, s_min, s_max, v_min, v_max)
      params["hsv"]["orange"] → (h_min, h_max, s_min, s_max, v_min, v_max)
      params["canny"]         → (lo, hi)
      params["hough"]         → (rho, threshold, min_line_length, max_line_gap)
    """
    g = lambda name: cv.getTrackbarPos(name, window_name)
 
    return {
        "hsv": {
            "white": (
                g("W H-min"), g("W H-max"),
                g("W S-min"), g("W S-max"),
                g("W V-min"), g("W V-max"),
            ),
            "orange": (
                g("O H-min"), g("O H-max"),
                g("O S-min"), g("O S-max"),
                g("O V-min"), g("O V-max"),
            ),
        },
        "canny": (g("Canny lo"), g("Canny hi")),
        "hough": (
            max(1, g("Hough rho")),   # rho must be >= 1
            g("Hough thresh"),
            g("Hough minLen"),
            g("Hough maxGap"),
        ),
    }

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
    
    config = COLOR_CONFIG
    
    detections = detect_objects(image_cropped_by_boundaries, config)

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
    print("CAMERA FUNCTION STARTED")

    cam = cv.VideoCapture(0)

    if not cam.isOpened():
        print("Camera could not be opened")
        return
    
    frame_width = int(cam.get(cv.CAP_PROP_FRAME_WIDTH))
    frame_height = int(cam.get(cv.CAP_PROP_FRAME_HEIGHT))


    #INITIALIZE VALUES - Koden kører en enkelt gang og ikke mere
    controller = MainController() 
    
    trackbars_ready = False
    show_trackbars = False
    
    config = COLOR_CONFIG
    
    

    #EACH FRAME - Koden kører for hvert billede i sekundet fra kameraet
    while True:
        #Get trackbar values
        params = get_params() 
        if show_trackbars:
            wh = params["hsv"]["white"]
            og = params["hsv"]["orange"]
            # White ball
            config["white_ball"]["lower"] = np.array([wh[0], wh[2], wh[4]])
            config["white_ball"]["upper"] = np.array([wh[1], wh[3], wh[5]])

            # Orange ball
            config["orange_ball"]["lower"] = np.array([og[0], og[2], og[4]])
            config["orange_ball"]["upper"] = np.array([og[1], og[3], og[5]])
        
        #Get camera frame
        ret, frame = cam.read()   
        

        if frame is None:
            continue
        
            
        #Detecetions
        if image_rec_active:
            detections = detect_objects(frame, config)
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
            
            if not trackbars_ready and show_trackbars is True:
                setup_trackbars('Camera')
                trackbars_ready = True
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
    #out.release()
    cv.destroyAllWindows()
if __name__ == "__main__":  
    main()