import math
def getAngle(x1, y1, x2, y2):
    return math.atan2(y1-y2,x2-x1)*(180/math.pi)