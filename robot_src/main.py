import sys
if sys.platform != 'linux' or 'ev3dev' not in open('/etc/os-release').read():
    import mock_ev3dev2  # patches sys.modules before ev3dev2 loads
import socket
from time import sleep
from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedPercent
from ev3dev2.sound import *
# your_script.py


HOST = "0.0.0.0"
PORT = 9999

# Motorer
motor_a = MediumMotor(OUTPUT_A)   # opsamler
motor_b = MediumMotor(OUTPUT_B)  # arm
left_motor = LargeMotor(OUTPUT_C)
right_motor = LargeMotor(OUTPUT_D)

DRIVE_SPEED = 25
TURN_SPEED = 10
NUDGE_TIME = 0.18


def stop_drive():
    left_motor.stop(stop_action="brake")
    right_motor.stop(stop_action="brake")


def stop_all():
    motor_a.stop(stop_action="brake")
    motor_b.stop(stop_action="hold")
    stop_drive()


def drive_forward(spd):
    print(spd)
    left_motor.on(SpeedPercent(spd))
    right_motor.on(SpeedPercent(spd))


def drive_backward(spd):
    left_motor.on(SpeedPercent(-spd))
    right_motor.on(SpeedPercent(-spd))


def turn_left(spd):
    left_motor.on(SpeedPercent(-spd))
    right_motor.on(SpeedPercent(spd))


def turn_right(spd):
    left_motor.on(SpeedPercent(spd))
    right_motor.on(SpeedPercent(-spd))


def timed_drive(action, duration=1.0):
    action()
    sleep(duration)
    stop_drive()


def nudge_forward():
    drive_forward()
    sleep(NUDGE_TIME)
    stop_drive()


def nudge_backward():
    drive_backward()
    sleep(NUDGE_TIME)
    stop_drive()


def nudge_left():
    turn_left()
    sleep(NUDGE_TIME)
    stop_drive()


def nudge_right():
    turn_right()
    sleep(NUDGE_TIME)
    stop_drive()


def collect_cycle():
    motor_a.on(SpeedPercent(25))
    #motor_a.stop(stop_action="brake")

def IAMFART():
    motor_a.on(SpeedPercent(45))
    connected_string = "I AM FART"
    # FIXED: Removed 'self=self'
    Sound.speak(text=connected_string)

def release_cycle():
    motor_a.stop(stop_action="brake")
    motor_a.on(SpeedPercent(-20))
    #sleep(0.5)
    #drive_forward(10)
    sleep(6.0)
    #stop_drive()
    #drive_backward(7)
    #sleep(2.5)
    stop_drive()
    motor_a.stop(stop_action="brake")


COMMAND_MAP = {
    "A_ON": lambda: motor_a.on(SpeedPercent(-35)),
    "A_REV": lambda: motor_a.on(SpeedPercent(35)),
    "A_OFF": lambda: motor_a.stop(stop_action="brake"),
    "B_IN": lambda: motor_b.on_for_degrees(SpeedPercent(20), -90, brake=True, block=True),
    "B_OUT": lambda: motor_b.on_for_degrees(SpeedPercent(20), 90, brake=True, block=True),
    "COLLECT": collect_cycle,
    "RELEASE": release_cycle,
    "FORWARD_TIMED": lambda time=None: timed_drive(lambda: drive_forward(10),time or 1.0),
    "BACKWARD_TIMED": lambda time=None: timed_drive(lambda: drive_backward(10),time or 25),
    "FORWARD": lambda v=None: drive_forward(v or 10),
    "BACKWARD": lambda v=None: drive_backward(v or 10),
    "LEFT_TIMED": lambda time=None: timed_drive(lambda: turn_left(TURN_SPEED), time or 1.0),
    "RIGHT_TIMED": lambda time=None: timed_drive(lambda: turn_right(TURN_SPEED), time or 1.0),
    "NUDGE_FORWARD": nudge_forward,
    "NUDGE_BACKWARD": nudge_backward,
    "NUDGE_LEFT": nudge_left,
    "NUDGE_RIGHT": nudge_right,
    "STOP_DRIVE": stop_drive,
    "STOP": stop_all,
    "ON_CONNECTION": lambda: IAMFART(),
}


def handle_command(command: str):
    raw_command = command.strip()
    parts = raw_command.upper().split("::")
    value = float(parts[1]) if len(parts) > 1 and parts[1] else None
    command = parts[0]
    if not command:
        return "IGNORED"

    print("Ny kommando:", command, " Vaerdi:", value)

    if command not in COMMAND_MAP:
        print("Ukendt kommando", command)
        return "ERROR::UNKNOWN_COMMAND::{}".format(command)

    try:
        if value is not None:
            COMMAND_MAP[command](value)
        else:
            COMMAND_MAP[command]()
        return "DONE::{}".format(command)
    except Exception as e:
        print("Kommando fejlede:", e)
        return "ERROR::{}::{}".format(command, e)


def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((HOST, PORT))
        server.listen(1)

        #COMMAND_MAP["ON_CONNECTION"]
        
        print("Robot-server lytter paa {}:{}".format(HOST, PORT))

        while True:
            conn, addr = server.accept()
            print("Forbundet fra:", addr)

            with conn:
                buffer = b""
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break

                    buffer += data

                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        command = line.decode("utf-8", errors="ignore")
                        response = handle_command(command)
                        if response:
                            conn.sendall((response + "\n").encode("utf-8"))

            print("Klient frakoblet")


if __name__ == "__main__": main()