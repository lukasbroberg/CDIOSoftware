from dotenv import load_dotenv
import socket
import sys
import os
import termios
import tty

load_dotenv()
ROBOT_IP = os.getenv("ROBOT_IP")
PORT = os.getenv("ROBOT_PORT")

#cmd = sys.argv[1]

def read_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

KEY_MAP = {
    "w": "FORWARD",
    "a": "NUDGE_LEFT",
    "s": "BACKWARD",
    "d": "NUDGE_RIGHT",
    "c": "COLLECT",
    "r": "RELEASE",
    " ": "STOP",
    "q": "EXIT",
}

def establish_connection():
    #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ROBOT_IP, int(PORT)))
    print("connected")
    return s