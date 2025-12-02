import subprocess
import time
import socket
import json
import threading
import random
from typing import List, Tuple

class TestParticipant:
    """Enhanced participant for testing with fault injection"""
    
    def __init__(self, port: int):
        self.port = port
        self.process = None
        self.should_fail = False
        self.fail_on_commit = False
        self.delay_response = 0
        
    def start(self):
        """Start the participant server"""
        self.process = subprocess.Popen(
            ['python', 'tm_participant.py', '--port', str(self.port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        time.sleep(0.5)  # Wait for server to start
        
    def stop(self):
        """Stop the participant server"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            
    def is_running(self):
        """Check if participant is still running"""
        return self.process and self.process.poll() is None


class TwoPhaseCommitTester:
    """Test harness for 2PC protocol"""
    
    def __init__(self):
        self.participants = []
        self.base_port = 7000
        
    def setup_participants(self, num_participants: int) -> List[Tuple[str, int]]:
        """Start multiple participant nodes"""
        nodes = []
        for i in range(num_participants):
            port = self.base_port + i
            participant = TestParticipant(port)
            participant.start()
            self.participants.append(participant)
            nodes.append(("127.0.0.1", port))
        return nodes
        
    def teardown(self):
        """Stop all participants"""
        for p in self.participants:
            p.stop()
        self.participants = []
        
    def simulate_network_partition(self, node_index: int):
        """Simulate network partition by killing a specific node"""
        if node_index < len(self.participants):
            self.participants[node_index].stop()
            print(f"[TEST] Simulated network partition: Node {node_index} disconnected")
            
    def send_transaction(self, nodes: List[Tuple[str, int]], writes: dict) -> dict:
        """Send a transaction to the coordinator"""
        txid = f"test-tx-{random.randint(1000, 9999)}"
        
        print(f"\n{'------------'}")
        print(f"TEST TRANSACTION: {txid}")
        print(f"Writes: {writes}")
        print(f"{'------------'}\n")
        
        # Simulate coordinator behavior
        votes = []
        for i, node in enumerate(nodes):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect(node)
                
                prep = {"type": "PREPARE", "txid": txid, "writes": writes}
                s.sendall(json.dumps(prep).encode())
                
                resp = json.loads(s.recv(4096).decode())
                s.close()
                
                vote = resp.get("type")
                votes.append((i, node, vote))
                print(f"[PREPARE] Node {i} at {node[0]}:{node[1]} -> {vote}")
            except Exception as e:
                votes.append((i, node, "TIMEOUT"))
                print(f"[PREPARE] Node {i} at {node[0]}:{node[1]} -> TIMEOUT ({e})")
        
        # Decide commit or abort
        decision = "COMMIT" if all(v[2] == "VOTE_COMMIT" for v in votes) else "ABORT"
        print(f"\n[DECISION] {decision}\n")
        
        # Send decision
        for i, node, vote in votes:
            if vote == "TIMEOUT":
                continue
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect(node)
                
                msg = {"type": decision, "txid": txid}
                s.sendall(json.dumps(msg).encode())
                
                resp = json.loads(s.recv(4096).decode())
                s.close()
                print(f"[{decision}] Node {i} -> {resp.get('msg', 'ok')}")
            except Exception as e:
                print(f"[{decision}] Node {i} -> FAILED ({e})")
        
        return {"txid": txid, "decision": decision, "votes": votes}


 
# TEST CASE 1: Network Partition During Prepare Phase
 
def test_network_partition_during_prepare():
    """
    Test behavior when a node becomes unreachable during the prepare phase.
    Expected: Transaction should ABORT because not all nodes can participate.
    """
    print("\n" + "------------")
    print("TEST 1: NETWORK PARTITION DURING PREPARE PHASE")
    print("------------")
    
    tester = TwoPhaseCommitTester()
    nodes = tester.setup_participants(3)
    
    try:
        time.sleep(1)
        
        # Simulate network partition: kill node 1 before transaction
        print("\n[SETUP] Simulating network partition on Node 1...")
        tester.simulate_network_partition(1)
        time.sleep(0.5)
        
        # Try to commit a transaction
        result = tester.send_transaction(
            nodes,
            {"alert_type": "earthquake", "severity": "high"}
        )
        
        # Verify result
        print(f"\n[RESULT] Decision: {result['decision']}")
        if result['decision'] == "ABORT":
            print("[PASS] Transaction correctly aborted due to network partition")
        else:
            print("[FAIL] Transaction should have aborted")
            
    finally:
        tester.teardown()


 
# TEST CASE 2: Node Failure During Commit Phase
 
def test_node_failure_during_commit():
    """
    Test behavior when a node crashes after voting COMMIT but before receiving
    the commit message.
    Expected: Other nodes should still commit successfully.
    """
    print("\n" + "------------")
    print("TEST 2: NODE FAILURE DURING COMMIT PHASE")
    print("------------")
    
    tester = TwoPhaseCommitTester()
    nodes = tester.setup_participants(3)
    
    try:
        time.sleep(1)
        
        # First, send prepare messages and collect votes
        txid = f"test-tx-{random.randint(1000, 9999)}"
        writes = {"alert_type": "flood", "region": "coastal"}
        
        print(f"\n[PHASE 1] Sending PREPARE messages...")
        votes = []
        for i, node in enumerate(nodes):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect(node)
            
            prep = {"type": "PREPARE", "txid": txid, "writes": writes}
            s.sendall(json.dumps(prep).encode())
            
            resp = json.loads(s.recv(4096).decode())
            s.close()
            
            vote = resp.get("type")
            votes.append(vote)
            print(f"  Node {i}: {vote}")
        
        # All voted commit, so decision is COMMIT
        decision = "COMMIT"
        print(f"\n[DECISION] {decision}")
        
        # Kill node 1 before sending commit
        print("\n[FAULT INJECTION] Killing Node 1 before COMMIT phase...")
        tester.simulate_network_partition(1)
        time.sleep(0.3)
        
        # Send commit to remaining nodes
        print(f"\n[PHASE 2] Sending {decision} messages...")
        for i, node in enumerate(nodes):
            if i == 1:  # Skip the killed node
                print(f"  Node {i}: SKIPPED (node is down)")
                continue
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect(node)
                
                msg = {"type": decision, "txid": txid}
                s.sendall(json.dumps(msg).encode())
                
                resp = json.loads(s.recv(4096).decode())
                s.close()
                print(f"  Node {i}: {resp.get('msg', 'ok')}")
            except Exception as e:
                print(f"  Node {i}: FAILED ({e})")
        
    finally:
        tester.teardown()


 
# TEST CASE 3: Simultaneous Conflicting Writes
 
def test_simultaneous_writes():
    """
    Test behavior when two transactions try to write to the same key simultaneously.
    Expected: One should succeed, one should abort due to lock conflict.
    """
    print("\n" + "------------")
    print("TEST 3: SIMULTANEOUS CONFLICTING WRITES")
    print("------------")
    
    tester = TwoPhaseCommitTester()
    nodes = tester.setup_participants(2)
    
    try:
        time.sleep(1)
        
        results = []
        
        def transaction_thread(tx_id: int, value: str):
            """Run a transaction in a separate thread"""
            txid = f"tx-{tx_id}-{random.randint(100, 999)}"
            writes = {"disaster_count": value}
            
            print(f"\n[TX{tx_id}] Starting transaction {txid}")
            
            # Prepare phase
            votes = []
            for i, node in enumerate(nodes):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(2)
                    s.connect(node)
                    
                    prep = {"type": "PREPARE", "txid": txid, "writes": writes}
                    s.sendall(json.dumps(prep).encode())
                    
                    resp = json.loads(s.recv(4096).decode())
                    s.close()
                    
                    vote = resp.get("type")
                    votes.append(vote)
                    print(f"[TX{tx_id}] Node {i}: {vote}")
                except Exception as e:
                    votes.append("VOTE_ABORT")
                    print(f"[TX{tx_id}] Node {i}: ERROR ({e})")
            
            # Decision
            decision = "COMMIT" if all(v == "VOTE_COMMIT" for v in votes) else "ABORT"
            print(f"[TX{tx_id}] Decision: {decision}")
            
            # Commit/Abort phase
            for i, node in enumerate(nodes):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(2)
                    s.connect(node)
                    
                    msg = {"type": decision, "txid": txid}
                    s.sendall(json.dumps(msg).encode())
                    
                    resp = json.loads(s.recv(4096).decode())
                    s.close()
                except Exception as e:
                    pass
            
            results.append({"tx_id": tx_id, "decision": decision})
        
        # Start two transactions simultaneously
        t1 = threading.Thread(target=transaction_thread, args=(1, "100"))
        t2 = threading.Thread(target=transaction_thread, args=(2, "200"))
        
        print("\n[SETUP] Launching two simultaneous transactions on same key...")
        t1.start()
        time.sleep(0.1)  # Small delay to ensure some overlap
        t2.start()
        
        t1.join()
        t2.join()
        
        # Analyze results
        print("\n" + "------------")
        print("FINAL RESULTS:")
        print("------------")
        commits = sum(1 for r in results if r['decision'] == 'COMMIT')
        aborts = sum(1 for r in results if r['decision'] == 'ABORT')
        
        for r in results:
            print(f"  TX{r['tx_id']}: {r['decision']}")
        
        print(f"\nCommits: {commits}, Aborts: {aborts}")
        
        if commits == 1 and aborts == 1:
            print("[PASS] Exactly one transaction committed (proper lock handling)")
        elif commits == 2:
            print("[FAIL] Both transactions committed (lost update)")
        else:
            print("[FAIL] Both transactions aborted (potential deadlock)")
            
    finally:
        tester.teardown()


 
# TEST CASE 4: Cascading Write Conflicts
 
def test_cascading_conflicts():
    """
    Test with multiple transactions writing to overlapping key sets.
    Expected: Proper serialization through locks.
    """
    print("\n" + "------------")
    print("TEST 4: CASCADING WRITE CONFLICTS (3 TRANSACTIONS)")
    print("------------")
    
    tester = TwoPhaseCommitTester()
    nodes = tester.setup_participants(2)
    
    try:
        time.sleep(1)
        
        # TX1: writes to keys A, B
        # TX2: writes to keys B, C (conflicts on B)
        # TX3: writes to keys C, D (conflicts on C)
        
        test_cases = [
            (1, {"key_A": "tx1", "key_B": "tx1"}),
            (2, {"key_B": "tx2", "key_C": "tx2"}),
            (3, {"key_C": "tx3", "key_D": "tx3"})
        ]
        
        results = []
        
        def run_transaction(tx_num, writes):
            result = tester.send_transaction(nodes, writes)
            results.append({"tx": tx_num, "decision": result['decision']})
        
        threads = []
        for tx_num, writes in test_cases:
            t = threading.Thread(target=run_transaction, args=(tx_num, writes))
            threads.append(t)
            t.start()
            time.sleep(0.15)  # Stagger starts slightly
        
        for t in threads:
            t.join()
        
        print("\n" + "------------")
        print("RESULTS:")
        for r in results:
            print(f"  TX{r['tx']}: {r['decision']}")
        
        commits = sum(1 for r in results if r['decision'] == 'COMMIT')
        print(f"\nTotal commits: {commits}/3")
        print("[INFO] At least one should abort due to conflicts")
        
    finally:
        tester.teardown()


 
# RUN ALL TESTS
 
if __name__ == "__main__":
    print("\n" + "------------")
    print("TESTING")
    print("------------")
    
    tests = [
        ("Network Partition During Prepare", test_network_partition_during_prepare),
        ("Node Failure During Commit", test_node_failure_during_commit),
        ("Simultaneous Conflicting Writes", test_simultaneous_writes),
        ("Cascading Write Conflicts", test_cascading_conflicts)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            test_func()
            time.sleep(2)  # Brief pause between tests
        except Exception as e:
            print(f"\n[ERROR] Test '{name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n""------------")
    print("TEST COMPLETE")
    print("------------")
    print("\nNOTE: Review output above to verify expected behaviors.")
    print("Look for [PASS] markers and check participant logs.\n")
