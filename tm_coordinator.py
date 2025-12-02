
import socket
import json
import uuid
import argparse

def send_msg(addr, data, timeout=2):
    h, pt = addr
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((h, pt))
    s.sendall(json.dumps(data).encode())
    resp = json.loads(s.recv(4096).decode())
    s.close()
    return resp

def two_phase_commit(nodes, writes):
    txid = str(uuid.uuid4())

    print("\n==== New Transaction ====")
    print("txid =", txid)
    print("writes =", writes)
    print()

    print("-- Prepare Phase --")
    votes = []
    for n in nodes:
        try:
            prep = {"type": "PREPARE", "txid": txid, "writes": writes}
            reply = send_msg(n, prep)
            if reply.get("type") == "VOTE_COMMIT":
                print(f"{n[0]}:{n[1]} -> commit vote")
            else:
                print(f"{n[0]}:{n[1]} -> abort vote")
            votes.append(reply.get("type"))
        except:
            print(f"{n[0]}:{n[1]} -> no reply (timeout)")
            votes.append("VOTE_ABORT")

    if all(v == "VOTE_COMMIT" for v in votes):
        decision = "COMMIT"
    else:
        decision = "ABORT"

    print()
    print("-- Commit Phase --" if decision == "COMMIT" else "-- abort phase --")

    for n in nodes:
        try:
            resp = send_msg(n, {"type": decision, "txid": txid})
            status = resp.get("msg", "ok")
            print(f"sent {decision.lower()} to {n[0]}:{n[1]} ({status})")
        except:
            print(f"failed sending {decision.lower()} to {n[0]}:{n[1]}")

    print()
    print("Transaction Result:", decision)
    print()

    return decision == "COMMIT"

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--participants", nargs="+", required=True)
    p.add_argument("--key", required=True)
    p.add_argument("--value", required=True)
    args = p.parse_args()

    nodes = []
    for x in args.participants:
        h, pt = x.split(":")
        nodes.append((h, int(pt)))

    committed = two_phase_commit(nodes, {args.key: args.value})

    print("RESULT:", "COMMITTED" if committed else "ABORTED")
