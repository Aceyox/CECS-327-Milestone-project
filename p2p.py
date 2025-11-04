import socket
import threading
import json
import time

PEERS = []   # This will be filled by user input

def listen_for_peers(port):
    """Each peer listens for incoming messages."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("0.0.0.0", port))   # Accept from any IP
    s.listen(5)
    print(f"[PEER {port}] Listening for connections...")

    while True:
        conn, addr = s.accept()
        try:
            data = conn.recv(1024).decode()
            if data:
                try:
                    msg = json.loads(data)
                    print(f"\n[PEER {port}] <<< Received from {addr}: {msg['message']} @ {msg['timestamp']}")
                except json.JSONDecodeError:
                    print(f"[PEER {port}] Invalid JSON from {addr}: {data}")
        finally:
            conn.close()


def send_to_peers(message, origin_port):
    """Broadcast message to all known peers."""
    alert = {
        "origin": origin_port,
        "message": message,
        "timestamp": time.strftime("%H:%M:%S")
    }
    msg = json.dumps(alert).encode()

    for host, port in PEERS:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, port))
            s.sendall(msg)
            s.close()
            print(f"[PEER {origin_port}] >>> Sent to {host}:{port}")
        except Exception:
            print(f"[PEER {origin_port}] !!! Could not reach {host}:{port}")


def main():
    port = int(input("Enter this peer's port: "))

    # Get peers from user
    print("Enter peers (IP:port). Press ENTER when done.")
    while True:
        peer = input("Peer: ")
        if peer.strip() == "":
            break
        try:
            host, p = peer.split(":")
            PEERS.append((host, int(p)))
        except:
            print("Invalid format. Use IP:port (ex: 192.168.1.10:6002)")

    print(f"[PEER {port}] Known peers: {PEERS}")

    # Start listener thread
    threading.Thread(target=listen_for_peers, args=(port,), daemon=True).start()

    time.sleep(1)
    print(f"[PEER {port}] Ready to broadcast alerts.")

    # Input loop for sending messages
    while True:
        msg = input("Enter message to broadcast (or 'exit'): ")
        if msg.lower() == "exit":
            break
        send_to_peers(msg, port)


if __name__ == "__main__":
    main()