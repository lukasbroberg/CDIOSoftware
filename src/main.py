import threading
import numpy as np
import cv2 as cv
from config.config_rules import COLOR_CONFIG, MIN_AREA
from ImageProcessing.image import loadImage, mask_image_by_walls, color_correct_with_reference
from ImageProcessing.detection import detect_objects, detect_boundary_lines, detect_goals_from_lines, detect_goals_from_aruco, detect_robot_from_aruco, detect_boundary_cross
from draw.draw import draw_detections,draw_lines,draw_goals,draw_robot,draw_cross_boundary, draw_target
from controller.mainController import *
from config.arucoConfig import aruco_config 
from controller.sceneAdapter import *
from connect import establish_connection, send_controller_command, send_command, establishWriteReadConnection, sendCommandReq
import asyncio
from controller.systemController import *

async def main():
    await image_rec_from_live_video(image_rec_active=True, runLoop=True)

if __name__ == "__main__":
    asyncio.run(main())    