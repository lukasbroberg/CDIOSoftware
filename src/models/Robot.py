from utils.getDistance import *
from models.Ball import *
from utils.getAngle import *
from models.Robot_config import *
from models.Ball import *

class Robot:
    #Constructor for Robot
    def __init__(self,x,y,rotation,state):
        self.x = x
        self.y = y
        self.rotation = rotation
        self.target = None
        self.pickedUpBalls = 0
    
    def findNearestBall(self, balls: list[Ball]):
        nearest = None
        nearestDist = None

        for i, ball in enumerate(balls):
            d = getDistance(self.x,self.y,ball.x,ball.y)
            if nearest is None or nearestDist is None:
                nearestDist=d
                nearest=ball
            
            if d < nearestDist:
                nearestDist=d
                nearest=ball
                print("New nearest", nearest.x, nearest.y)
        return nearest
    
    
    #def findNearestBall(self, balls):
        if len(balls) == 0:
            return None

        robot_x = self.robot["x"]
        robot_y = self.robot["y"]

        return min(
            self.balls,
            key=lambda ball: math.hypot(
                ball["position"]["x"] - robot_x,
                ball["position"]["y"] - robot_y
            )
        )
    
    def getDeltaAngle(self, targetAngle):
        if targetAngle is None:
            return None
        
        delta = (targetAngle - self.rotation) % 360;
        if (delta > 180): delta -= 360;
        if (delta < -180): delta += 360;
        return delta

    def isFacingTarget(self, targetAngle, tolerance = ROBOTCONFIG["angleTolerance"]):
        return abs(self.getDeltaAngle(targetAngle)) <= tolerance;

    def setTarget(self, target):
        self.target = target

    