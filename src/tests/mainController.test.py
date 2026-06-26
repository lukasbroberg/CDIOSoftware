"""
Unit tests for MainController state machine logic.

All external dependencies (Robot, Ball, Goal, Point, ROBOTCONFIG, tracker,
pathPlanner, perspectiveCorrection) are mocked so these tests run without
the physical robot stack installed.

Run with:
    python -m unittest test_main_controller.py
"""

import sys
import math
import unittest
from unittest.mock import MagicMock, patch, PropertyMock

# ── Stub out every import that MainController needs ───────────────────────────

# models
Ball        = MagicMock()
Goal        = MagicMock()
Point       = MagicMock()
Robot       = MagicMock()

# TrackedObjects
TrackedObject = type("TrackedObject", (), {})   # real class so isinstance works
ObjectTracker = MagicMock()

# ROBOTCONFIG values used by the controller
ROBOTCONFIG = {
    "collectOffset":        10.0,
    "backupDistance":       2.0,
    "goalDropOffOffset":    20.0,
    "maxDistToBoundary":    5.0,
    "fullTurnTime":         2.0,
}

PIXELS_PER_CM_FLOOR = 4.0

# Stub modules before import
sys.modules["models.Robot"]         = MagicMock(Robot=Robot)
sys.modules["models.Ball"]          = MagicMock(Ball=Ball)
sys.modules["models.Goal"]          = MagicMock(Goal=Goal)
sys.modules["models.Point"]         = MagicMock(Point=Point)
sys.modules["models.Robot_config"]  = MagicMock(ROBOTCONFIG=ROBOTCONFIG)
sys.modules["models.TrackedObjects"]= MagicMock(
    TrackedObject=TrackedObject,
    ObjectTracker=ObjectTracker,
)
sys.modules["utils.getDistance"]    = MagicMock()
sys.modules["utils.getAngle"]       = MagicMock()
sys.modules["utils.perspectiveCorrection"] = MagicMock(
    PIXELS_PER_CM_FLOOR=PIXELS_PER_CM_FLOOR,
    pixel_to_world=lambda x, y, object_height_cm=0: (x / PIXELS_PER_CM_FLOOR,
                                                      y / PIXELS_PER_CM_FLOOR),
)
sys.modules["utils.pathPlanner"]    = MagicMock(
    build_path=MagicMock(return_value=[]),
    pixel_to_world=lambda x, y, object_height_cm=0: (x / PIXELS_PER_CM_FLOOR,
                                                      y / PIXELS_PER_CM_FLOOR),
)
sys.modules["collections"]          = __import__("collections")

# Now we can safely import the controller
from mainController import MainController   # noqa: E402


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_robot(x=100, y=100, rotation=0, facing=True, picked=0, delivered=0):
    """Return a mock Robot with sensible defaults."""
    r = MagicMock()
    r.x             = x
    r.y             = y
    r.rotation      = rotation
    r.pickedUpBalls = picked
    r.deliveredBalls= delivered
    r.target        = None
    r.isFacingTarget.return_value = facing
    r.getDeltaAngle.return_value  = 15.0
    r.findNearestBall.side_effect = lambda balls: balls[0] if balls else None
    return r


def make_ball(x=200, y=200, orange=False):
    b = MagicMock(spec=TrackedObject)   # Ball IS a TrackedObject for isinstance
    b.__class__ = type("Ball", (TrackedObject,), {})
    b.x        = x
    b.y        = y
    b.isOrange = orange
    b.id       = 1
    return b


def make_goal(x=500, y=300):
    g = MagicMock()
    g.x = x
    g.y = y
    return g


def make_controller(state=None, robot=None, balls=None,
                    small_goal=None, large_goal=None):
    """Build a MainController wired up with mocks."""
    ctrl = MainController()
    ctrl.commandsQueue = []           # clear the initial COLLECT
    ctrl.currentState  = state
    ctrl.robot         = robot or make_robot()
    ctrl.balls         = balls or []
    ctrl.smallGoal     = small_goal or make_goal(500, 300)
    ctrl.largeGoal     = large_goal or make_goal(50,  300)
    ctrl.boundaries    = {"left": 0, "right": 800, "top": 0, "bottom": 600}
    ctrl.cross         = None
    ctrl.currentPath   = []
    return ctrl


# ─────────────────────────────────────────────────────────────────────────────
# FindBall
# ─────────────────────────────────────────────────────────────────────────────

