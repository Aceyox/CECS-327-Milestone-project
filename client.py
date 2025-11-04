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
#Creates a TCP socket and connect to the server
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(json.dumps(alert).encode())   #Convert the dictionary to JSON and send it to the server

    #Wait for the server's response and decode it
    data = s.recv(1024).decode()
    print("Server reply:", data)
