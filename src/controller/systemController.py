import threading
import numpy as np
import cv2 as cv
from config.config_rules import COLOR_CONFIG, MIN_AREA
from ImageProcessing.image import loadImage, mask_image_by_walls, color_correct_with_reference
from ImageProcessing.neutralizeImage import *
from ImageProcessing.detection import detect_objects, detect_boundary_lines, detect_goals_from_lines, detect_goals_from_aruco, detect_robot_from_aruco, detect_boundary_cross, expand_boundaries, smooth_boundaries
from draw.draw import draw_detections,draw_lines,draw_goals,draw_robot,draw_cross_boundary, draw_target
from controller.mainController import *
from config.arucoConfig import aruco_config 
from controller.sceneAdapter import *
from connect import establish_connection, send_controller_command, send_command, establishWriteReadConnection, sendCommandReq
import asyncio

latest_scene = None
latest_frame_data = None

async def camera_task(cam, config, image_rec_active):
    
    loop = asyncio.get_event_loop()
    
    global latest_scene, latest_frame_data, main_controller
    loop = asyncio.get_event_loop()
    
    #trackbars_initialized = False

    while True:
        frame = await loop.run_in_executor(None, capture_frame, cam)
                
        if frame is None:
            continue
        
        frame = normalize_frame(frame)

        
        #if not trackbars_initialized:
        #    setup_trackbars("Camera")
        #    trackbars_initialized = True
            
        #params = get_params("Camera")
        #config = update_config_from_trackbars(config, params)

        detections, final_boundaries, goals, robot_pos, robot_angle, raw_pts, cross_boundary = run_detection(frame, config)
        latest_scene = build_scene_from_camera(detections, goals, robot_pos, robot_angle)
        latest_frame_data = (frame, detections, final_boundaries, goals, robot_angle, raw_pts, cross_boundary)

        target = main_controller.robot.target if main_controller and main_controller.robot else None

        draw_output(
            frame, 
            detections, 
            final_boundaries, 
            goals, robot_angle, 
            raw_pts, 
            cross_boundary, 
            image_rec_active,
            target=main_controller.robot.target if main_controller and main_controller.robot else None
        )

        if cv.waitKey(1) == ord('q'):
            break
        
async def control_task(controller, reader, writer):
    global latest_scene

    while True:
        if latest_scene is None:
            await asyncio.sleep(0.1)  # wait for camera to produce a scene
            continue
        
        
        if reader is None or writer is None:
            return
        response = await run_controller(controller, latest_scene, reader, writer,False)
        
        if response is None:
            print("no response")
            await asyncio.sleep(1.0)
            continue

        parts = response.split("::")
        if parts[0] == "DONE":
            await asyncio.sleep(1.0)  # wait before next command
            
#Live loop of camera
async def image_rec_from_live_video(image_rec_active: bool, runLoop: bool):
    global main_controller
    cam = init_camera()
    if cam is None:
        return

    main_controller = MainController()
    config = COLOR_CONFIG
    reader, writer = await establishWriteReadConnection()

    tasks = [asyncio.create_task(camera_task(cam, config, image_rec_active))]
    
    if runLoop:
        tasks.append(asyncio.create_task(control_task(main_controller, reader, writer)))

    await asyncio.gather(*tasks)

    cam.release()
    cv.destroyAllWindows()

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

def init_camera():
    cam = cv.VideoCapture(1)
    cam.set(cv.CAP_PROP_AUTO_EXPOSURE, 0.25)
    exposure = -1
    cam.set(cv.CAP_PROP_EXPOSURE, exposure)
    
    
    if not cam.isOpened():
        print("Camera could not be opened")
        return None
    return cam

def capture_frame(cam):
    ret, frame = cam.read()
    return frame if ret else None

def run_detection(frame, config):
    #hvid_reference_boks = (10,10, 50, 50)
    #frame = color_correct_with_reference(frame,hvid_reference_boks)
    lines, final_boundaries = detect_boundary_lines(frame)
    final_boundaries = smooth_boundaries(final_boundaries)
    buffered_boundaries = expand_boundaries(final_boundaries, 30)
    image_cropped = mask_image_by_walls(frame, buffered_boundaries)
    detections = detect_objects(image_cropped, config)
    goals = detect_goals_from_aruco(frame)
    robot_pos, robot_angle, raw_pts = detect_robot_from_aruco(image_cropped)
    cross_boundary = detect_boundary_cross(image_cropped)
    return detections, final_boundaries, goals, robot_pos, robot_angle, raw_pts, cross_boundary

def update_config_from_trackbars(config, params):
    wh = params["hsv"]["white"]
    og = params["hsv"]["orange"]
    config["white_ball"]["lower"] = np.array([wh[0], wh[2], wh[4]])
    config["white_ball"]["upper"] = np.array([wh[1], wh[3], wh[5]])
    config["orange_ball"]["lower"] = np.array([og[0], og[2], og[4]])
    config["orange_ball"]["upper"] = np.array([og[1], og[3], og[5]])
    return config

def draw_output(frame, detections, final_boundaries, goals, robot_angle, raw_pts, cross_boundary, image_rec_active, target: Ball = None):
    #hvid_reference_boks = (1000,1000, 5, 5)
    #frame = color_correct_with_reference(frame,hvid_reference_boks)
    
    if image_rec_active:
        output = frame.copy()
        robot_pos_formatted = np.array(raw_pts, dtype=np.int32) if raw_pts is not None else None
        output = draw_detections(frame, detections)
        output = draw_lines(frame, final_boundaries)
        output = draw_goals(frame, goals)
        output = draw_robot(frame, robot_pos_formatted, robot_angle)
        output = draw_cross_boundary(frame, cross_boundary)
        
        if(target is not None):
            output = draw_target(output,target)
        
        cv.imshow('Camera', output)
    else:
        cv.imshow('Camera', frame)
        
def handle_keypresses(image_rec_active, runLoop):
    key = cv.waitKey(1)
    if key == ord('q'):
        return image_rec_active, runLoop, True   # True = quit
    if key == ord('d'):
        image_rec_active = not image_rec_active
        print("Image rec:", image_rec_active)
    if key == ord('s'):
        runLoop = not runLoop
        print("Run loop:", runLoop)
    return image_rec_active, runLoop, False
        
async def run_controller(controller: MainController, scene, reader, writer, sendCommands: bool = True):
    controller.initializeObjects(scene)
    controller.updateRobotState()
    if sendCommands is True and len(controller.commandsQueue) > 0:
        response: str = await send_command(reader, writer, controller.passCommandToRobot())
        return response
    return "DONE::NoCommand"


#Static function get objects from a static image - use for testing.
def image_rec_from_static_image():
    global main_controller
    image_path = "images/test_image_aruco1.png"
    picture = loadImage(image_path)
    main_controller = MainController()
    
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
    
    scene = build_scene_from_camera(detections, goals, robot_pos, robot_angle)
    main_controller.initializeObjects(scene)

    
    output = draw_output(picture, detections, final_boundaries, goals, robot_pos_formatted, robot_angle, cross_boundary)
    
    
    cv.imshow("Detections", output)
    cv.setMouseCallback("Detections", on_mouse_click, param={"image": picture, "hsv": image_hsv})
    
    cv.waitKey(0)
    cv.destroyAllWindows()