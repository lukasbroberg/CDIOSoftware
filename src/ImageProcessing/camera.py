import cv2 as cv
from config.config_rules import COLOR_CONFIG, MIN_AREA
from ImageProcessing.image import loadImage, mask_image_by_walls
from ImageProcessing.detection import detect_objects, detect_boundary_lines, detect_goals_from_lines, detect_goals_from_aruco, detect_robot_from_aruco, detect_boundary_cross
from asyncio import *

async def run(scene_queue: asyncio.Queue, loop):
    def _capture():
        cam = cv.VideoCapture(1)
        while True:
            ret, frame = cam.read()
            if frame is None:
                continue
            scene = process_frame(frame)  # all your vision logic here
            asyncio.run_coroutine_threadsafe(scene_queue.put(scene), loop)
            if cv.waitKey(1) == ord('q'):
                break
        cam.release()
    
    await loop.run_in_executor(None, _capture)
    
def process_frame(frame, config):
    detections = detect_objects(frame, config)
    lines, final_boundaries = detect_boundary_lines(frame)
    image_cropped_by_boundaries = mask_image_by_walls(frame,final_boundaries)
    goals = detect_goals_from_aruco(frame)
    robot_pos, robot_angle, raw_pts = detect_robot_from_aruco(image_cropped_by_boundaries)
    cross_boundary = detect_boundary_cross(image_cropped_by_boundaries)
    return detections, final_boundaries, goals, robot_pos, robot_angle, cross_boundary
        