import socket
import json
import threading

HOST = "127.0.0.1"
PORT = 5050

alerts_log = []
lock = threading.Lock()

def handle_client(conn, addr):
    try:
        data = conn.recv(1024).decode()
        if not data:
            return

        alert = json.loads(data)
        dtype = alert.get("disaster_type", alert.get("type", "Unknown"))
        region = alert.get("region", "Unknown")

        # Critical section — safely update shared list
        with lock:
            alerts_log.append(alert)
            print("\n-------------------------------")
            print(f"[CLIENT CONNECTED] {addr}")
            print(f"Alert logged safely:")
            print(f"  • Disaster Type : {dtype}")
            print(f"  • Region        : {region}")
            print(f"  • Full Alert    : {alert}")
            print("-------------------------------\n")

        reply = {"status": "OK", "message": "Alert received successfully"}
        conn.sendall(json.dumps(reply).encode())

    except Exception as e:
        print(f"[ERROR] {addr}: {e}")
    finally:
        conn.close()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"[SERVER READY] Listening on {HOST}:{PORT}")

    while True:
        conn, addr = s.accept()
        t = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
        t.start()
        print(f"\n[NEW CONNECTION] {addr} handled in thread {t.name}")

if __name__ == "__main__":
    main()
