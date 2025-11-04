import socket
import threading
import json
import time

# Manually list peers or load from a small file
PEERS = [("127.0.0.1", 6001), ("127.0.0.1", 6002), ("127.0.0.1", 6003)]

def listen_for_peers(port):
    """Each peer listens for incoming messages."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", port))
    s.listen(5)
    print(f"[PEER {port}] Listening for connections...")
    while True:
        conn, addr = s.accept()
        data = conn.recv(1024).decode()
        if data:
            try:
                msg = json.loads(data)
                print(f"[PEER {port}] Received alert from {addr}: {msg['message']}")
            except json.JSONDecodeError:
                print(f"[PEER {port}] Invalid JSON from {addr}: {data}")
        conn.close()

def send_to_peers(message, origin_port):
    """Broadcast message to all peers except self."""
    alert = {
        "origin": origin_port,
        "message": message,
        "timestamp": time.strftime("%H:%M:%S")
    }
    msg = json.dumps(alert).encode()

    for peer in PEERS:
        host, port = peer
        if port == origin_port:
            continue  # skip self
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(peer)
            s.sendall(msg)
            s.close()
            print(f"[PEER {origin_port}] Sent to {port}")
        except Exception as e:
            print(f"[PEER {origin_port}] Could not reach {port}: {e}")

def main():
    port = int(input("Enter this peer's port: "))
    threading.Thread(target=listen_for_peers, args=(port,), daemon=True).start()

    time.sleep(1)
    print(f"[PEER {port}] Ready to broadcast alerts.")
    while True:
        msg = input("Enter message to broadcast (or 'exit'): ")
        if msg.lower() == "exit":
            break
        send_to_peers(msg, port)

if __name__ == "__main__":
    main()
