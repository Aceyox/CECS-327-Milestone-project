
import socket
import json
import threading
import argparse

db = {}
lock_table = {}
staged_data = {}

def handle_prepare(txid, writes):
    for k in writes:
        if k in lock_table and lock_table[k] != txid:
            print(f"[{txid[:6]}] prepare -> abort (lock conflict)")
            return {"type": "VOTE_ABORT"}
    for k in writes:
        lock_table[k] = txid

    staged_data[txid] = writes
    print(f"[{txid[:6]}] prepare -> vote commit")
    return {"type": "VOTE_COMMIT"}

def handle_commit(txid):
    if txid in staged_data:
        for k, v in staged_data[txid].items():
            db[k] = v
        del staged_data[txid]

    for k in list(lock_table):
        if lock_table[k] == txid:
            del lock_table[k]

    print(f"[{txid[:6]}] commit applied")
    return {"type": "ACK", "msg": "committed"}

def handle_abort(txid):
    if txid in staged_data:
        del staged_data[txid]

    for k in list(lock_table):
        if lock_table[k] == txid:
            del lock_table[k]

    print(f"[{txid[:6]}] aborted")
    return {"type": "ACK", "msg": "aborted"}

def handle_client(conn, addr):
    try:
        msg = json.loads(conn.recv(4096).decode())
        t = msg.get("type")
        txid = msg.get("txid")

        if t == "PREPARE":
            resp = handle_prepare(txid, msg["writes"])
        elif t == "COMMIT":
            resp = handle_commit(txid)
        elif t == "ABORT":
            resp = handle_abort(txid)
        else:
            resp = {"type": "ERROR", "msg": "unknown"}

        conn.sendall(json.dumps(resp).encode())
    except Exception as e:
        print("participant err:", e)
    finally:
        conn.close()

def run_server(host, port):
    print(f"\nParticipant running on {host}:{port}\n")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    s.listen(10)
    while True:
        c, a = s.accept()
        threading.Thread(target=handle_client, args=(c,a),daemon=True).start()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", required=True)
    args = p.parse_args()
    run_server(args.host, int(args.port))
