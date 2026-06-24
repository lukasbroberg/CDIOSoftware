import math
from utils.perspectiveCorrection import pixel_to_world, HEIGHT_ROBOT, HEIGHT_FLOOR, PIXELS_PER_CM_FLOOR


DEFAULTS = {
    "robotSafetyMargin": 8,
    "wallBallThreshold": 12,
    "nearCrossDistance": 16,
    "crossSafetyRadius": 20,
    "approachDistance": 11,
    "waypointOffset": 10,
}


def _px(obj):
    """Get pixel x/y from object or dict."""
    if isinstance(obj, dict):
        return obj["x"], obj["y"]
    return obj.x, obj.y


def distance(a, b, h1=HEIGHT_FLOOR, h2=HEIGHT_FLOOR):
    """Real-world cm distance between two pixel-space points."""
    ax, ay = _px(a)
    bx, by = _px(b)
    wx1, wy1 = pixel_to_world(ax, ay, h1)
    wx2, wy2 = pixel_to_world(bx, by, h2)
    return math.hypot(wx2 - wx1, wy2 - wy1)


def _distance_px(a, b):
    """Raw pixel distance — used for internal path geometry only."""
    ax, ay = _px(a)
    bx, by = _px(b)
    return math.hypot(bx - ax, by - ay)


def clamp_to_field(point, field, margin=DEFAULTS["robotSafetyMargin"]):
    """Clamp a pixel-space point to within field boundaries (pixels)."""
    px, py = _px(point)
    margin_px = margin * PIXELS_PER_CM_FLOOR
    return {
        "x": max(field["left"] + margin_px, min(field["right"] - margin_px, px)),
        "y": max(field["top"] + margin_px, min(field["bottom"] - margin_px, py)),
    }


def get_approach_point(ball, cross, approach_distance=DEFAULTS["approachDistance"]):
    bx, by = _px(ball)
    cx, cy = _px(cross)
    dx = bx - cx
    dy = by - cy
    length = math.hypot(dx, dy)

    if length == 0:
        return {"x": bx, "y": by}

    return {
        "x": bx + (dx / length) * approach_distance,
        "y": by + (dy / length) * approach_distance,
    }


def classify_ball(ball, cross):
    if cross is None:
        return "normal"

    if distance(ball, cross) < DEFAULTS["nearCrossDistance"]:
        return "nearCross"
    return "normal"


def path_blocked_by_cross(start, target, cross):
    if cross is None:
        return False

    sx, sy = _px(start)
    tx, ty = _px(target)
    cx, cy = _px(cross)

    dx = tx - sx
    dy = ty - sy
    line_length_squared = dx * dx + dy * dy

    if line_length_squared == 0:
        return False

    t = ((cx - sx) * dx + (cy - sy) * dy) / line_length_squared
    t = max(0, min(1, t))

    closest_point = {"x": sx + t * dx, "y": sy + t * dy}

    return distance(closest_point, cross) < DEFAULTS["crossSafetyRadius"]

def create_cross_waypoint(robot, target, cross, field):
    cx, cy = _px(cross)
    
    # Calculate the total safe distance from the center in centimeters
    # (Safety radius + our extra waypoint clearance)
    total_safety_cm = DEFAULTS["crossSafetyRadius"] + DEFAULTS["waypointOffset"]
    
    # Convert this real-world centimeter distance into pixels
    offset_px = total_safety_cm * PIXELS_PER_CM_FLOOR

    # Generate options using the pixel-converted offset
    waypoint_options = [
        {"x": cx - offset_px, "y": cy - offset_px},
        {"x": cx + offset_px, "y": cy - offset_px},
        {"x": cx - offset_px, "y": cy + offset_px},
        {"x": cx + offset_px, "y": cy + offset_px},
    ]

    safe_options = [
        clamp_to_field(p, field)
        for p in waypoint_options
        if not path_blocked_by_cross(robot, clamp_to_field(p, field), cross)
        and not path_blocked_by_cross(clamp_to_field(p, field), target, cross)
    ]

    options = safe_options if safe_options else [
        clamp_to_field(p, field) for p in waypoint_options
    ]

    # Sort by real-world distance
    options.sort(key=lambda p: distance(robot, p) + distance(p, target))
    return options[0]


def build_path(robot, target, cross, field):
    """
    All coordinates in pixel space.
    Distance/angle calculations use pixel_to_world for real-world accuracy.
    Returns list of pixel-space dicts.
    """
    tx, ty = _px(target)
    final_target = {"x": tx, "y": ty}
    
    blocked = path_blocked_by_cross(robot, final_target, cross)
    ball_type = classify_ball(target, cross)
    print(f"[PATH] cross={cross} blocked={blocked} ball_type={ball_type}")

    near_wall = (
        tx < field["left"]   + DEFAULTS["wallBallThreshold"]
        or tx > field["right"]  - DEFAULTS["wallBallThreshold"]
        or ty < field["top"]    + DEFAULTS["wallBallThreshold"]
        or ty > field["bottom"] - DEFAULTS["wallBallThreshold"]
    )

    if near_wall:
        final_target = clamp_to_field(target, field, DEFAULTS["wallBallThreshold"])

    ball_type = classify_ball(target, cross)

    if ball_type == "nearCross":
        final_target = clamp_to_field(
            get_approach_point(target, cross, DEFAULTS["approachDistance"]),
            field,
            DEFAULTS["robotSafetyMargin"],
        )

    path = []

    if path_blocked_by_cross(robot, final_target, cross):
        waypoint = create_cross_waypoint(robot, final_target, cross, field)
        path.append(waypoint)

    #path.append(final_target)

    #if final_target != {"x": tx, "y": ty}:
    #    path.append({"x": tx, "y": ty})
        

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
    ball  = {"x": 500, "y": 250}
    cross = {"x": 300, "y": 200}

    path = build_path(robot, ball, cross, field)
    print("Generated Path (pixels):", path)
    print("Path Cost (cm):", get_path_cost(path, robot))