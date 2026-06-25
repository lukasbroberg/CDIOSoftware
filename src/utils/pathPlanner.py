import math
from utils.perspectiveCorrection import pixel_to_world, HEIGHT_ROBOT, HEIGHT_FLOOR, PIXELS_PER_CM_FLOOR


DEFAULTS = {
    "robotSafetyMargin": 18,
    "wallBallThreshold": 12,
    "nearCrossDistance": 16,
    # Pixel-space route safety around the cross.  The overlay and robot drive
    # commands are ultimately pixel targets, so the collision check must agree
    # with the drawn line on the camera frame.
    "crossSafetyRadius": 30,
    "approachDistance": 11,
    # Keep route points just outside the no-go circle.  Too large a value
    # pushes the robot into the bands; too small clips the cross.
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

    safety_radius_px = DEFAULTS["crossSafetyRadius"] * PIXELS_PER_CM_FLOOR
    return _distance_px(closest_point, cross) < safety_radius_px


def _inside_field(point, field, margin=DEFAULTS["robotSafetyMargin"]):
    px, py = _px(point)
    margin_px = margin * PIXELS_PER_CM_FLOOR
    return (
        field["left"] + margin_px <= px <= field["right"] - margin_px
        and field["top"] + margin_px <= py <= field["bottom"] - margin_px
    )

def create_cross_waypoints(cross, field):
    """Return fixed waypoints around a square perimeter outside the cross.

    The points are ordered clockwise starting at right:
    right, bottom-right, bottom, bottom-left, left, top-left, top, top-right.
    Moving between neighbouring points follows the outside of the square and
    avoids the old diagonal right→bottom shortcut that clipped the cross.
    """
    cx, cy = _px(cross)
    total_safety_cm = DEFAULTS["crossSafetyRadius"] + DEFAULTS["waypointOffset"]
    offset_px = total_safety_cm * PIXELS_PER_CM_FLOOR

    points = [
        {"x": cx + offset_px, "y": cy},  # right
        {"x": cx + offset_px, "y": cy + offset_px},  # bottom-right
        {"x": cx, "y": cy + offset_px},  # bottom
        {"x": cx - offset_px, "y": cy + offset_px},  # bottom-left
        {"x": cx - offset_px, "y": cy},  # left
        {"x": cx - offset_px, "y": cy - offset_px},  # top-left
        {"x": cx, "y": cy - offset_px},  # top
        {"x": cx + offset_px, "y": cy - offset_px},  # top-right
    ]
    return [point for point in points if _inside_field(point, field)]


def _dedupe_consecutive(points):
    deduped = []
    for point in points:
        if not deduped or _distance_px(deduped[-1], point) > 1.0:
            deduped.append(point)
    return deduped


def _segments_clear(route, start, target, cross):
    return all(
        not path_blocked_by_cross(a, b, cross)
        for a, b in zip([start, *route], [*route, target])
    )


def _route_around_cross(start, target, cross, field):
    """Find the shortest safe route around the cross perimeter."""
    waypoints = create_cross_waypoints(cross, field)
    candidates = []

    for start_index, start_waypoint in enumerate(waypoints):
        if path_blocked_by_cross(start, start_waypoint, cross):
            continue

        for direction in (1, -1):
            route = []
            current = start_index
            for _ in range(len(waypoints)):
                waypoint = waypoints[current]
                route.append(waypoint)
                clean_route = _dedupe_consecutive(route)

                if _segments_clear(clean_route, start, target, cross):
                    candidates.append(clean_route)
                    break

                next_index = (current + direction) % len(waypoints)
                if path_blocked_by_cross(waypoint, waypoints[next_index], cross):
                    break
                current = next_index

    if not candidates:
        return []

    return min(candidates, key=lambda route: (get_path_cost(route, start), len(route)))


def build_path(robot, target, cross, field):
    """
    All coordinates in pixel space.
    Distance/angle calculations use pixel_to_world for real-world accuracy.
    Returns list of pixel-space dicts.
    """
    if cross is None or field is None or not path_blocked_by_cross(robot, target, cross):
        return []

    path = _route_around_cross(robot, target, cross, field)
    print(f"[PATH] cross blocks direct route; waypoints={path}")
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
