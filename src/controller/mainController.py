from collections import *

class MainController():
    commands = deque() #Commands for the robot as a queue
    balls = []
    robot = {}
    boundary = []
    smallGoal = {}
    BigGoal = {}
    
    ## Instantiates new objects
    def initializeObjects(ColorDetection):
        for det in ColorDetection:
            print(
            f"[{det['label']}]"
            f"centroid=({[det['centroid'][0]]},{[det['centroid'][1]]})"
            f"bbox={det['bbox']}"
            f"area={det['area']:.0f}px"
        )
        pass
    
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