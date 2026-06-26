"""Regression tests for the reduced MainController state machine."""

import sys
import unittest
from pathlib import Path

# Allow both `python src/tests/test_main_controller.py` and unittest discovery
# from the repository root, without requiring a manually configured PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from controller.mainController import (
    ALIGN_TARGET,
    BALL_TARGET,
    DROPOFF_TARGET,
    DROP_BALL,
    FIND_BALL,
    GOAL_TARGET,
    MOVE_TO_TARGET,
    PICKUP_BALL,
    MainController,
    _drive_time,
)
from models.Robot_config import ROBOTCONFIG
from utils.pathPlanner import DEFAULTS, build_path, path_blocked_by_cross, distance
from utils.perspectiveCorrection import PIXELS_PER_CM_FLOOR


class Target:
    def __init__(self, x=500, y=200, is_orange=False, target_id=None):
        self.x = x
        self.y = y
        self.isOrange = is_orange
        self.id = target_id


class FakeRobot:
    def __init__(self):
        self.x = 100
        self.y = 100
        self.rotation = 0
        self.target = None
        self.pickedUpBalls = 0
        self.deliveredBalls = 0
        self.facing = True

    def findNearestBall(self, balls):
        return balls[0]

    def isFacingTarget(self, _tolerance=None):
        return self.facing

    def getDeltaAngle(self, _angle):
        return 10

    def setTarget(self, target):
        self.target = target


class MainControllerStateTests(unittest.TestCase):
    def setUp(self):
        self.controller = MainController()
        self.controller.commandsQueue = []
        self.controller.robot = FakeRobot()
        self.controller.currentState = FIND_BALL
        self.controller.smallGoal = Target(500, 300)

    def _plan_directly_to(self, target, allow_edge_approach=False):
        self.controller.currentPath = [target]
        self.controller.robot.target = target

    def test_ball_flow_uses_shared_align_and_move_states(self):
        ball = Target()
        self.controller.balls = [ball]
        self.controller._planPathTo = self._plan_directly_to

        self.controller.updateRobotState()
        self.assertEqual(self.controller.currentState, ALIGN_TARGET)
        self.assertEqual(self.controller.targetKind, BALL_TARGET)

        self.controller.updateRobotState()
        self.assertEqual(self.controller.currentState, MOVE_TO_TARGET)

        self.controller._distance_to_target = lambda: 1
        self.controller.updateRobotState()
        self.assertEqual(self.controller.currentState, PICKUP_BALL)

    def test_pickup_clears_path_before_finding_next_ball(self):
        ball = Target()
        self.controller.currentState = PICKUP_BALL
        self.controller.targetKind = BALL_TARGET
        self.controller.robot.target = ball
        self.controller.currentPath = [ball]
        self.controller._distance_to_target = lambda: 1

        self.controller.updateRobotState()

        self.assertEqual(self.controller.currentState, FIND_BALL)
        self.assertIsNone(self.controller.robot.target)
        self.assertIsNone(self.controller.targetKind)
        self.assertEqual(self.controller.currentPath, [])

    def test_collected_tracking_id_is_not_selected_again(self):
        collected = Target(target_id=1)
        next_ball = Target(x=500, target_id=2)
        self.controller.currentState = PICKUP_BALL
        self.controller.targetKind = BALL_TARGET
        self.controller.robot.target = collected
        self.controller.currentPath = [collected]
        self.controller._distance_to_target = lambda: 1

        self.controller.updateRobotState()
        self.controller.commandsQueue = []
        self.controller.balls = [collected, next_ball]
        self.controller._planPathTo = self._plan_directly_to
        self.controller.updateRobotState()

        self.assertIs(self.controller.robot.target, next_ball)

    def test_detection_on_robot_is_not_an_available_target(self):
        self.controller.robot.x = 960
        self.controller.robot.y = 540
        false_detection = Target(960, 540, target_id=1)
        real_ball = Target(960 + 60 * PIXELS_PER_CM_FLOOR, 540, target_id=2)
        self.controller.balls = [false_detection, real_ball]

        self.assertEqual(self.controller._available_balls(), [real_ball])

    def test_ball_inside_cross_zone_is_not_an_available_target(self):
        self.controller.robot.x = 100
        self.controller.robot.y = 100
        self.controller.cross = Target(960, 540)
        unsafe_ball = Target(
            960 + 10 * PIXELS_PER_CM_FLOOR,
            540,
            target_id=1,
        )
        real_ball = Target(
            960 + 80 * PIXELS_PER_CM_FLOOR,
            540,
            target_id=2,
        )
        self.controller.balls = [unsafe_ball, real_ball]

        self.assertEqual(self.controller._available_balls(), [real_ball])

    def test_edge_ball_gets_inside_field_approach_point(self):
        ball = Target(10, 500, target_id=1)
        self.controller.boundaries = {
            "left": 0,
            "right": 1920,
            "top": 0,
            "bottom": 1080,
        }

        self.controller._planPathTo(ball, allow_edge_approach=True)

        self.assertEqual(len(self.controller.currentPath), 2)
        approach = self.controller.currentPath[0]
        self.assertIs(self.controller.robot.target, approach)
        self.assertIs(self.controller.currentPath[-1], ball)
        self.assertGreater(approach.x, ball.x)
        self.assertAlmostEqual(
            approach.x,
            ROBOTCONFIG["edgeBallApproachMargin"] * PIXELS_PER_CM_FLOOR,
        )

    def test_edge_risky_active_target_is_not_changed(self):
        edge_ball = Target(10, 500, target_id=1)
        other_ball = Target(400, 500, target_id=2)
        self.controller.boundaries = {
            "left": 0,
            "right": 1920,
            "top": 0,
            "bottom": 1080,
        }
        self.controller.targetKind = BALL_TARGET
        self.controller.currentPath = [Target(200, 500), edge_ball]
        self.controller.robot.target = self.controller.currentPath[0]
        self.controller.balls = [other_ball, edge_ball]

        self.assertIs(self.controller._find_best_ball(), edge_ball)

    def test_edge_pickup_uses_short_cautious_drive(self):
        ball = Target(10, 500, target_id=1)
        self.controller.boundaries = {
            "left": 0,
            "right": 1920,
            "top": 0,
            "bottom": 1080,
        }
        self.controller.currentState = PICKUP_BALL
        self.controller.targetKind = BALL_TARGET
        self.controller.robot.target = ball
        self.controller.currentPath = [ball]
        self.controller._distance_to_target = lambda: 1

        self.controller.updateRobotState()

        self.assertEqual(self.controller.commandsQueue[0], "COLLECT")
        self.assertEqual(
            self.controller.commandsQueue[1],
            f"FORWARD_TIMED::{_drive_time(ROBOTCONFIG['edgeCollectForward'] + 1.0)}",
        )
        self.assertNotEqual(
            self.controller.commandsQueue[1],
            f"FORWARD_TIMED::{_drive_time(14.0)}",
        )

    def test_dropoff_and_goal_use_the_same_align_and_move_states(self):
        dropoff = Target(400, 300)
        self.controller.currentState = ALIGN_TARGET
        self.controller.targetKind = DROPOFF_TARGET
        self.controller.currentPath = [dropoff]
        self.controller.robot.target = dropoff
        self.controller._distance_to_target = lambda: 30

        self.controller.updateRobotState()
        self.assertEqual(self.controller.currentState, MOVE_TO_TARGET)

        self.controller._distance_to_target = lambda: 1
        self.controller.updateRobotState()
        self.assertEqual(self.controller.currentState, ALIGN_TARGET)
        self.assertEqual(self.controller.targetKind, GOAL_TARGET)
        self.assertIs(self.controller.robot.target, self.controller.smallGoal)

        self.controller.updateRobotState()
        self.assertEqual(self.controller.currentState, DROP_BALL)

    def test_waypoint_is_not_reached_too_early_near_cross(self):
        waypoint = Target(300, 300)
        ball = Target(500, 500)
        self.controller.currentState = MOVE_TO_TARGET
        self.controller.targetKind = BALL_TARGET
        self.controller.currentPath = [waypoint, ball]
        self.controller.robot.target = waypoint
        self.controller._distance_to_target = lambda: ROBOTCONFIG["waypointArrivalTolerance"] + 5

        self.controller.updateRobotState()

        self.assertEqual(self.controller.currentState, MOVE_TO_TARGET)
        self.assertIs(self.controller.robot.target, waypoint)
        self.assertTrue(self.controller.commandsQueue)

    def test_lost_target_returns_to_ball_selection(self):
        self.controller.currentState = ALIGN_TARGET
        self.controller.targetKind = BALL_TARGET

        self.controller.updateRobotState()

        self.assertEqual(self.controller.currentState, FIND_BALL)
        self.assertIsNone(self.controller.targetKind)


