import socket
import json

HOST = "127.0.0.1"
PORT = 5050

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print(f"Server is running on {HOST}:{PORT}")
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        data = conn.recv(1024)
        if not data:
            print("No data received.")
        else:
            try:
                msg = json.loads(data.decode())
                print("Received from client:", msg)
            except json.JSONDecodeError:
                msg = {"error": "not json", "raw": data.decode(errors="replace")}
                print("Received non-JSON payload:", msg)

            # send a reply
            reply = {"status": "ok", "echo": msg}
            conn.sendall(json.dumps(reply).encode())
            print("Sent reply to client.")
