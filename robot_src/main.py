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
TURN_SPEED = 20
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
    motor_a.on(SpeedPercent(-45))
    sleep(1.0)
    motor_b.on_for_degrees(SpeedPercent(5), -90, brake=True, block=True)
    sleep(1.5)
    motor_b.on_for_degrees(SpeedPercent(5), 90, brake=True, block=True)
    sleep(1.5)
    motor_a.stop(stop_action="brake")

def IAMFART():
    connected_string = "I AM FART"
    Sound.speak(self=self,text=connected_string)

def release_cycle():
    motor_a.on(SpeedPercent(80))
    
COMMAND_MAP = {
    "A_ON": lambda: motor_a.on(SpeedPercent(-35)),
    "A_REV": lambda: motor_a.on(SpeedPercent(35)),
    "A_OFF": lambda: motor_a.stop(stop_action="brake"),
    "B_IN": lambda: motor_b.on_for_degrees(SpeedPercent(20), -90, brake=True, block=True),
    "B_OUT": lambda: motor_b.on_for_degrees(SpeedPercent(20), 90, brake=True, block=True),
    "COLLECT": collect_cycle,
    "RELEASE": release_cycle,
    "FORWARD_TIMED": lambda time=None: timed_drive(lambda: drive_forward(50),time or 1.0),
    "BACKWARD_TIMED": lambda time=None: timed_drive(lambda: drive_backward(50),time or 25),
    "FORWARD": lambda v=None: drive_forward(v or 10),
    "BACKWARD": lambda v=None: drive_backward(v or 10),
    "LEFT_TIMED": lambda time=None: timed_drive(lambda: turn_left(TURN_SPEED), time or 1.0),
    "RIGHT_TIMED": lambda time=None: timed_drive(lambda: turn_right(TURN_SPEED), time or 1.0),
    "NUDGE_FORWARD": nudge_forward,
    "NUDGE_BACKWARD": nudge_backward,
    "NUDGE_LEFT": nudge_left,
    "NUDGE_RIGHT": nudge_right,
    "STOP_DRIVE": stop_drive,
    "STOP":lambda: stop_all,
    #"ON_CONNECTION": IAMFART,
}


def handle_command(command: str):
    parts = command.strip().upper().split("::")
    value = int(parts[1]) if len(parts) > 1 and parts[1] else None
    command = parts[0]
    if not command:
        return

    print("Ny kommando:", command," Vaerdi:", value)

    if command not in COMMAND_MAP:
        print("Ukendt kommando", command)
        return
    if value is not None:
        COMMAND_MAP[command](value)
    else:
        COMMAND_MAP[command]()


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
                        handle_command(command)

            print("Klient frakoblet")


if __name__ == "__main__": main()