class TestFindBall(unittest.TestCase):

    def test_transitions_to_align_when_ball_found(self):
        ball = make_ball()
        ctrl = make_controller(state="FindBall", balls=[ball])
        ctrl._planPathTo = MagicMock()
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "AlignWithBall")

    def test_transitions_to_stop_when_no_balls(self):
        ctrl = make_controller(state="FindBall", balls=[])
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "Stop")

    def test_goes_to_goal_when_quota_reached(self):
        ctrl = make_controller(state="FindBall")
        ctrl.robot.pickedUpBalls = 3        # BALLS_PER_TRIP = 3
        ctrl._planPathTo = MagicMock()
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "AlignWithDropOffPoint")

    def test_prefers_white_ball_on_first_trip(self):
        white  = make_ball(x=300, orange=False)
        orange = make_ball(x=400, orange=True)
        ctrl   = make_controller(state="FindBall", balls=[white, orange])
        ctrl.robot.deliveredBalls = 0
        ctrl.robot.pickedUpBalls  = 0
        ctrl._planPathTo = MagicMock()
        ctrl.updateRobotState()
        # findNearestBall called with white balls only
        call_args = ctrl.robot.findNearestBall.call_args[0][0]
        self.assertTrue(all(not b.isOrange for b in call_args))

    def test_prefers_orange_ball_after_first_white(self):
        white  = make_ball(x=300, orange=False)
        orange = make_ball(x=400, orange=True)
        ctrl   = make_controller(state="FindBall", balls=[white, orange])
        ctrl.robot.deliveredBalls = 0
        ctrl.robot.pickedUpBalls  = 1
        ctrl._planPathTo = MagicMock()
        ctrl.updateRobotState()
        call_args = ctrl.robot.findNearestBall.call_args[0][0]
        self.assertTrue(all(b.isOrange for b in call_args))

    def test_goes_to_dropoff_when_no_balls_but_carrying(self):
        ctrl = make_controller(state="FindBall", balls=[])
        ctrl.robot.pickedUpBalls = 2
        ctrl._planPathTo = MagicMock()
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "AlignWithDropOffPoint")


# ─────────────────────────────────────────────────────────────────────────────
# AlignWithBall
# ─────────────────────────────────────────────────────────────────────────────

class TestAlignWithBall(unittest.TestCase):

    def test_transitions_to_move_when_facing(self):
        ctrl = make_controller(state="AlignWithBall")
        ctrl.robot.target = make_ball()
        ctrl.robot.isFacingTarget.return_value = True
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "MoveToBall")
        self.assertEqual(len(ctrl.commandsQueue), 0)   # no turn command

    def test_enqueues_turn_when_not_facing(self):
        ctrl = make_controller(state="AlignWithBall")
        ctrl.robot.target = make_ball()
        ctrl.robot.isFacingTarget.return_value = False
        ctrl.robot.getDeltaAngle.return_value  = 30.0
        ctrl._angle_to_target = MagicMock(return_value=45.0)
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "AlignWithBall")   # state unchanged
        self.assertEqual(len(ctrl.commandsQueue), 1)
        self.assertIn("RIGHT_TIMED", ctrl.commandsQueue[0])

    def test_enqueues_left_turn_for_negative_delta(self):
        ctrl = make_controller(state="AlignWithBall")
        ctrl.robot.target = make_ball()
        ctrl.robot.isFacingTarget.return_value = False
        ctrl.robot.getDeltaAngle.return_value  = -30.0
        ctrl._angle_to_target = MagicMock(return_value=-45.0)
        ctrl.updateRobotState()
        self.assertIn("LEFT_TIMED", ctrl.commandsQueue[0])

    def test_goes_to_findball_when_no_target(self):
        ctrl = make_controller(state="AlignWithBall")
        ctrl.robot.target = None
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "FindBall")


# ─────────────────────────────────────────────────────────────────────────────
# MoveToBall
# ─────────────────────────────────────────────────────────────────────────────

