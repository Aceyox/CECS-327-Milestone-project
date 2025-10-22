import socket
import json
import uuid

HOST = "127.0.0.1"
PORT = 5050

alert = {
    "id": str(uuid.uuid4()),
    "disaster_type": "Earthquake",
    "region": "California",
    "severity": "High",
    "magnitude": 5.8
}

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.sendall(json.dumps(alert).encode())

data = s.recv(1024).decode()
print("")
print("Server reply:", data)
print("")


s.close()
