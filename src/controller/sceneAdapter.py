

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


def build_scene_from_camera(detections, goals, robot_pos, robot_angle, boundaries):
        
    robot = None
    orange_ball = []
    white_balls = []
    _boundaries = []

    goal_large = None
    goal_small = None

    for det in detections:
        label = det["label"]

        if label == "orange_ball":
            orange_ball.append(detection_to_point(det))

        elif label == "white_ball":
            white_balls.append(detection_to_point(det))

    if robot_pos is not None:
        x1,x2,y1,y2 = robot_pos
        robot = {
            "x": x1+(x2-x1)/2,
            "y": y1+(y2-y1)/2,
            "rotation": robot_angle
        }
    if goals is not None and goals[0] is not None and goals[1] is not None:
        goal_large = bbox_center(goals[0])
        goal_small = bbox_center(goals[1])
        
    if boundaries is not None:
        _boundaries = [
            boundaries[0][2], #right X (top right)
            boundaries[2][0], #left X (bottom left)
            boundaries[0][3], #top Y (top right)
            boundaries[2][1], #bottom Y (bottom left)
        ]
        

    return {
        "robot": robot,
        "goal_large": goal_large,
        "orange_ball": orange_ball,
        "white_balls": white_balls,
        "goal_small": goal_small,
        "boundaries": boundaries #right, left, top, bottom
    }