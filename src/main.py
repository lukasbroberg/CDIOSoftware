from controller.mainController import MainController
from controller.mockScene import get_mock_scene


def main():
    scene = get_mock_scene()

    controller = MainController()
    controller.initializeObjects(scene)

    step = 0

    while True:
        step += 1
        print("\n--- STEP", step, "---")

        action = controller.decideNextAction()
        controller.passCommandToRobot()
        controller.simulateStep(action)

        print("Action:", action)

        if action == "Stop" or step >= 200:
            break


if __name__ == "__main__":
    main()