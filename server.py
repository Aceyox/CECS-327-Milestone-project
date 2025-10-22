import socket
import json

HOST = "127.0.0.1"
PORT = 5050

#Creates a TCP socket and connects it to the host and port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen()

print(f"Server is running on {HOST}:{PORT}")

#Waits for client to connect
conn, addr = s.accept()
print(f"Server connected via {addr}")

#Data is converted to JSON string when data is received 
data = conn.recv(1024).decode()
alert = json.loads(data)

#Prints data in a format
print("\n*** Disaster Alert ***")
print(f"Disaster Type : {alert.get('disaster_type')}")
print(f"Region        : {alert.get('region')}")
print(f"Severity      : {alert.get('severity')}")
print(f"Magnitude     : {alert.get('magnitude')}")
print("--------------------------------\n")

#Confirmation message back to the client
reply = {"status": "OK", "message": "Alert has been received"}
conn.sendall(json.dumps(reply).encode())

conn.close()
s.close()
