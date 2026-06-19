from dotenv import load_dotenv
import socket
import sys
import os
import termios
import tty
import asyncio

load_dotenv()
ROBOT_IP = os.getenv("ROBOT_IP")
PORT = os.getenv("ROBOT_PORT")

def establish_connection():
    #with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((ROBOT_IP, int(PORT)))
    print("connected")
    return s

# sends a controller command to the robot through the scoket connection
def send_controller_command(sock: socket, command):
    if sock is None:
        return None
    
    if command is None:
        return None
    
    print("Sending to robot:", command)
    sock.sendall(command.encode())
    
async def send_command(reader, writer, command):
    writer.write((command+"\n").encode("utf-8"))
    await writer.drain()
    print("command: " + str(command) + " sent")
    
    response = await reader.readline()
    response = response.decode("utf-8").strip()
    print("svar fra robot:",response)
    return response

async def sendCommandReq(reader, writer, command):
    writer.write((command + "\n").encode("utf-8"))
    await writer.drain()
    print("command: " + str(command) + " sent")

    response = await reader.readline()  # reads until \n
    response = response.decode("utf-8").strip()

    print("Svar fra robot:", response)
    return response


async def establishWriteReadConnection():
    reader, writer = await asyncio.open_connection(ROBOT_IP,PORT)
    
    return reader, writer