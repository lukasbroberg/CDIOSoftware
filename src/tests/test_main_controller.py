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
)
from utils.pathPlanner import build_path, path_blocked_by_cross
from utils.perspectiveCorrection import PIXELS_PER_CM_FLOOR


class Target:
    def __init__(self, x=200, y=200, is_orange=False, target_id=None):
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

    def _plan_directly_to(self, target):
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
        next_ball = Target(x=300, target_id=2)
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

    def test_lost_target_returns_to_ball_selection(self):
        self.controller.currentState = ALIGN_TARGET
        self.controller.targetKind = BALL_TARGET

        self.controller.updateRobotState()

        self.assertEqual(self.controller.currentState, FIND_BALL)
        self.assertIsNone(self.controller.targetKind)


class PathPlannerTests(unittest.TestCase):
    def test_blocked_diagonal_uses_clockwise_cardinal_cross_points(self):
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

        self.assertGreaterEqual(len(path), 2)
        # First two points are right and then below the cross (clockwise).
        self.assertGreater(path[0]["x"], cross.x)
        self.assertEqual(path[0]["y"], cross.y)
        self.assertEqual(path[1]["x"], cross.x)
        self.assertGreater(path[1]["y"], cross.y)
        self.assertTrue(all(
            not path_blocked_by_cross(start, end, cross)
            for start, end in zip([robot, *path], [*path, ball])
        ))


if __name__ == "__main__":
    unittest.main()
