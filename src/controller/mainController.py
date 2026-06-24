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
    FindBall        – pick the best ball and set it as target
    AlignWithBall   – rotate to face the ball
    MoveToBall      – drive until collectOffset away; uses wider angle
                      tolerance close-up to avoid oscillation
    PickupBall      – COLLECT (start intake) + ram forward + back up
    AlignWithGoal   – rotate to face the goal
    MoveToGoal      – drive until goalOffset away from the goal
    DropBall        – RELEASE + reset
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
        if not self.balls:
            return None
        return self.robot.findNearestBall(self.balls)
        #orange = next((b for b in self.balls if b.isOrange), None)
        #if orange:
        #    return orange
    
    def _find_best_white_ball(self) -> Ball | None:
        if not self.balls:
            return None
        white_balls = []
        for ball in self.balls:
            if not ball.isOrange:
                white_balls.append(ball)
        
        if white_balls is None or len(white_balls)<=0:
            return self._find_best_ball()
        
        return self.robot.findNearestBall(white_balls)
    
    def _find_best_orange_ball(self) -> Ball | None:
        if not self.balls:
            return None
        orange_balls = []
        for ball in self.balls:
            if ball.isOrange:
                orange_balls.append(ball)
        if orange_balls is None or len(orange_balls) == 0:
            return self._find_best_ball()
        return self.robot.findNearestBall(orange_balls)

    def _planPathTo(self, target: Ball):
        self.currentPath = build_path(
            self.robot,
            target,
            cross=self.cross,
            field=self.boundaries
        )
        # Ensure the original Ball instance is always the last point
        self.currentPath.append(target)
        
        # Remove the last dict copy of the ball position
        if self.currentPath:
            self.currentPath.pop()
            
        # Append the real Ball instance as final target
        self.currentPath = [
            Point(p["x"], p["y"]) if isinstance(p, dict) else p
            for p in self.currentPath
        ]
        self.currentPath.append(target)
        self.robot.target = self.currentPath[0]

    #Queue commands
    def _enqueue_turn(self, delta: float):
        t = _turn_time(delta)
        direction = "LEFT_TIMED" if delta < 0 else "RIGHT_TIMED"
        self.commandsQueue.append(f"{direction}::{t}")

    def _enqueue_forward(self, cm: float):
        self.commandsQueue.append(f"FORWARD_TIMED::{_drive_time(cm+1.0)}")

    def _enqueue_backward(self, cm: float):
        self.commandsQueue.append(f"BACKWARD_TIMED::{_drive_time(cm+1.0)}")
        
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
        if self.boundaries is None:
            return False
        
        if item is None:
            return False
        
        print(f"[DANGER CHECK] pos=({item.x:.0f},{item.y:.0f}) boundaries={self.boundaries} margin={ROBOTCONFIG['maxDistToBoundary']}")
        
        if (item.y-ROBOTCONFIG["maxDistToBoundary"]>self.boundaries["top"] and
            item.y+ROBOTCONFIG["maxDistToBoundary"]<self.boundaries["bottom"] and
            item.x+ROBOTCONFIG["maxDistToBoundary"]<self.boundaries["right"] and
            item.x-ROBOTCONFIG["maxDistToBoundary"]>self.boundaries["left"]):
            return False
        
        return True

    def _go_to_drop_off_ball(self):
        dropOffPoint = Point(
            self.smallGoal.x+ROBOTCONFIG["goalDropOffOffset"],
            self.smallGoal.y
        )
        self._planPathTo(dropOffPoint)
        #self.robot.setTarget(dropOffPoint)
        self._go_to_state("AlignWithDropOffPoint", "quota reached")
        
        
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
            self._go_to_state("FindBall", "init")
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
            case "FindBall":
                
                print("Picked up balls ",self.robot.pickedUpBalls)
                
                target = self.robot.target
                if target is not None:
                    if isinstance(target, TrackedObject | Ball):
                        self._go_to_state("AlignWithBall", "Has target, aligns with target now")
                    #else:
                        #if self.smallGoal is None:
                        #    print("[STATE] Goal not yet detected – waiting")
                        #    return
                        #self.robot.setTarget(self.smallGoal)

                
                if self.robot.pickedUpBalls >= BALLS_PER_TRIP:
                    if self.smallGoal is None:
                        print("[STATE] Goal not yet detected – waiting")
                        return
                    #self.robot.setTarget(self.smallGoal)
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
                    if self.robot.pickedUpBalls>0:
                        self._go_to_drop_off_ball()   
                        return
                    self._go_to_state("Stop", "no balls")
                    return
                
                self._planPathTo(ball)

                print(f"[STATE] Target → ({ball.x:.0f},{ball.y:.0f})  orange={ball.isOrange}")
                self._go_to_state("AlignWithBall")

            # 2. Rotate to face the ball
            case "AlignWithBall":
                if self.robot.target is None:
                    self._go_to_state("FindBall", "lost target")
                    return
                
                d = self._distance_to_target()
                if d<18:
                    self._go_to_state("MoveToBall", "aligned")

                if self.robot.isFacingTarget():
                    self._go_to_state("MoveToBall", "aligned")
                    return

                delta = self.robot.getDeltaAngle(self._angle_to_target())
                print(f"[STATE] Turning {delta:+.1f}°")
                self._enqueue_turn(delta)

            #  3. Drive to Target
            case "MoveToBall":
                if self.robot.target is None:
                    if self.robot.pickedUpBalls<3:
                        self._go_to_state("FindBall", "No target, finds next target")
                        return
                    else:
                        self._go_to_state("Stop", "Filled with balls. goes to state: Stop")

                d = self._distance_to_target()
    
                is_waypoint = not isinstance(self.robot.target, Ball | TrackedObject)
                
                # Waypoints use a larger threshold, balls use collectOffset
                threshold = ROBOTCONFIG["waypointOffset"] if is_waypoint else ROBOTCONFIG["collectOffset"]

                print(f"[STATE] Distance to target: {d:.0f} cm  waypoint={is_waypoint}")

                if d <= threshold:
                    if is_waypoint:
                        self.currentPath.pop(0)
                        if self.currentPath:
                            self.robot.target = self.currentPath[0]
                            self._go_to_state("AlignWithBall", "waypoint reached, next point")
                        else:
                            self._go_to_state("FindBall", "path exhausted")
                        return
                    self._go_to_state("PickupBall", "in collect range")
                    return


                # Realignment check
                if not self.robot.isFacingTarget():
                    self._go_to_state("AlignWithBall", "drifted")
                    return

                MIN_DRIVE_CM = 2.0
                drive_cm = min(d - threshold, 30.0)
                if drive_cm < MIN_DRIVE_CM:
                    if is_waypoint:
                        self.currentPath.pop(0)
                        if self.currentPath:
                            self.robot.target = self.currentPath[0]
                            self._go_to_state("AlignWithBall", "waypoint reached, next point")
                        else:
                            self._go_to_state("FindBall", "path exhausted")
                        return
                    self._go_to_state("PickupBall", "close enough")
                    return
                

                self._enqueue_forward(float(drive_cm))

            # 4. Collect ball, then back up
            case "PickupBall":
                d = self._distance_to_target()
                # Accept anything within collectOffset + MIN_DRIVE_PX — that's
                # the same boundary MoveToBall uses to enter this state.
                MIN_DRIVE_PX = 2.0
                if d is not None and d > ROBOTCONFIG["collectOffset"] + MIN_DRIVE_PX:
                    self._go_to_state("MoveToBall", "too far")
                    return

                self.robot.pickedUpBalls += 1
                self._enqueue_collect()
                self._enqueue_forward(14.0)
                self._enqueue_backward(14.0)

                print(f"[STATE] Collecting ball #{self.robot.pickedUpBalls}  "
                      f"(backup {ROBOTCONFIG['backupDistance']}px)")

                if self.robot.pickedUpBalls < BALLS_PER_TRIP:
                    self.robot.target = None
                    self._go_to_state("FindBall", f"need {BALLS_PER_TRIP - self.robot.pickedUpBalls} more")
                else:
                    if self.smallGoal is None:
                        print("[STATE] Goal not yet detected – waiting")
                        return
                    
                    self._go_to_drop_off_ball()
                    
            # Align with dropOffPoint
            case "AlignWithDropOffPoint":
                if self.robot.target is None:
                    self._go_to_state("FindBall", "lost goal target")
                    return
                
                if self.robot.isFacingTarget():
                    self._go_to_state("MoveTowardsDropOffPoint", "aligned")
                    return
                
                d = self._distance_to_target()
                if d <= 5.0:
                    self.robot.setTarget(self.smallGoal)
                    self._go_to_state("AlignWithGoal", "in range")
                    return
                
                delta = self.robot.getDeltaAngle(self._angle_to_target())
                print(f"[STATE] Turning {delta:+.1f}°")
                self._enqueue_turn(delta)
                
            case "MoveTowardsDropOffPoint":
                if self.robot.target is None:
                    self._go_to_state("FindBall", "lost goal target")
                    return

                if not self.robot.isFacingTarget():
                    self._go_to_state("AlignWithDropOffPoint", "drifted")
                    return

                is_waypoint = not isinstance(self.robot.target, Ball | TrackedObject) and len(self.currentPath) > 1
                threshold = 23.0 if is_waypoint else 5.0

                d = self._distance_to_target()
                print(f"[STATE] Distance to dropoff: {d:.0f} cm  waypoint={is_waypoint}")

                if d <= threshold:
                    if is_waypoint:
                        self.currentPath.pop(0)
                        self.robot.target = self.currentPath[0]
                        self._go_to_state("AlignWithDropOffPoint", "waypoint reached, next point")
                    else:
                        self.robot.setTarget(self.smallGoal)
                        self._go_to_state("AlignWithGoal", "at dropoff point")
                    return

                if not self.robot.isFacingTarget():
                    self._go_to_state("AlignWithDropOffPoint", "drifted")
                    return

                drive_cm = min(d - threshold, 15.0)
                self._enqueue_forward(drive_cm)
                

            #  5. Rotate to face the goal 
            case "AlignWithGoal":
                if self.robot.target is None:
                    self._go_to_state("FindBall", "lost goal target")
                    return

                if self.robot.isFacingTarget():
                    self._go_to_state("DropBall", "aligned")
                    return

                delta = self.robot.getDeltaAngle(self._angle_to_target())
                print(f"[STATE] Turning {delta:+.1f}°")
                self._enqueue_turn(delta)

            #  6. Drive to goalOffset distance from the goal
            case "MoveToGoal":
                if self.robot.target is None:
                    self._go_to_state("FindBall", "lost goal target")
                    return

                if not self.robot.isFacingTarget():
                    self._go_to_state("AlignWithGoal", "drifted")
                    return

                d = self._distance_to_target()
                print(f"[STATE] Distance to goal: {d:.0f} px")

                if d <= ROBOTCONFIG["goalDropOffOffset"]:
                    self._go_to_state("DropBall", "in range")
                    return

                drive_px = min(d - ROBOTCONFIG["goalDropOffOffset"], 150)
                #Safe quit to release ball, removes unlimited cycle of moving forward
                if(drive_px<0.1):
                    self._go_to_state("DropBall", "in range")
                
                self._enqueue_forward(drive_px)

            # 7. Release balls at goal
            case "DropBall":
                if not self.robot.isFacingTarget():
                    self._go_to_state("AlignWithGoal", "not facing")
                    return

                #d = self._distance_to_target()
                #if d is not None and d > ROBOTCONFIG["goalDropOffOffset"]:
                #    self._go_to_state("MoveToGoal", "too far")
                #    return

                self.commandsQueue.append("RELEASE")
                self.robot.deliveredBalls += self.robot.pickedUpBalls
                self.robot.pickedUpBalls = 0
                self.robot.target = None
                print("[STATE] Released all balls")
                self._go_to_state("FindBall", "delivery done")
                self.commandsQueue.append("COLLECT")

            # Terminal 
            case "Stop":
                if self.robot.pickedUpBalls>0 or self.robot.deliveredBalls<=0:
                    self.currentState="AlignWithDropOffPoint"
                    print("Robot stopped, no balls detected. Moving robot away")
                
                print("[STATE] Robot stopped – nothing left to do")

            case _:
                print(f"[STATE] Unknown state '{self.currentState}'")
                self._go_to_state("Stop")

    # Command dispatch (called by main.py)

    def passCommandToRobot(self) -> str | None:
        if not self.commandsQueue:
            return None
        command = self.commandsQueue.pop(0)
        print(f"[CMD] {command}")
        return command