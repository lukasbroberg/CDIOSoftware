from collections import *
from math import *
from collections import deque
from collections import *
from models.Robot import *
from utils.getDistance import *

GOAL_THRESHOLD = 50
DISTANCE_THRESHOLD = 80
ANGLE_THRESHOLD = 10

class MainController():
    def __init__(self):
        self.commandsQueue = ["FORWARD_TIMED::2.0"] #Commands for the robot as a queue
        self.balls = None
        self.robot: Robot = None
        self.boundaries = None
        self.cross = None
        self.smallGoal = None
        self.largeGoal = None
        self.currentState = None
        
    def initializeObjects(self, scene):
        robot_data = scene["robot"]
        if robot_data is not None:
            
            if self.robot is None:
                self.robot = Robot (
                    x=robot_data["x"],
                    y=robot_data["y"],
                    rotation=robot_data["rotation"],
                    state=None
                )
            else:
                self.robot.x = robot_data["x"]
                self.robot.y = robot_data["y"]
                self.robot.rotation = robot_data["rotation"]
            
        
        self.goalB = scene["goal_b"]
        self.balls = []

        if scene["orange_ball"] is not None:
            for ball in scene["orange_ball"]:
                self.balls.append(
                    Ball(
                        ball["x"],
                        ball["y"],
                        True
                    )
                )

        if scene["white_balls"] is not None:
            for ball in scene["white_balls"]:
                self.balls.append(
                    Ball(
                        ball["x"],
                        ball["y"],
                        False
                    )
                )
    
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
            
    def findOrangeBall(self):
        for ball in self.balls:
            if ball["type"] == "orange":
                return ball
        return None
    
    def findNearestWhiteBall(self):
        if len(self.balls) == 0:
            return None

        return min(
            self.balls,
            key=lambda ball: math.hypot(
                ball["position"]["x"] - self.robot.x,
                ball["position"]["y"] - self.robot.y
            )
        )

    def distanceToTarget(self):
        if self.currentTarget is None:
            return None

        return math.hypot(
            self.currentTarget["position"]["x"] - self.robot["x"],
            self.currentTarget["position"]["y"] - self.robot["y"]
        )

    def isAtGoal(self):
        if self.currentTarget is None:
            return False

        distance = math.hypot(
            self.goalB["x"] - self.currentTarget["position"]["x"],
            self.goalB["y"] - self.currentTarget["position"]["y"]
        )

        return distance < GOAL_THRESHOLD

    def updateRobotState(self):
        
        if self.robot is None:
            print("No robot detected, skipping state update")
            return
        
        if self.currentState is None:
            self.currentState = "FindNearestBall"
            return
    
        match(self.currentState):
            #State "FindNearestBall"
            case "FindNearestBall":
                if self.robot.target is not None:
                    self.currentState="AlignWithTarget"
                    raise "Changed state"
                
                self.robot.target = self.robot.findNearestBall(self.balls)
                self.currentState = "AlignWithTarget"
                
            #State align to target
            case "AlignWithTarget":
                
                if self.robot.target is None:
                    self.currentState = "FindNearestBall"
                    raise "Changed state"
                
                targetAngle = getAngle(self.robot.x,
                                       self.robot.y,
                                       self.robot.target.x,
                                       self.robot.target.y
                )
                delta = self.robot.getDeltaAngle(targetAngle)
                if(delta>0):
                    self.commandsQueue.append("LEFT_TIMED::1.0") #TODO CALCULATE TIME
                else:
                    self.commandsQueue.append("RIGHT_TIMED::1.0") #TODO CALCULATE TIME
                
            case "MoveTowardsTarget":
                d = getDistance(self.robot.x,self.robot.y,self.robot.target.x,self.robot.target.y)
                
                if not self.robot.isFacingTarget(getAngle(self.robot.x,self.robot.y,self.robot.target.x,self.robot.target.y)):
                    self.currentState="AlignWithTarget"
                    raise "changed state"
                
                if abs(d)<ROBOTCONFIG["distanceTolerance"]:
                    if self.robot.target is Ball:
                        self.currentState = "PickupBall"
                    else:
                        self.currentState = "DropBall"
                
                self.commandsQueue.append("FORWARD_TIMED::2.0") #TODO Calculate time
                
            case _:
                self.currentState = "Stop"

    def passCommandToRobot(self):
        if len(self.commandsQueue) == 0:
            return None

        command = self.commandsQueue.pop(0)
        print("[COMMAND]:", command)
        return command
    
    def simulateStep(self, action):
        if action == "DriveForward" and self.currentTarget is not None:
            target_x = self.currentTarget["position"]["x"]
            target_y = self.currentTarget["position"]["y"]

            robot_x = self.robot["x"]
            robot_y = self.robot["y"]

            dx = target_x - robot_x
            dy = target_y - robot_y

            dist = math.hypot(dx, dy)

            if dist > 0:
                step = min(10, dist)
                self.robot["x"] += step * dx / dist
                self.robot["y"] += step * dy / dist

        elif action == "TurnLeft":
            self.robot["heading"] += 10

        elif action == "TurnRight":
            self.robot["heading"] -= 10

        elif action == "PushForward" and self.currentTarget is not None:
            self.robot["x"] = self.currentTarget["position"]["x"] - 20
            self.robot["y"] = self.currentTarget["position"]["y"] - 20
            target_x = self.goalB["x"]
            target_y = self.goalB["y"]

            ball_x = self.currentTarget["position"]["x"]
            ball_y = self.currentTarget["position"]["y"]

            dx = target_x - ball_x
            dy = target_y - ball_y

            dist = math.hypot(dx, dy)

            if dist > 0:
                step = min(20, dist)
                self.currentTarget["position"]["x"] += step * dx / dist
                self.currentTarget["position"]["y"] += step * dy / dist

        print("Robot after step:", self.robot)

    def findOrangeBall(self):
        for ball in self.balls:
            if ball["type"] == "orange":
                return ball
        return None
