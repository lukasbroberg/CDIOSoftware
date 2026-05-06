import math
from collections import deque

DISTANCE_THRESHOLD = 80
ANGLE_THRESHOLD = 10
GOAL_THRESHOLD = 50

class MainController:
    def __init__(self):
        self.deliveredBalls = 0
        self.commands = deque()
        self.balls = []
        self.robot = {}
        self.goalB = {}
        self.currentTarget = None
        self.currentState = "SelectTarget"

    def initializeObjects(self, scene):
        self.robot = scene["robot"]
        self.goalB = scene["goal_b"]
        self.balls = []

        if scene["orange_ball"] is not None:
            self.balls.append({
                "type": "orange",
                "position": scene["orange_ball"]
            })

        for ball in scene["white_balls"]:
            self.balls.append({
                "type": "white",
                "position": ball
            })

        print("Robot:", self.robot)
        print("Goal B:", self.goalB)
        print("Balls:", self.balls)

    def findOrangeBall(self):
        for ball in self.balls:
            if ball["type"] == "orange":
                return ball
        return None

    def findNearestBall(self):
        if len(self.balls) == 0:
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

    def selectTarget(self):
        orange_ball = self.findOrangeBall()

        if orange_ball is not None:
            self.currentTarget = orange_ball
            self.currentState = "DriveToBall"
            return orange_ball

        nearest_ball = self.findNearestBall()

        if nearest_ball is not None:
            self.currentTarget = nearest_ball
            self.currentState = "DriveToBall"
            return nearest_ball

        self.currentTarget = None
        self.currentState = "Finished"
        return None

    def distanceToTarget(self):
        if self.currentTarget is None:
            return None

        return math.hypot(
            self.currentTarget["position"]["x"] - self.robot["x"],
            self.currentTarget["position"]["y"] - self.robot["y"]
        )

    def angleToTarget(self):
        if self.currentTarget is None:
            return None

        dx = self.currentTarget["position"]["x"] - self.robot["x"]
        dy = self.currentTarget["position"]["y"] - self.robot["y"]

        target_angle = math.degrees(math.atan2(dy, dx))
        robot_heading = self.robot.get("heading", 0)

        angle_diff = target_angle - robot_heading

        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360

        return angle_diff

    def isAtGoal(self):
        if self.currentTarget is None:
            return False

        distance = math.hypot(
            self.goalB["x"] - self.currentTarget["position"]["x"],
            self.goalB["y"] - self.currentTarget["position"]["y"]
        )

        return distance < GOAL_THRESHOLD

    def decideNextAction(self):
        print("Current state:", self.currentState)

    # SELECT TARGET
        if self.currentState == "SelectTarget":
            target = self.selectTarget()

            if target is None:
                self.currentState = "Finished"
                self.commands.append("Stop")
                return "Stop"

            return "Continue"

    # DRIVE TO BALL
        elif self.currentState == "DriveToBall":
            distance = self.distanceToTarget()
            print("Distance to target:", distance)

            if distance > DISTANCE_THRESHOLD:
                self.commands.append("DriveForward")
                return "DriveForward"

            self.currentState = "AlignWithBall"
            return "Continue"

    # ALIGN WITH BALL
        elif self.currentState == "AlignWithBall":
            angle = self.angleToTarget()
            print("Angle to target:", angle)

            if abs(angle) > ANGLE_THRESHOLD:
                if angle > 0:
                    self.commands.append("TurnLeft")
                    return "TurnLeft"
                else:
                    self.commands.append("TurnRight")
                    return "TurnRight"

            self.currentState = "PushBallToGoal"
            return "Continue"

    # PUSH BALL TO GOAL
        elif self.currentState == "PushBallToGoal":
            if self.isAtGoal():
                self.currentState = "DeliverBall"
                return "Continue"

            self.commands.append("PushForward")
            return "PushForward"

    # DELIVER BALL
        elif self.currentState == "DeliverBall":
            self.deliveredBalls += 1
            print("Delivered balls:", self.deliveredBalls)

            if self.currentTarget in self.balls:
                self.balls.remove(self.currentTarget)

            self.currentTarget = None
            self.currentState = "SelectTarget"
            return "Continue"

    # FINISHED
        elif self.currentState == "Finished":
            self.commands.append("Stop")
            return "Stop"

    def passCommandToRobot(self):
        if len(self.commands) == 0:
            return None

        command = self.commands.popleft()
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