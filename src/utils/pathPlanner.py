import math


DEFAULTS = {
    "robotSafetyMargin": 55,
    "wallBallThreshold": 80,
    "nearCrossDistance": 110,
    "crossSafetyRadius": 90,
    "approachDistance": 75,
    "waypointOffset": 120,
}


def distance(a, b):
    return math.hypot(b["x"] - a["x"], b["y"] - a["y"])


def clamp_to_field(point, field, margin=DEFAULTS["robotSafetyMargin"]):
    return {
        "x": max(field["left"] + margin, min(field["right"] - margin, point["x"])),
        "y": max(field["top"] + margin, min(field["bottom"] - margin, point["y"])),
    }


def get_approach_point(ball, cross, approach_distance=DEFAULTS["approachDistance"]):
    dx = ball["x"] - cross["x"]
    dy = ball["y"] - cross["y"]
    length = math.hypot(dx, dy)

    if length == 0:
        return {"x": ball["x"], "y": ball["y"]}

    return {
        "x": ball["x"] + (dx / length) * approach_distance,
        "y": ball["y"] + (dy / length) * approach_distance,
    }


def classify_ball(ball, cross):
    if distance(ball, cross) < DEFAULTS["nearCrossDistance"]:
        return "nearCross"

    return "normal"


def path_blocked_by_cross(start, target, cross):
    dx = target["x"] - start["x"]
    dy = target["y"] - start["y"]

    line_length_squared = dx * dx + dy * dy

    if line_length_squared == 0:
        return False

    t = ((cross["x"] - start["x"]) * dx + (cross["y"] - start["y"]) * dy) / line_length_squared
    t = max(0, min(1, t))

    closest_point = {
        "x": start["x"] + t * dx,
        "y": start["y"] + t * dy,
    }

    return distance(closest_point, cross) < DEFAULTS["crossSafetyRadius"]


def create_cross_waypoint(robot, target, cross, field):
    offset = DEFAULTS["waypointOffset"]

    waypoint_options = [
        {"x": cross["x"] - offset, "y": cross["y"] - offset},
        {"x": cross["x"] + offset, "y": cross["y"] - offset},
        {"x": cross["x"] - offset, "y": cross["y"] + offset},
        {"x": cross["x"] + offset, "y": cross["y"] + offset},
    ]

    safe_options = []

    for point in waypoint_options:
        safe_point = clamp_to_field(point, field)

        if (
            not path_blocked_by_cross(robot, safe_point, cross)
            and not path_blocked_by_cross(safe_point, target, cross)
        ):
            safe_options.append(safe_point)

    options = safe_options if safe_options else [
        clamp_to_field(point, field) for point in waypoint_options
    ]

    options.sort(
        key=lambda point: distance(robot, point) + distance(point, target)
    )

    return options[0]


def build_path(robot, target, cross, field):
    wall_margin = 55
    approach_distance = 75
    wall_threshold = 80

    final_target = target

    near_wall = (
        target["x"] < field["left"] + wall_threshold
        or target["x"] > field["right"] - wall_threshold
        or target["y"] < field["top"] + wall_threshold
        or target["y"] > field["bottom"] - wall_threshold
    )

    if near_wall:
        final_target = clamp_to_field(target, field, wall_threshold)

    ball_type = classify_ball(target, cross)

    if ball_type == "nearCross":
        final_target = clamp_to_field(
            get_approach_point(target, cross, approach_distance),
            field,
            wall_margin,
        )

    path = []

    if path_blocked_by_cross(robot, final_target, cross):
        waypoint = create_cross_waypoint(robot, final_target, cross, field)
        path.append(waypoint)

    path.append(final_target)

    if final_target != target:
        path.append(target)

    return path


def get_path_cost(path, start):
    if not path:
        return math.inf

    cost = distance(start, path[0])

    for i in range(1, len(path)):
        cost += distance(path[i - 1], path[i])

    return cost

if __name__ == "__main__":
    field = {"left": 0, "right": 1000, "top": 0, "bottom": 500}
    robot = {"x": 100, "y": 100}
    ball = {"x": 500, "y": 250}
    cross = {"x": 300, "y": 200}

    path = build_path(robot, ball, cross, field)
    print("Generated Path:", path)
    print("Path Cost:", get_path_cost(path, robot))
    