class PathPlannerTests(unittest.TestCase):
    def test_blocked_diagonal_uses_only_safe_cross_perimeter_segments(self):
        cross = Target(960, 540)
        robot = Target(
            960 + 80 * PIXELS_PER_CM_FLOOR,
            540 + 80 * PIXELS_PER_CM_FLOOR,
        )
        ball = Target(
            960 - 80 * PIXELS_PER_CM_FLOOR,
            540 - 80 * PIXELS_PER_CM_FLOOR,
        )
        field = {"left": 0, "right": 1920, "top": 0, "bottom": 1080}

        path = build_path(robot, ball, cross, field)

        self.assertGreaterEqual(len(path), 1)
        self.assertTrue(all(
            not path_blocked_by_cross(start, end, cross)
            for start, end in zip([robot, *path], [*path, ball])
        ))
        self.assertTrue(all(
            distance(point, cross) >= DEFAULTS["crossSafetyRadius"]
            for point in path
        ))

    def test_cross_route_does_not_clamp_to_band_or_cross_over_target_line(self):
        cross = Target(960, 520)
        robot = Target(1500, 900)
        target = Target(478, 181)
        field = {"left": 380, "right": 1700, "top": 135, "bottom": 1040}

        path = build_path(robot, target, cross, field)

        self.assertTrue(path)
        self.assertTrue(all(point["y"] > field["top"] + 80 for point in path))
        self.assertTrue(all(
            not path_blocked_by_cross(start, end, cross)
            for start, end in zip([robot, *path], [*path, target])
        ))


if __name__ == "__main__":
    unittest.main()
