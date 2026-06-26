<<<<<<< HEAD
<<<<<<< HEAD
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
=======
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
>>>>>>> 1a6062c (Finish robot controller state machine)

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
=======
import math
from collections import deque
from models.Robot import Robot
from models.Ball import Ball
from models.Goal import Goal
from models.Point import Point
from models.Robot_config import ROBOTCONFIG
from utils.getDistance import getDistance
from utils.getAngle import getAngle
from models.TrackedObjects import *
from utils.perspectiveCorrection import PIXELS_PER_CM_FLOOR
from utils.pathPlanner import *

# ── How many balls to collect before heading to the goal ─────────────────────
BALLS_PER_TRIP = 5

# The controller deliberately has only action states.  What it is moving
# towards is kept separately as targetKind, rather than duplicating every
# action for balls, waypoints and the goal.
FIND_BALL = "FindBall"
ALIGN_TARGET = "AlignTarget"
MOVE_TO_TARGET = "MoveToTarget"
PICKUP_BALL = "PickupBall"
DROP_BALL = "DropBall"
STOP = "Stop"

BALL_TARGET = "ball"
DROPOFF_TARGET = "dropoff"
GOAL_TARGET = "goal"

# ── Drive calibration ─────────────────────────────────────────────────────────
# Measured from logs: robot moves ~47 px/s, so 100 px takes ~2.155 s.
# Tune this if your surface or battery level changes.
SECONDS_PER_100_PX = 2.155/2.5


def _drive_time(cm: float) -> float:
    equivalent_pixels = abs(cm) * PIXELS_PER_CM_FLOOR
    return round(equivalent_pixels / 100.0 * SECONDS_PER_100_PX, 1)


def _turn_time(degrees: float) -> float:
    return round(abs(degrees) / 360.0 * ROBOTCONFIG["fullTurnTime"], 1)


