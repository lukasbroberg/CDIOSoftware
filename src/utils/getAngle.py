import math
def getAngle(x1, y1, x2, y2):
    return math.atan2(y2-y1,x2-x1)*(180/math.pi)

#def getAngleDelta()