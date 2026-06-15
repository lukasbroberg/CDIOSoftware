from utils.getDistance import *
from models.Ball import *

class Robot:
    #Constructor for Robot
    def __init__(self,x,y,rotation,state):
        self.x = x,
        self.y = y
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
    
    