class MainController:
    """
    State machine that maps vision data → robot commands.

    States
    ──────
    FindBall        – pick the best ball and plan a path
    AlignTarget     – rotate to face the current target
    MoveToTarget    – drive to a ball, waypoint or drop-off point
    PickupBall      – collect a ball
    DropBall        – release collected balls
    Stop            – nothing left to do
    """

    def __init__(self):
        self.commandsQueue: list[str] = ["COLLECT"]
        self.balls:         list[Ball] = []
        self.robot:         Robot | None = None
        self.largeGoal:     Goal  | None = None
        self.smallGoal:     Goal  | None = None
        self.currentState:  str   | None = None
        self.boundaries:    list | None = None
        self.tracker = ObjectTracker(max_distance=150)
        self.currentPath = []
        self.cross = None
        self.targetKind: str | None = None
        self.collectedTargetIds: set[int] = set()

    # ─────────────────────────────────────────────────────────────────────────
    # Scene initialisation (called every frame by main.py)
    # ─────────────────────────────────────────────────────────────────────────

    def initializeObjects(self, scene: dict):
        robot_data = scene.get("robot")
        if robot_data is not None:
            if self.robot is None:
                self.robot = Robot(
                    x=robot_data["x"],
                    y=robot_data["y"],
                    rotation=robot_data["rotation"] - 90,
                    state=None,
                )
            else:
                self.robot.x        = robot_data["x"]
                self.robot.y        = robot_data["y"]
                self.robot.rotation = robot_data["rotation"] - 90

        if self.largeGoal is None and scene.get("goal_large") is not None:
            self.largeGoal = Goal(scene["goal_large"]["x"], scene["goal_large"]["y"])

        if self.smallGoal is None and scene.get("goal_small") is not None:
            self.smallGoal = Goal(scene["goal_small"]["x"], scene["goal_small"]["y"])


        raw_balls = []
        for b in (scene.get("orange_ball") or []):
            raw_balls.append(Ball(b["x"], b["y"], True))
        for b in (scene.get("white_balls") or []):
            raw_balls.append(Ball(b["x"], b["y"], False))
        self.balls = self.tracker.update(raw_balls)
        
        #Update robot's target to follow target position
        #if self.robot and isinstance(self.robot.target, TrackedObject):
        #    target_id = self.robot.target.id
        #    matched = self.tracker.tracked.get(target_id)
        #    if matched:
        #        print(f"[DEBUG] before update target=({self.robot.target.x:.0f},{self.robot.target.y:.0f}) matched=({matched.x:.0f},{matched.y:.0f})")
        #        self.robot.setTarget(matched)
        #        print(f"[DEBUG] after update target=({self.robot.target.x:.0f},{self.robot.target.y:.0f})")
            
        if scene.get("boundaries") is not None:
            _boundaries = scene.get("boundaries")
            top_wall    = _boundaries[0]
            bottom_wall = _boundaries[1]
            left_wall   = _boundaries[2]
            right_wall  = _boundaries[3]

            self.boundaries = {
                "right":  int(right_wall[0]),   
                "left":   int(left_wall[0]),    
                "top":    int(top_wall[1]),     
                "bottom": int(bottom_wall[1]), 
            }
            
        if scene.get("cross") is not None:
            self.cross = scene.get("cross")
            
    # Gets the robot's true angle to target on the floor
    def _angle_to_target(self) -> float | None:
        t = self.robot.target
        if t is None:
            return None
        
        # 1. Map the robot's top pixel point down to its true ground-floor cm coordinate
        rx_cm, ry_cm = pixel_to_world(self.robot.x, self.robot.y, object_height_cm=26.0)
        
        # 2. Map the target's pixel point down to its ground-floor cm coordinate
        tx_cm, ty_cm = pixel_to_world(t.x, t.y, object_height_cm=0.0)
        
        # 3. Compute the pure ground angle using standard trigonometry 
        return math.degrees(math.atan2(ty_cm - ry_cm, tx_cm - rx_cm))

    # Gets the robot's true distance to target on the floor
    def _distance_to_target(self) -> float | None:
        t = self.robot.target
        if t is None:
            return None
            
        # 1. Map robot top to real-world floor centimeters
        rx_cm, ry_cm = pixel_to_world(self.robot.x, self.robot.y, object_height_cm=26.0)
        
        # 2. Map target to real-world floor centimeters
        tx_cm, ty_cm = pixel_to_world(t.x, t.y, object_height_cm=0.0)
        
        # 3. Return the real ground distance
        return abs(math.hypot(tx_cm - rx_cm, ty_cm - ry_cm))

    def _is_forward_target(self) -> bool | None:
        t = self.robot.target
        if t is None:
            return None

        rx_cm, ry_cm = pixel_to_world(self.robot.x, self.robot.y, object_height_cm=26.0)
        tx_cm, ty_cm = pixel_to_world(t.x, t.y, object_height_cm=0.0)

        angle_to_target = math.degrees(math.atan2(ty_cm - ry_cm, tx_cm - rx_cm))
        delta = (angle_to_target - self.robot.rotation + 180) % 360 - 180

        # Target is "forward" if it's within 90° of the robot's heading
        return abs(delta) < 90

    #Returns the nearest Ball - TODO add compatibility to find orange balls
    def _find_best_ball(self) -> Ball | None:
        locked_edge_target = self._locked_edge_target()
        if locked_edge_target is not None:
            return locked_edge_target

        balls = self._available_balls()
        if not balls:
            return None
        return self.robot.findNearestBall(balls)
        #orange = next((b for b in self.balls if b.isOrange), None)
        #if orange:
        #    return orange
    
    def _find_best_white_ball(self) -> Ball | None:
        locked_edge_target = self._locked_edge_target()
        if locked_edge_target is not None and not locked_edge_target.isOrange:
            return locked_edge_target

        white_balls = []
        for ball in self._available_balls():
            if not ball.isOrange:
                white_balls.append(ball)
        
        if white_balls is None or len(white_balls)<=0:
            return self._find_best_ball()
        
        return self.robot.findNearestBall(white_balls)
    
    def _find_best_orange_ball(self) -> Ball | None:
        locked_edge_target = self._locked_edge_target()
        if locked_edge_target is not None and locked_edge_target.isOrange:
            return locked_edge_target

        orange_balls = []
        for ball in self._available_balls():
            if ball.isOrange:
                orange_balls.append(ball)
        if orange_balls is None or len(orange_balls) == 0:
            return self._find_best_ball()
        return self.robot.findNearestBall(orange_balls)

    def _locked_edge_target(self) -> Ball | None:
        """Keep collecting the selected edge ball instead of switching target.

        Edge-risk should change *how* we approach/pick up the ball, not whether
        we keep chasing it.  Without this lock the controller can keep selecting
        a different nearby ball while the robot is already committed to an edge
        pickup, which creates path churn.
        """
        if self.targetKind != BALL_TARGET or not self.currentPath:
            return None

        target = self.currentPath[-1]
        if getattr(target, "id", None) in self.collectedTargetIds:
            return None
        if self._is_in_cross_ignore_zone(target):
            return None
        if not self._is_near_boundary(target):
            return None
        return target

    def _available_balls(self) -> list[Ball]:
        """Ignore a tracked ball after collecting it until vision removes it."""
        return [
            ball for ball in self.balls
            if getattr(ball, "id", None) not in self.collectedTargetIds
            and not self._is_in_cross_ignore_zone(ball)
            and getDistance(
                self.robot.x, self.robot.y, 26,
                ball.x, ball.y, 0,
            ) >= ROBOTCONFIG["minimumTargetDistance"]
        ]

    def _is_in_cross_ignore_zone(self, ball: Ball) -> bool:
        if self.cross is None:
            return False
        return distance(ball, self.cross) <= ROBOTCONFIG["crossBallIgnoreRadius"]

    def _is_near_boundary(self, item, margin_cm: float | None = None) -> bool:
        if self.boundaries is None or item is None:
            return False

        margin_cm = ROBOTCONFIG["edgeBallSafetyMargin"] if margin_cm is None else margin_cm
        margin_px = margin_cm * PIXELS_PER_CM_FLOOR
        return not (
            self.boundaries["left"] + margin_px <= item.x <= self.boundaries["right"] - margin_px
            and self.boundaries["top"] + margin_px <= item.y <= self.boundaries["bottom"] - margin_px
        )

    def _edge_approach_point(self, target: Ball | Point) -> Point | None:
        """Return a safer inside-field waypoint before collecting an edge ball."""
        if self.boundaries is None or not self._is_near_boundary(target):
            return None

        margin_px = ROBOTCONFIG["edgeBallApproachMargin"] * PIXELS_PER_CM_FLOOR
        safe_x = max(
            self.boundaries["left"] + margin_px,
            min(self.boundaries["right"] - margin_px, target.x),
        )
        safe_y = max(
            self.boundaries["top"] + margin_px,
            min(self.boundaries["bottom"] - margin_px, target.y),
        )

        if math.isclose(safe_x, target.x) and math.isclose(safe_y, target.y):
            return None

        approach = Point(safe_x, safe_y)
        approach.is_edge_approach = True
        print(
            f"[PATH] edge ball; approach=({safe_x:.0f},{safe_y:.0f}) "
            f"before target=({target.x:.0f},{target.y:.0f})"
        )
        return approach

    def _planPathTo(self, target: Ball | Point, allow_edge_approach: bool = False):
        edge_approach = self._edge_approach_point(target) if allow_edge_approach else None
        path_target = edge_approach or target
        waypoints = build_path(
            self.robot,
            path_target,
            cross=self.cross,
            field=self.boundaries
        )
        self.currentPath = [
            Point(p["x"], p["y"]) if isinstance(p, dict) else p
            for p in waypoints
        ]
        if edge_approach is not None:
            self.currentPath.append(edge_approach)
        # The real tracked object must always be last.  A waypoint can never
        # trigger pickup or release.
        self.currentPath.append(target)
        self.robot.target = self.currentPath[0]

    #Queue commands
    def _enqueue_turn(self, delta: float):
        t = _turn_time(delta)
        direction = "LEFT_TIMED" if delta < 0 else "RIGHT_TIMED"
        self.commandsQueue.append(f"{direction}::{t}")

    def _enqueue_forward(self, cm: float):
        self.commandsQueue.append(f"FORWARD_TIMED::{_drive_time(cm)}")

    def _enqueue_backward(self, cm: float):
        self.commandsQueue.append(f"BACKWARD_TIMED::{_drive_time(cm)}")
        
    def _enqueue_collect(self):
        self.commandsQueue.append(f"COLLECT")
        
    def _enqueue_opendoors(self):
        self.commandsQueue.append(f"OPENDOOR")
        
    def _enqueue_closedoors(self):
        self.commandsQueue.append(f"CLOSEDOOR")
    
        
    def _go_to_state(self, state: str, reason: str = ""):
        tag = f" ({reason})" if reason else ""
        print(f"[STATE] {self.currentState} → {state}{tag}")
        self.currentState = state


    # checks whether or not the robot is too close to the boundary
    def is_danger_zone(self, item):
        if self.boundaries is None or item is None:
            return False

        print(f"[DANGER CHECK] pos=({item.x:.0f},{item.y:.0f}) boundaries={self.boundaries} margin={ROBOTCONFIG['maxDistToBoundary']}")
        return self._is_near_boundary(item, ROBOTCONFIG["maxDistToBoundary"])

    def _go_to_drop_off_ball(self):
        if self.smallGoal is None:
            return False

        dropOffPoint = Point(
            self.smallGoal.x+ROBOTCONFIG["goalDropOffOffset"],
            self.smallGoal.y
        )
        self._planPathTo(dropOffPoint)
        self.targetKind = DROPOFF_TARGET
        self._go_to_state(ALIGN_TARGET, "heading to drop-off")
        return True

    def _advance_path(self) -> bool:
        """Select the next waypoint. Returns False after the final target."""
        if self.currentPath:
            self.currentPath.pop(0)
        if not self.currentPath:
            return False
        self.robot.target = self.currentPath[0]
        return True

    def _start_goal_alignment(self):
        if self.smallGoal is None:
            self.robot.target = None
            self.targetKind = None
            self._go_to_state(FIND_BALL, "goal lost")
            return
        self.robot.setTarget(self.smallGoal)
        self.targetKind = GOAL_TARGET
        self._go_to_state(ALIGN_TARGET, "at drop-off point")

    def _move_settings(self) -> tuple[float, float]:
        """Return (arrival threshold, max drive distance) for the current target."""
        is_waypoint = len(self.currentPath) > 1
        if self.targetKind == BALL_TARGET:
            return (ROBOTCONFIG["waypointArrivalTolerance"] if is_waypoint
                    else ROBOTCONFIG["collectOffset"], 30.0)
        return (ROBOTCONFIG["waypointArrivalTolerance"] if is_waypoint else 5.0, 15.0)

    def _has_drifted(self) -> bool:
        """Avoid turn/move oscillation from small camera-heading changes."""
        return not self.robot.isFacingTarget(ROBOTCONFIG["closeRangeTolerance"])
        
        
    # State machine
    # The state is updated after each succesful command.
    def updateRobotState(self):
        if self.robot is None:
            print("[STATE] No robot detected – skipping")
            return

        # Don't advance state while commands are still pending. The robot
        # hasn't finished executing them yet so position/heading are stale.
        if self.commandsQueue:
            print(f"[STATE] Queue not empty ({len(self.commandsQueue)} pending) – skipping update")
            return
        
        if self.currentState is None:
            self._go_to_drop_off_ball()
            #self._go_to_state("FindBall", "init")
            return

        #Log each state
        print(
            f"[STATE] {self.currentState} | "
            f"pos=({self.robot.x:.0f},{self.robot.y:.0f}) "
            f"rotation={self.robot.rotation:.1f}° "
            f"carried={self.robot.pickedUpBalls}"
            f"path={self.currentPath}",
        )

        match self.currentState:

            # 1. Choose a target ball
            case _ if self.currentState == FIND_BALL:
                print("Picked up balls ",self.robot.pickedUpBalls)
                if self.robot.pickedUpBalls >= BALLS_PER_TRIP:
                    if self.smallGoal is None:
                        print("[STATE] Goal not yet detected – waiting")
                        return
                    self._go_to_drop_off_ball()
                    return
                    
                ball = None
                
                if self.robot.deliveredBalls == 0 and self.robot.pickedUpBalls == 0:
                    ball = self._find_best_white_ball()
                elif self.robot.deliveredBalls == 0 and self.robot.pickedUpBalls == BALLS_PER_TRIP-1:
                    ball = self._find_best_orange_ball()
                else:
                    ball = self._find_best_ball()
                
                if ball is None:
                    print("[STATE] No balls visible")
                    #if self.robot.pickedUpBalls>0:
                    if self._go_to_drop_off_ball():
                        return
                    print("[STATE] Goal not yet detected – waiting")
                    return
                    #self._go_to_state(STOP, "no balls")
                    #return
                
                self._planPathTo(ball, allow_edge_approach=True)
                self.targetKind = BALL_TARGET

                print(f"[STATE] Target → ({ball.x:.0f},{ball.y:.0f})  orange={ball.isOrange}")
                self._go_to_state(ALIGN_TARGET, "ball selected")

            # 2. Rotate to face whichever target is active.
            case _ if self.currentState == ALIGN_TARGET:
                if self.robot.target is None:
                    self.targetKind = None
                    self._go_to_state(FIND_BALL, "lost target")
                    return

                d = self._distance_to_target()
                if self.targetKind == DROPOFF_TARGET and d is not None and d <= 5.0:
                    self._start_goal_alignment()
                    return

                if self.robot.isFacingTarget():
                    if self.targetKind == GOAL_TARGET:
                        self._go_to_state(DROP_BALL, "goal aligned")
                    else:
                        self._go_to_state(MOVE_TO_TARGET, "aligned")
                    return

                delta = self.robot.getDeltaAngle(self._angle_to_target())
                print(f"[STATE] Turning {delta:+.1f}°")
                self._enqueue_turn(delta)

            # 3. Drive to a ball or a drop-off waypoint.
            case _ if self.currentState == MOVE_TO_TARGET:
                if self.robot.target is None:
                    self.targetKind = None
                    self._go_to_state(FIND_BALL, "lost target")
                    return

                d = self._distance_to_target()
                threshold, max_drive = self._move_settings()
                is_waypoint = len(self.currentPath) > 1
                print(f"[STATE] Distance to target: {d:.0f} cm  kind={self.targetKind} waypoint={is_waypoint}")

                if d <= threshold:
                    if is_waypoint:
                        self._advance_path()
                        self._go_to_state(ALIGN_TARGET, "waypoint reached")
                        return
                    if self.targetKind == BALL_TARGET:
                        self._go_to_state(PICKUP_BALL, "in collect range")
                    else:
                        self._start_goal_alignment()
                    return

                # Alignment needs the strict tolerance. While moving, use a
                # wider tolerance so camera noise does not bounce us straight
                # back to AlignTarget after every short drive command.
                if self._has_drifted():
                    self._go_to_state(ALIGN_TARGET, "drifted")
                    return

                MIN_DRIVE_CM = 2.0
                drive_cm = min(d - threshold, max_drive)
                if drive_cm < MIN_DRIVE_CM:
                    if is_waypoint:
                        self._advance_path()
                        self._go_to_state(ALIGN_TARGET, "waypoint reached")
                        return
                    if self.targetKind == BALL_TARGET:
                        self._go_to_state(PICKUP_BALL, "close enough")
                    else:
                        self._start_goal_alignment()
                    return
                self._enqueue_forward(float(drive_cm))

            # 4. Collect ball, then back up
            case _ if self.currentState == PICKUP_BALL:
                d = self._distance_to_target()
                # Accept anything within collectOffset + MIN_DRIVE_PX — that's
                # the same boundary MoveToBall uses to enter this state.
                MIN_DRIVE_PX = 2.0
                if d is not None and d > ROBOTCONFIG["collectOffset"] + MIN_DRIVE_PX:
                    self._go_to_state(MOVE_TO_TARGET, "too far")
                    return

                self.robot.pickedUpBalls += 1
                target_id = getattr(self.robot.target, "id", None)
                if target_id is not None:
                    self.collectedTargetIds.add(target_id)
                pickup_drive_cm = (
                    ROBOTCONFIG["edgeCollectForward"]
                    if self._is_near_boundary(self.robot.target)
                    else 14.0
                )
                self._enqueue_collect()
                self._enqueue_forward(pickup_drive_cm)
                self._enqueue_backward(pickup_drive_cm)

                print(f"[STATE] Collecting ball #{self.robot.pickedUpBalls}  "
                      f"(pickup drive {pickup_drive_cm:.1f}cm)")

                if self.robot.pickedUpBalls < BALLS_PER_TRIP:
                    self.robot.target = None
                    self.targetKind = None
                    self.currentPath = []
                    self._go_to_state(FIND_BALL, f"need {BALLS_PER_TRIP - self.robot.pickedUpBalls} more")
                else:
                    if self.smallGoal is None:
                        print("[STATE] Goal not yet detected – waiting")
                        return
                    self._go_to_drop_off_ball()

            # 7. Release balls at goal
            case _ if self.currentState == DROP_BALL:
                if not self.robot.isFacingTarget():
                    self._go_to_state(ALIGN_TARGET, "not facing goal")
                    return

                #d = self._distance_to_target()
                #if d is not None and d > ROBOTCONFIG["goalDropOffOffset"]:
                #    self._go_to_state("MoveToGoal", "too far")
                #    return

                self.commandsQueue.append("RELEASE")
                self.robot.deliveredBalls += self.robot.pickedUpBalls
                self.robot.pickedUpBalls = 0
                self.robot.target = None
                self.targetKind = None
                self.currentPath = []
                print("[STATE] Released all balls")
                self._go_to_state(FIND_BALL, "delivery done")
                self.commandsQueue.append("COLLECT")

            # Terminal 
            case _ if self.currentState == STOP:
                if self.robot.pickedUpBalls > 0 and self._go_to_drop_off_ball():
                    return
                print("[STATE] Robot stopped – nothing left to do")

            case _:
                print(f"[STATE] Unknown state '{self.currentState}'")
                self._go_to_state(STOP)

    # Command dispatch (called by main.py)

    def passCommandToRobot(self) -> str | None:
        if not self.commandsQueue:
            return None
        command = self.commandsQueue.pop(0)
        print(f"[CMD] {command}")
        return command
>>>>>>> development
