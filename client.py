import socket
import json

HOST = "127.0.0.1"
PORT = 5050

alert = {
    "disaster_type": "Earthquake",
    "region": "California",
    "severity": "High",
    "magnitude": 5.8
}

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(json.dumps(alert).encode())
    data = s.recv(1024).decode()
    print("Server reply:", data)
