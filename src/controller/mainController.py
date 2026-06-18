from collections import *
from math import *
from collections import deque
from collections import *
from models.Robot import *
from utils.getDistance import *
from models.Goal import *

GOAL_THRESHOLD = 50
DISTANCE_THRESHOLD = 80
ANGLE_THRESHOLD = 10

class MainController():
    def __init__(self):
        self.commandsQueue = [] #Commands for the robot as a queue
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
                self.robot.rotation = robot_data["rotation"]-90
        if self.largeGoal is None:
            self.largeGoal = Goal(scene["goal_b"]["x"], scene["goal_b"]["y"])
        
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
        print("robot pos: ", self.robot.x, self.robot.y)
        
        print("---State: " + str(self.currentState) + "---")
        
        if self.robot is None:
            print("No robot detected, skipping state update")
            return
        
        if self.currentState is None:
            self.currentState = "FindNearestBall"
            return
        
        targetAngle = None
        if self.robot.target is not None:
            targetAngle = getAngle(self.robot.x,
                                   self.robot.y,
                                   self.robot.target.x,
                                   self.robot.target.y)
    
        match(self.currentState):
            #State "FindNearestBall"
            case "FindNearestBall":
                if self.robot.target is not None:
                    self.currentState="AlignWithTarget"
                    raise "Changed state"
                
                self.robot.target = self.robot.findNearestBall(self.balls)
                print("Target: ", self.robot.target.x, self.robot.target.y)
                self.currentState = "AlignWithTarget"
                
            #State align to target
            case "AlignWithTarget":
                if self.robot.target is None:
                    self.currentState = "FindNearestBall"
                    print("!!changed state!!")
                    return
                
                print("Target angle", targetAngle)
                print("Robot angle", self.robot.rotation)
                
                if self.robot.isFacingTarget():
                    self.currentState="MoveTowardsTarget"
                    print("Aligned! Switching to MoveTowardsTarget")
                    return
                
                delta = self.robot.getDeltaAngle(targetAngle)
                print("Delta", delta)
                if(delta<0):
                    turnTime = abs(delta)/360 * 6.5
                    commandString = "LEFT_TIMED::"+str(abs(turnTime))
                    self.commandsQueue.append(commandString) #TODO CALCULATE TIME
                else:
                    turnTime = abs(delta)/360 * 6.5
                    commandString = "RIGHT_TIMED::"+str(abs(turnTime))
                    self.commandsQueue.append(commandString) #TODO CALCULATE TIME
                
            case "MoveTowardsTarget":
                
                if self.robot.target is None:
                    self.currentState = "FindNearestBall"
                    return
                
                d = getDistance(self.robot.x,self.robot.y,self.robot.target.x,self.robot.target.y)
            
                print("distance", str(d))
                
                if not self.robot.isFacingTarget():
                    self.currentState="AlignWithTarget"
                    print("!!NOT LOOKING AT TARGET changed state!!")
                    return
                
                if abs(d)<ROBOTCONFIG["distanceTolerance"]:
                    if self.robot.target is Ball:
                        self.currentState = "PickupBall"
                    else:
                        self.currentState = "DropBall"
                
                self.commandsQueue.append("FORWARD_TIMED::2.0") #TODO Calculate time
            
            case "PickupBall":
                d = getDistance(self.robot.x,self.robot.y,self.robot.target.x,self.robot.target.y)
                #If not in angle to pickup ball
                if not self.robot.isFacingTarget():
                    self.currentState="AlignWithTarget"
                    raise "changed state"
                
                #If too far away
                if abs(d)>ROBOTCONFIG["distanceTolerance"]:
                    if self.robot.target is Ball:
                        self.currentState = "moveTowardsTarget"

                self.commandsQueue.append("COLLECT")
                self.robot.pickedUpBalls += 1
                print("picked up balls", self.robot.pickedUpBalls)
                
                if self.robot.pickedUpBalls<3:
                    self.currentState = "FindNearestBall"
                    self.robot.target = None
                else:
                    self.robot.target = self.largeGoal
                    self.currentState = "AlignWithTarget"
            
            case "DropBall":
                d = getDistance(self.robot.x,self.robot.y,self.robot.target.x,self.robot.target.y)
                #If too far away
                if abs(d)>ROBOTCONFIG["distanceTolerance"]:
                    if self.robot.target is Ball:
                        self.currentState = "moveTowardsTarget"
                
                if not self.robot.isFacingTarget(getAngle(self.robot.x,self.robot.y,self.robot.target.x,self.robot.target.y)):
                    self.currentState="AlignWithTarget"
                    raise "changed state"

                self.commandsQueue.append("RELEASE")
                
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
