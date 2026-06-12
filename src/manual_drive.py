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
    "w": "FORWARD",
    "a": "NUDGE_LEFT",
    "s": "BACKWARD",
    "d": "NUDGE_RIGHT",
    "c": "COLLECT",
    "r": "RELEASE",
    " ": "STOP",
    "q": "EXIT",
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
    print("command: " + str(cmd) + " sent")