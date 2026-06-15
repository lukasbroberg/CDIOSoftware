from utils.getDistance import *
from models.Ball import *

class Robot:
    #Constructor for Robot
    def __init__(self,x1,y1,x2,y2,rotation,state):
        self.x = x1+(x2-x1)/2,
        self.y = y1+(y2-y1)/2
        self.rotation = rotation
        self.target = None
    
    def findNearestBall(self, balls: list[Ball]):
        nearest = None
        nearestDist = None
        for ball in balls:
            d = getDistance(self.x,self.y,ball.x,ball.y)
            if d < nearestDist or nearestDist is None or nearest is None:
                nearestDist=d
                nearest=ball
        return nearest
    
    