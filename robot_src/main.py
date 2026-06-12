import socket
from time import sleep

from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D, SpeedPercent
from ev3dev2.sound import *

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


def drive_forward():
    left_motor.on(SpeedPercent(DRIVE_SPEED))
    right_motor.on(SpeedPercent(DRIVE_SPEED))


def drive_backward():
    left_motor.on(SpeedPercent(-DRIVE_SPEED))
    right_motor.on(SpeedPercent(-DRIVE_SPEED))


def turn_left():
    left_motor.on(SpeedPercent(-TURN_SPEED))
    right_motor.on(SpeedPercent(TURN_SPEED))


def turn_right():
    left_motor.on(SpeedPercent(TURN_SPEED))
    right_motor.on(SpeedPercent(-TURN_SPEED))


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
    "A_ON": motor_a.on(SpeedPercent(-35)),
    "A_REV": motor_a.on(SpeedPercent(35)),
    "A_OFF": motor_a.stop(stop_action="brake"),
    "B_IN": motor_b.on_for_degrees(SpeedPercent(20), -90, brake=True, block=True),
    "B_OUT": motor_b.on_for_degrees(SpeedPercent(20), 90, brake=True, block=True),
    "COLLECT": collect_cycle,
    "RELEASE": release_cycle,
    "FORWARD_1s": timed_drive(drive_forward, 1.0),
    "FORWARD": drive_forward,
    "BACKWARD": drive_backward,
    "LEFT": timed_drive(turn_left, 1.0),
    "RIGHT": timed_drive(turn_right, 1.0),
    "NUDGE_FORWARD": nudge_forward,
    "NUDGE_BACKWARD": nudge_backward,
    "NUDGE_LEFT": nudge_left,
    "NUDGE_RIGHT": nudge_right,
    "STOP_DRIVE": stop_drive,
    "STOP": stop_all,
    #"ON_CONNECTION": IAMFART,
}


def handle_command(command: str):
    command = command.strip().upper()
    if not command:
        return

    print("Ny kommando:", command)

    if command not in COMMAND_MAP:
        return

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