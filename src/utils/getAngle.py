import math
from utils.perspectiveCorrection import pixel_to_world, HEIGHT_ROBOT, HEIGHT_FLOOR

def getAngle(x1, y1, x2, y2, h1 = 0.0, h2 = 0.0):
    """Calculates the absolute ground-plane angle from item 1 to item 2"""
    wx1, wy1 = pixel_to_world(x1, y1, object_height_cm=h1)
    wx2, wy2 = pixel_to_world(x2, y2, object_height_cm=h2)
    return math.degrees(math.atan2(wy2 - wy1, wx2 - wx1))