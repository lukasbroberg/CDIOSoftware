from controller.sceneAdapter import build_scene_from_camera
from controller.mainController import MainController

fake_detections = [
    {
        "label": "orange",
        "centroid": (580, 230)
    },
    {
        "label": "white",
        "centroid": (300, 250)
    },
    {
        "label": "white",
        "centroid": (400, 200)
    }
]

fake_goals = [
    (590, 610, 230, 250, "large_goal")
]

fake_robot_pos = (560, 580, 210, 230)
fake_robot_angle = 45

scene = build_scene_from_camera(
    fake_detections,
    fake_goals,
    fake_robot_pos,
    fake_robot_angle
)

print("SCENE:", scene)

controller = MainController()
controller.initializeObjects(scene)

for step in range(20):
    print("\n" + "=" * 40)
    print("STEP", step)

    previous_state = controller.currentState

    print("Balls left:", len(controller.balls))
    print("Delivered:", controller.deliveredBalls)
    print("Previous state:", previous_state)

    if controller.currentTarget:
        print("Target:", controller.currentTarget["type"])
        print("Target position:", controller.currentTarget["position"])
    else:
        print("Target: None")

    action = controller.decideNextAction()
    command = controller.passCommandToRobot()

    current_state = controller.currentState

    print("Current state:", current_state)
    print("Action:", action)
    print("Command:", command)

    controller.simulateStep(action)

    if action == "Stop":
        break