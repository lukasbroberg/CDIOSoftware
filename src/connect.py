from dotenv import load_dotenv
import socket
import sys
import os

load_dotenv()
ROBOT_IP = os.getenv("ROBOT_IP")
PORT = os.getenv("ROBOT_PORT")

cmd = sys.argv[1]

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((ROBOT_IP, PORT))
    s.sendall((cmd + "\n"))