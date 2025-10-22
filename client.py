import socket
import json
import uuid

HOST = "127.0.0.1"
PORT = 5050

#Dictionary for an example alert message 
alert = {
    "id": str(uuid.uuid4()),
    "disaster_type": "Earthquake",
    "region": "California",
    "severity": "High",
    "magnitude": 5.8
}

#Creates a TCP socket and connect to the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

#Convert the dictionary to JSON and send it to the server
s.sendall(json.dumps(alert).encode())

#Wait for the server's response and decode it
data = s.recv(1024).decode()

print("")
print("Server reply:", data)
print("")


s.close()
