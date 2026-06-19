import sys
import termios
import tty
from connect import establish_connection

def read_key():
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

KEY_MAP = {
    "w": "FORWARD_TIMED::2",
    "a": "LEFT_TIMED::6.5",
    "s": "BACKWARD_TIMED::2",
    "d": "RIGHT_TIMED::6.5",
    "c": "COLLECT",
    "r": "RELEASE",
    " ": "STOP",
    "q": "EXIT",
    "p": "ON_CONNECTION",
}

VALUE_MAP = {
    "DRIVE_SPEED": 25,
    "TURN_SPEED": 20,
}

keep_connection = True
s = establish_connection()
while(keep_connection):        
    key = read_key()
            
    if key not in KEY_MAP: continue
    
    cmd = KEY_MAP[key]
    
    if cmd == "EXIT":
        keep_connection=False
        break
    
    s.sendall((cmd+"\n").encode("utf-8"))

    buffer = b""
    while b"\n" not in buffer:
        data = s.recv(1024)
        if not data:
            raise RuntimeError("Robot disconnected")
        buffer += data

    response = buffer.decode("utf-8").strip()
    
    print("command: " + str(cmd) + " sent")
    print("Svar fra robot:", response)
