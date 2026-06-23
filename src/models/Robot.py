from utils.getDistance import *
from models.Ball import *
from utils.getAngle import *
from models.Robot_config import *
from models.Ball import *
from models.Goal import *

class Robot:
    #Constructor for Robot
    def __init__(self,x,y,rotation,state):
        self.x = x
        self.y = y
        self.rotation = rotation
        self.target = None
        self.pickedUpBalls = 0
        self.deliveredBalls = 0
    
    def findNearestBall(self, balls: list[Ball]):
        nearest = None
        nearestDist = None

        for i, ball in enumerate(balls):
            d = getDistance(self.x,self.y,ball.x,ball.y,26,0)
            #Check if the ball is too close - might be the robot itself then.
            if(d<ROBOTCONFIG['leastDistanceToBall'] and len(balls)>1):
                continue
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
        
    def setTarget(self, target):
        import copy
        _target = copy.copy(target)
        self.target = _target
        self.target.x = _target.x + ROBOTCONFIG['targetOffsetX']
        self.target.y = _target.y + ROBOTCONFIG['targetOffsetY']
    
    def getDeltaAngle(self, targetAngle_deg):
        if targetAngle_deg is None:
            return None
        
        
        # 3. FIX THE FLIPPED MARKER: Add 180 degrees because the ArUco 
        # thinks the back of the robot is the front.
        robot_deg = (self.rotation + 180) % 360
        
        # 4. Find the shortest steering delta
        delta = (targetAngle_deg - robot_deg ) % 360 - 180
        return delta

    def isFacingTarget(self, tolerance = ROBOTCONFIG["angleTolerance"]):
        if self.target is None:
            return False
        isFacing = abs(self.getDeltaAngle(getAngle(self.x,self.y,self.target.x,self.target.y,26,0))) <= tolerance;
        return isFacing

    