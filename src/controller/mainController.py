from collections import *
from models.Robot import *

class MainController():
    def __init__(self):
        self.commands = deque() #Commands for the robot as a queue
        self.balls = None
        self.robot: Robot = None
        self.boundaries = None
        self.cross = None
        self.smallGoal = None
        self.largeGoal = None
    
    def updateBalls(self, _balls):
        if _balls is not None:
            self.balls = _balls;
        
    def updateRobot(self, robot: Robot):
        if robot is not None:
            self.robot = robot
    
    def updateBoundaries(self, boundaries, crossBoundary):
        if boundaries is not None:
            self.boundaries = boundaries
        
    def updateCross(self, cross):
        if cross is not None:
            self.cross=cross
    
    def updateSmallGoal(self, smallGoal):
        if smallGoal is not None:
            self.smallGoal = smallGoal
    
    def updateLargeGoal(self, largeGoal):
        if largeGoal is not None:
            self.largeGoal = largeGoal
        
    def findObjects():
        pass

    #Algorithm for finding the nearest ball to the robot
    def findNearestBall():
        pass
    
    def FindOrangeBall():
        pass
    
    #Passes commands to the actual robot
    def passCommandToRobot():
        pass