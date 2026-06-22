import math
from utils.perspectiveCorrection import pixel_to_world, HEIGHT_ROBOT, HEIGHT_FLOOR

def getDistance(x1, y1, h1, x2, y2, h2):
    """Calculates real world ground distance between two objects of different heights"""
    wx1, wy1 = pixel_to_world(x1, y1, object_height_cm=h1)
    wx2, wy2 = pixel_to_world(x2, y2, object_height_cm=h2)
    return math.hypot(wx2 - wx1, wy2 - wy1)