class TestMoveToBall(unittest.TestCase):

    def _ctrl_with_ball_target(self, distance, facing=True):
        ctrl = make_controller(state="MoveToBall")
        ball = make_ball()
        ctrl.robot.target = ball
        ctrl.currentPath  = [ball]
        ctrl.robot.isFacingTarget.return_value = facing
        ctrl._distance_to_target = MagicMock(return_value=distance)
        ctrl._angle_to_target    = MagicMock(return_value=0.0)
        return ctrl

    def test_transitions_to_pickup_when_close_enough(self):
        ctrl = self._ctrl_with_ball_target(distance=ROBOTCONFIG["collectOffset"] - 1)
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "PickupBall")

    def test_enqueues_forward_when_far(self):
        ctrl = self._ctrl_with_ball_target(distance=50.0)
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "MoveToBall")
        self.assertEqual(len(ctrl.commandsQueue), 1)
        self.assertIn("FORWARD_TIMED", ctrl.commandsQueue[0])

    def test_realigns_when_drifted(self):
        ctrl = self._ctrl_with_ball_target(distance=50.0, facing=False)
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "AlignWithBall")
        self.assertEqual(len(ctrl.commandsQueue), 0)

    def test_advances_path_on_waypoint_reached(self):
        ctrl  = make_controller(state="MoveToBall")
        wp    = MagicMock(spec=object)   # plain Point, not Ball/TrackedObject
        ball  = make_ball()
        ctrl.currentPath  = [wp, ball]
        ctrl.robot.target = wp
        ctrl.robot.isFacingTarget.return_value = True
        ctrl._distance_to_target = MagicMock(return_value=5.0)   # within 15cm threshold
        ctrl._angle_to_target    = MagicMock(return_value=0.0)
        ctrl.updateRobotState()
        # Waypoint popped, next target set
        self.assertEqual(ctrl.robot.target, ball)
        self.assertEqual(ctrl.currentState, "AlignWithBall")

    def test_caps_drive_distance_at_15cm(self):
        ctrl = self._ctrl_with_ball_target(distance=100.0)
        ctrl.updateRobotState()
        cmd  = ctrl.commandsQueue[0]
        # FORWARD_TIMED::<seconds> — extract seconds
        secs = float(cmd.split("::")[1])
        max_secs = round(15.0 * PIXELS_PER_CM_FLOOR / 100.0 * 2.155, 3)
        self.assertAlmostEqual(secs, max_secs, places=2)


# ─────────────────────────────────────────────────────────────────────────────
# PickupBall
# ─────────────────────────────────────────────────────────────────────────────

class TestPickupBall(unittest.TestCase):

    def _ctrl_at_pickup(self, picked=0):
        ctrl = make_controller(state="PickupBall")
        ball = make_ball()
        ctrl.robot.target        = ball
        ctrl.robot.pickedUpBalls = picked
        ctrl._distance_to_target = MagicMock(return_value=ROBOTCONFIG["collectOffset"])
        return ctrl

    def test_increments_picked_up_balls(self):
        ctrl = self._ctrl_at_pickup(picked=0)
        ctrl.updateRobotState()
        self.assertEqual(ctrl.robot.pickedUpBalls, 1)

    def test_enqueues_correct_pickup_sequence(self):
        ctrl = self._ctrl_at_pickup(picked=0)
        ctrl.updateRobotState()
        cmds = ctrl.commandsQueue
        types = [c.split("::")[0] for c in cmds]
        self.assertEqual(types, [
            "FORWARD_TIMED", "CLOSEDOOR", "FORWARD_TIMED", "OPENDOOR", "BACKWARD_TIMED"
        ])

    def test_goes_to_findbball_when_more_needed(self):
        ctrl = self._ctrl_at_pickup(picked=0)   # will become 1, need 3
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "FindBall")

    def test_goes_to_dropoff_when_quota_reached(self):
        ctrl = self._ctrl_at_pickup(picked=2)   # will become 3 = BALLS_PER_TRIP
        ctrl._planPathTo = MagicMock()
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "AlignWithDropOffPoint")

    def test_goes_back_to_move_when_too_far(self):
        ctrl = make_controller(state="PickupBall")
        ctrl.robot.target        = make_ball()
        ctrl.robot.pickedUpBalls = 0
        ctrl._distance_to_target = MagicMock(
            return_value=ROBOTCONFIG["collectOffset"] + 10.0
        )
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "MoveToBall")


# ─────────────────────────────────────────────────────────────────────────────
# AlignWithDropOffPoint
# ─────────────────────────────────────────────────────────────────────────────

class TestAlignWithDropOffPoint(unittest.TestCase):

    def test_transitions_to_move_when_facing(self):
        ctrl = make_controller(state="AlignWithDropOffPoint")
        ctrl.robot.target = MagicMock()
        ctrl.robot.isFacingTarget.return_value = True
        ctrl._distance_to_target = MagicMock(return_value=30.0)
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "MoveTowardsDropOffPoint")

    def test_enqueues_turn_when_not_facing(self):
        ctrl = make_controller(state="AlignWithDropOffPoint")
        ctrl.robot.target = MagicMock()
        ctrl.robot.isFacingTarget.return_value = False
        ctrl.robot.getDeltaAngle.return_value  = 20.0
        ctrl._distance_to_target = MagicMock(return_value=30.0)
        ctrl._angle_to_target    = MagicMock(return_value=20.0)
        ctrl.updateRobotState()
        self.assertTrue(any("TIMED" in c for c in ctrl.commandsQueue))

    def test_goes_to_findball_when_no_target(self):
        ctrl = make_controller(state="AlignWithDropOffPoint")
        ctrl.robot.target = None
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "FindBall")


