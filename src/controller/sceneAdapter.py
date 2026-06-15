def bbox_center(box):
    x1, x2, y1, y2 = box[:4]
    return {
        "x": (x1 + x2) // 2,
        "y": (y1 + y2) // 2
    }


def detection_to_point(det):
    cx, cy = det["centroid"]
    return {
        "x": cx,
        "y": cy
    }


def build_scene_from_camera(detections, goals, robot_pos, robot_angle):
    orange_ball = None
    white_balls = []

    for det in detections:
        label = det["label"]

        if label == "orange":
            orange_ball = detection_to_point(det)

        elif label == "white":
            white_balls.append(detection_to_point(det))

    robot = None
    if robot_pos is not None:
        robot_center = bbox_center(robot_pos)
        robot = {
            "x": robot_center["x"],
            "y": robot_center["y"],
            "heading": robot_angle
        }

    goal_b = None
    if goals is not None and goals[0] is not None:
        goal_b = bbox_center(goals[0])

    return {
        "robot": robot,
        "goal_b": goal_b,
        "orange_ball": orange_ball,
        "white_balls": white_balls
    }