# ─────────────────────────────────────────────────────────────────────────────
# MoveTowardsDropOffPoint
# ─────────────────────────────────────────────────────────────────────────────

class TestMoveTowardsDropOffPoint(unittest.TestCase):

    def _ctrl(self, distance, facing=True, path_len=1):
        ctrl = make_controller(state="MoveTowardsDropOffPoint")
        # Use a plain object (not Ball/TrackedObject) to simulate a Point target
        target = MagicMock(spec=object)
        ctrl.robot.target = target
        ctrl.currentPath  = [target] * path_len
        ctrl.robot.isFacingTarget.return_value = facing
        ctrl._distance_to_target = MagicMock(return_value=distance)
        ctrl._angle_to_target    = MagicMock(return_value=0.0)
        return ctrl

    def test_transitions_to_align_goal_when_at_dropoff(self):
        ctrl = self._ctrl(distance=3.0, path_len=1)   # last item, within 5cm
        ctrl.updateRobotState()
        self.assertEqual(ctrl.robot.target, ctrl.smallGoal)
        self.assertEqual(ctrl.currentState, "AlignWithGoal")

    def test_advances_waypoint_when_not_last(self):
        wp   = MagicMock(spec=object)
        drop = MagicMock(spec=object)
        ctrl = make_controller(state="MoveTowardsDropOffPoint")
        ctrl.currentPath  = [wp, drop]
        ctrl.robot.target = wp
        ctrl.robot.isFacingTarget.return_value = True
        ctrl._distance_to_target = MagicMock(return_value=5.0)
        ctrl._angle_to_target    = MagicMock(return_value=0.0)
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "AlignWithDropOffPoint")

    def test_enqueues_forward_when_far(self):
        ctrl = self._ctrl(distance=50.0, path_len=1)
        ctrl.updateRobotState()
        self.assertTrue(any("FORWARD_TIMED" in c for c in ctrl.commandsQueue))

    def test_realigns_when_drifted(self):
        ctrl = self._ctrl(distance=50.0, facing=False)
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "AlignWithDropOffPoint")
        self.assertEqual(len(ctrl.commandsQueue), 0)

    def test_caps_drive_at_15cm(self):
        ctrl = self._ctrl(distance=100.0, path_len=1)
        ctrl.updateRobotState()
        cmd  = ctrl.commandsQueue[0]
        secs = float(cmd.split("::")[1])
        max_secs = round(15.0 * PIXELS_PER_CM_FLOOR / 100.0 * 2.155, 3)
        self.assertAlmostEqual(secs, max_secs, places=2)


# ─────────────────────────────────────────────────────────────────────────────
# DropBall
# ─────────────────────────────────────────────────────────────────────────────

class TestDropBall(unittest.TestCase):

    def test_releases_and_resets(self):
        ctrl = make_controller(state="DropBall")
        ctrl.robot.target        = make_goal()
        ctrl.robot.pickedUpBalls = 3
        ctrl.robot.deliveredBalls= 0
        ctrl.robot.isFacingTarget.return_value = True
        ctrl.updateRobotState()
        self.assertIn("RELEASE", ctrl.commandsQueue)
        self.assertEqual(ctrl.robot.pickedUpBalls,  0)
        self.assertEqual(ctrl.robot.deliveredBalls, 3)
        self.assertIsNone(ctrl.robot.target)
        self.assertEqual(ctrl.currentState, "FindBall")

    def test_goes_back_to_align_when_not_facing(self):
        ctrl = make_controller(state="DropBall")
        ctrl.robot.target = make_goal()
        ctrl.robot.isFacingTarget.return_value = False
        ctrl.updateRobotState()
        self.assertEqual(ctrl.currentState, "AlignWithGoal")
        self.assertNotIn("RELEASE", ctrl.commandsQueue)

    def test_re_enqueues_collect_after_release(self):
        ctrl = make_controller(state="DropBall")
        ctrl.robot.target        = make_goal()
        ctrl.robot.pickedUpBalls = 3
        ctrl.robot.deliveredBalls= 0
        ctrl.robot.isFacingTarget.return_value = True
        ctrl.updateRobotState()
        self.assertIn("COLLECT", ctrl.commandsQueue)


if __name__ == "__main__":
    unittest.main(verbosity=2)