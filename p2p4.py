import socket
import threading
import json
import time
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Set
import queue

PEERS = []  # (host, port, area) tuples

# Lamport Clock for event ordering
class LamportClock:
    def __init__(self):
        self.time = 0
        self.lock = threading.Lock()
    
    def tick(self):
        """Increment clock on local event"""
        with self.lock:
            self.time += 1
            return self.time
    
    def update(self, received_time):
        """Update clock on message receipt"""
        with self.lock:
            self.time = max(self.time, received_time) + 1
            return self.time
    
    def get(self):
        with self.lock:
            return self.time


# Message types
class MessageType(Enum):
    ALERT = "alert"
    REQUEST = "request"           # Ricart-Agrawala: Request critical section
    REPLY = "reply"               # Ricart-Agrawala: Grant permission
    RELEASE = "release"           # Ricart-Agrawala: Release critical section
    PREPARE = "prepare"           # 2PC: Prepare phase
    COMMIT = "commit"             # 2PC: Commit decision
    ABORT = "abort"               # 2PC: Abort decision
    VOTE_YES = "vote_yes"         # 2PC: Participant votes yes
    VOTE_NO = "vote_no"           # 2PC: Participant votes no
    ACK = "ack"                   # 2PC: Acknowledgment


@dataclass
class Message:
    msg_type: MessageType
    sender_port: int
    lamport_time: int
    content: str = ""
    transaction_id: Optional[str] = None
    target_areas: Optional[List[str]] = None  # NEW: Which areas should receive this
    sender_area: Optional[str] = None         # NEW: Sender's area
    
    def to_json(self):
        data = asdict(self)
        data['msg_type'] = self.msg_type.value
        return json.dumps(data)
    
    @staticmethod
    def from_json(data):
        msg_dict = json.loads(data)
        msg_dict['msg_type'] = MessageType(msg_dict['msg_type'])
        return Message(**msg_dict)


class RicartAgrawala:
    """Distributed Mutual Exclusion using Ricart-Agrawala algorithm"""
    
    def __init__(self, node_port: int, clock: LamportClock, num_peers: int):
        self.node_port = node_port
        self.clock = clock
        self.num_peers = num_peers
        
        self.requesting = False
        self.in_critical_section = False
        self.request_timestamp = 0
        self.replies_received = 0
        self.deferred_replies: List[int] = []  # Ports to reply to later
        
        self.reply_queue = queue.Queue()
        self.lock = threading.Lock()
    
    def request_critical_section(self, send_func):
        """Request access to critical section"""
        with self.lock:
            self.requesting = True
            self.request_timestamp = self.clock.tick()
            self.replies_received = 0
        
        print(f"\n[MUTEX] Requesting critical section at Lamport time {self.request_timestamp}")
        
        # Send REQUEST to all peers
        msg = Message(
            msg_type=MessageType.REQUEST,
            sender_port=self.node_port,
            lamport_time=self.request_timestamp,
            content="critical_section_request"
        )
        send_func(msg)
        
        # Wait for replies from all peers
        while self.replies_received < self.num_peers:
            time.sleep(0.1)
        
        with self.lock:
            self.in_critical_section = True
            self.requesting = False
        
        print(f"[MUTEX] ✓ Entered critical section")
    
    def release_critical_section(self, send_func):
        """Release critical section and send deferred replies"""
        with self.lock:
            self.in_critical_section = False
            deferred = self.deferred_replies.copy()
            self.deferred_replies.clear()
        
        print(f"[MUTEX] Released critical section")
        
        # Send RELEASE to all peers
        msg = Message(
            msg_type=MessageType.RELEASE,
            sender_port=self.node_port,
            lamport_time=self.clock.tick(),
            content="release"
        )
        send_func(msg)
        
        # Send deferred replies
        for port in deferred:
            reply_msg = Message(
                msg_type=MessageType.REPLY,
                sender_port=self.node_port,
                lamport_time=self.clock.tick(),
                content=f"deferred_reply_to_{port}"
            )
            send_func(reply_msg, specific_port=port)
    
    def handle_request(self, msg: Message, send_func):
        """Handle incoming REQUEST message"""
        with self.lock:
            # Defer reply if we're in CS or requesting with higher priority
            should_defer = (
                self.in_critical_section or
                (self.requesting and 
                 (self.request_timestamp < msg.lamport_time or
                  (self.request_timestamp == msg.lamport_time and self.node_port < msg.sender_port)))
            )
            
            if should_defer:
                self.deferred_replies.append(msg.sender_port)
                print(f"[MUTEX] Deferring reply to peer {msg.sender_port}")
                return
        
        # Send immediate reply
        reply = Message(
            msg_type=MessageType.REPLY,
            sender_port=self.node_port,
            lamport_time=self.clock.tick(),
            content=f"reply_to_{msg.sender_port}"
        )
        send_func(reply, specific_port=msg.sender_port)
        print(f"[MUTEX] Sent immediate reply to peer {msg.sender_port}")
    
    def handle_reply(self, msg: Message):
        """Handle incoming REPLY message"""
        with self.lock:
            self.replies_received += 1
            print(f"[MUTEX] Received reply {self.replies_received}/{self.num_peers} from peer {msg.sender_port}")


class TwoPhaseCommit:
    """Two-Phase Commit protocol for atomic transactions"""
    
    def __init__(self, node_port: int, clock: LamportClock):
        self.node_port = node_port
        self.clock = clock
        
        # Coordinator state
        self.active_transactions: Dict[str, dict] = {}
        
        # Participant state
        self.prepared_transactions: Dict[str, bool] = {}
        
        self.lock = threading.Lock()
    
    def start_transaction_as_coordinator(self, transaction_id: str, transaction_data: str, send_func) -> bool:
        """Phase 1: Coordinator sends PREPARE to all participants"""
        with self.lock:
            self.active_transactions[transaction_id] = {
                'votes': {},
                'state': 'preparing',
                'data': transaction_data
            }
        
        print(f"\n[2PC COORDINATOR] Starting transaction {transaction_id}")
        print(f"[2PC COORDINATOR] Phase 1: Sending PREPARE to all peers...")
        
        # Send PREPARE to all peers
        msg = Message(
            msg_type=MessageType.PREPARE,
            sender_port=self.node_port,
            lamport_time=self.clock.tick(),
            content=transaction_data,
            transaction_id=transaction_id
        )
        send_func(msg)
        
        # Wait for votes (with timeout)
        timeout = time.time() + 5
        while time.time() < timeout:
            with self.lock:
                tx = self.active_transactions.get(transaction_id)
                if tx and len(tx['votes']) >= len(PEERS):
                    break
            time.sleep(0.1)
        
        # Phase 2: Make decision
        with self.lock:
            tx = self.active_transactions[transaction_id]
            votes = tx['votes']
            all_yes = all(vote == 'yes' for vote in votes.values())
            decision = MessageType.COMMIT if all_yes else MessageType.ABORT
            tx['state'] = 'committed' if all_yes else 'aborted'
        
        print(f"[2PC COORDINATOR] Votes received: {votes}")
        print(f"[2PC COORDINATOR] Phase 2: Decision = {decision.value.upper()}")
        
        # Send decision
        decision_msg = Message(
            msg_type=decision,
            sender_port=self.node_port,
            lamport_time=self.clock.tick(),
            content=f"transaction_{decision.value}",
            transaction_id=transaction_id
        )
        send_func(decision_msg)
        
        return all_yes
    
    def handle_prepare(self, msg: Message, send_func):
        """Participant: Handle PREPARE message"""
        tx_id = msg.transaction_id
        
        # Simulate decision logic (you can add custom validation)
        can_commit = True  # In real scenario, check if transaction is valid
        
        with self.lock:
            self.prepared_transactions[tx_id] = can_commit
        
        vote = MessageType.VOTE_YES if can_commit else MessageType.VOTE_NO
        print(f"[2PC PARTICIPANT] Received PREPARE for {tx_id}, voting {vote.value.upper()}")
        
        # Send vote back to coordinator
        vote_msg = Message(
            msg_type=vote,
            sender_port=self.node_port,
            lamport_time=self.clock.tick(),
            content=f"vote_{vote.value}",
            transaction_id=tx_id
        )
        send_func(vote_msg, specific_port=msg.sender_port)
    
    def handle_vote(self, msg: Message):
        """Coordinator: Handle vote from participant"""
        tx_id = msg.transaction_id
        vote = 'yes' if msg.msg_type == MessageType.VOTE_YES else 'no'
        
        with self.lock:
            if tx_id in self.active_transactions:
                self.active_transactions[tx_id]['votes'][msg.sender_port] = vote
                print(f"[2PC COORDINATOR] Received {vote.upper()} vote from peer {msg.sender_port}")
    
    def handle_decision(self, msg: Message):
        """Participant: Handle final decision from coordinator"""
        tx_id = msg.transaction_id
        decision = "COMMIT" if msg.msg_type == MessageType.COMMIT else "ABORT"
        
        with self.lock:
            if tx_id in self.prepared_transactions:
                del self.prepared_transactions[tx_id]
        
        print(f"[2PC PARTICIPANT] Transaction {tx_id}: {decision}")


class P2PNode:
    def __init__(self, port: int, area: str):
        self.port = port
        self.area = area.upper()
        self.clock = LamportClock()
        self.ricart_agrawala: Optional[RicartAgrawala] = None
        self.two_phase_commit = TwoPhaseCommit(port, self.clock)
        self.log_file = f"peer_{port}_{area}_log.txt"
        
        # Clear log file
        with open(self.log_file, 'w') as f:
            f.write(f"=== Peer {port} (Area: {self.area}) Event Log ===\n")
    
    def log_event(self, event: str):
        """Log events with Lamport timestamp"""
        timestamp = self.clock.get()
        log_entry = f"[LC:{timestamp}] {time.strftime('%H:%M:%S')} - {event}\n"
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
        print(f"[LOG] {log_entry.strip()}")
    
    def should_receive_alert(self, msg: Message) -> bool:
        """Determine if this node should receive an alert based on area"""
        # If no target areas specified, everyone gets it
        if not msg.target_areas:
            return True
        
        # Check if our area is in the target list
        return self.area in [a.upper() for a in msg.target_areas]
    
    def listen_for_peers(self):
        """Listen for incoming messages"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", self.port))
        s.listen(5)
        print(f"[PEER {self.port} - Area {self.area}] Listening for connections...")

        while True:
            conn, addr = s.accept()
            try:
                data = conn.recv(4096).decode()
                if data:
                    try:
                        msg = Message.from_json(data)
                        self.clock.update(msg.lamport_time)
                        self.handle_message(msg)
                    except json.JSONDecodeError:
                        print(f"[PEER {self.port}] Invalid JSON from {addr}")
            finally:
                conn.close()
    
    def handle_message(self, msg: Message):
        """Route messages to appropriate handlers"""
        if msg.msg_type == MessageType.ALERT:
            # Check if this alert is for our area
            if self.should_receive_alert(msg):
                areas_str = f"[{', '.join(msg.target_areas)}]" if msg.target_areas else "[ALL AREAS]"
                print(f"\n{'='*60}")
                print(f"🚨 ALERT RECEIVED - {areas_str}")
                print(f"From: Peer {msg.sender_port} (Area {msg.sender_area})")
                print(f"Message: {msg.content}")
                print(f"{'='*60}\n")
                self.log_event(f"Alert from Area {msg.sender_area}: {msg.content}")
            else:
                # Alert not for our area - ignore silently
                pass
        
        elif msg.msg_type == MessageType.REQUEST:
            if self.ricart_agrawala:
                self.ricart_agrawala.handle_request(msg, self.send_message)
        
        elif msg.msg_type == MessageType.REPLY:
            if self.ricart_agrawala:
                self.ricart_agrawala.handle_reply(msg)
        
        elif msg.msg_type == MessageType.PREPARE:
            self.two_phase_commit.handle_prepare(msg, self.send_message)
        
        elif msg.msg_type in [MessageType.VOTE_YES, MessageType.VOTE_NO]:
            self.two_phase_commit.handle_vote(msg)
        
        elif msg.msg_type in [MessageType.COMMIT, MessageType.ABORT]:
            self.two_phase_commit.handle_decision(msg)
    
    def send_message(self, msg: Message, specific_port: Optional[int] = None):
        """Send message to peers (all or specific)"""
        self.clock.tick()
        msg.lamport_time = self.clock.get()
        msg.sender_area = self.area  # Always include sender's area
        encoded_msg = msg.to_json().encode()
        
        targets = [(h, p, a) for h, p, a in PEERS if p == specific_port] if specific_port else PEERS
        
        for host, port, area in targets:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((host, port))
                s.sendall(encoded_msg)
                s.close()
            except Exception as e:
                print(f"[PEER {self.port}] !!! Could not reach {host}:{port}")
    
    def broadcast_alert(self, message: str, target_areas: Optional[List[str]] = None):
        """Broadcast alert to specific areas or all areas"""
        if target_areas:
            areas_str = ", ".join(target_areas)
            self.log_event(f"Broadcasting alert to areas [{areas_str}]: {message}")
            print(f"\n[BROADCAST] Sending to areas: {areas_str}")
        else:
            self.log_event(f"Broadcasting alert to ALL areas: {message}")
            print(f"\n[BROADCAST] Sending to ALL areas")
        
        msg = Message(
            msg_type=MessageType.ALERT,
            sender_port=self.port,
            lamport_time=self.clock.tick(),
            content=message,
            target_areas=target_areas,
            sender_area=self.area
        )
        self.send_message(msg)
    
    def demo_mutual_exclusion(self):
        """Demo: Access critical section (simulate traffic signal coordination)"""
        if not self.ricart_agrawala:
            print("[ERROR] Ricart-Agrawala not initialized!")
            return
        
        print(f"\n{'='*60}")
        print(f"🚦 TRAFFIC SIGNAL COORDINATION DEMO")
        print(f"Peer {self.port} (Area {self.area}) wants to change traffic signal timing")
        print(f"{'='*60}")
        
        # Request critical section
        self.ricart_agrawala.request_critical_section(self.send_message)
        
        # Simulate critical section work (e.g., coordinate traffic signals)
        self.log_event("CRITICAL SECTION: Adjusting traffic signal timing")
        print(f"[CRITICAL SECTION] Peer {self.port} is coordinating signals...")
        time.sleep(2)  # Simulate work
        self.log_event("CRITICAL SECTION: Traffic signal coordination complete")
        
        # Release critical section
        self.ricart_agrawala.release_critical_section(self.send_message)
    
    def demo_two_phase_commit(self, transaction_data: str):
        """Demo: Coordinate atomic transaction across nodes"""
        tx_id = f"tx_{self.port}_{int(time.time())}"
        
        print(f"\n{'='*60}")
        print(f"🔄 TWO-PHASE COMMIT DEMO")
        print(f"Peer {self.port} (Area {self.area}) coordinating transaction: {transaction_data}")
        print(f"{'='*60}")
        
        success = self.two_phase_commit.start_transaction_as_coordinator(
            tx_id, transaction_data, self.send_message
        )
        
        result = "SUCCESS ✓" if success else "FAILED ✗"
        self.log_event(f"Transaction {tx_id}: {result}")
        print(f"\n[RESULT] Transaction {result}")


def main():
    port = int(input("Enter this peer's port: "))
    area = input("Enter your area (e.g., NORTH, SOUTH, DOWNTOWN, HIGHWAY1): ").strip()
    
    if not area:
        print("Area cannot be empty! Using 'UNKNOWN' as default.")
        area = "UNKNOWN"
    
    node = P2PNode(port, area)

    # Get peers from user
    print("\nEnter peers (IP:port:area). Press ENTER when done.")
    print("Example: 192.168.1.100:6002:SOUTH")
    while True:
        peer = input("Peer: ")
        if peer.strip() == "":
            break
        try:
            parts = peer.split(":")
            if len(parts) == 3:
                host, p, peer_area = parts
                PEERS.append((host, int(p), peer_area.upper()))
            else:
                print("Invalid format. Use IP:port:area (ex: 192.168.1.10:6002:NORTH)")
        except:
            print("Invalid format. Use IP:port:area (ex: 192.168.1.10:6002:NORTH)")

    print(f"\n[PEER {port} - Area {area}] Known peers:")
    for host, p, a in PEERS:
        print(f"  - {host}:{p} (Area: {a})")
    
    # Initialize Ricart-Agrawala
    if PEERS:
        node.ricart_agrawala = RicartAgrawala(port, node.clock, len(PEERS))
        print(f"\n[PEER {port}] Ricart-Agrawala initialized with {len(PEERS)} peers")

    # Start listener thread
    threading.Thread(target=node.listen_for_peers, daemon=True).start()
    time.sleep(1)

    print(f"\n{'='*60}")
    print(f"✓ Peer {port} (Area: {area.upper()}) ready!")
    print(f"{'='*60}")
    print("\nCommands:")
    print("  msg <text>                    - Broadcast alert to ALL areas")
    print("  msg <area1,area2> <text>      - Broadcast alert to specific areas")
    print("  mutex                         - Demo distributed mutual exclusion")
    print("  2pc <data>                    - Demo two-phase commit transaction")
    print("  exit                          - Exit program")
    print(f"{'='*60}")
    print("\nExamples:")
    print("  msg Traffic jam on Main St")
    print("  msg NORTH,SOUTH Accident on Highway 1")
    print("  msg DOWNTOWN Road closure on 5th Ave")
    print(f"{'='*60}\n")

    # Command loop
    while True:
        cmd = input(f"[{port}-{area}]> ").strip()
        
        if cmd.lower() == "exit":
            break
        elif cmd.startswith("msg "):
            rest = cmd[4:].strip()
            
            # Check if first word contains commas (area list)
            parts = rest.split(None, 1)
            if len(parts) == 2 and ',' in parts[0]:
                # Format: msg NORTH,SOUTH message text
                area_list = [a.strip().upper() for a in parts[0].split(',')]
                message = parts[1]
                node.broadcast_alert(message, target_areas=area_list)
            elif len(parts) == 2 and parts[0].isupper() and ',' not in parts[0]:
                # Format: msg NORTH message text (single area)
                area_list = [parts[0].upper()]
                message = parts[1]
                node.broadcast_alert(message, target_areas=area_list)
            else:
                # Format: msg message text (all areas)
                message = rest
                node.broadcast_alert(message)
        elif cmd == "mutex":
            threading.Thread(target=node.demo_mutual_exclusion, daemon=True).start()
        elif cmd.startswith("2pc "):
            transaction_data = cmd[4:]
            threading.Thread(
                target=node.demo_two_phase_commit,
                args=(transaction_data,),
                daemon=True
            ).start()
        else:
            print("Unknown command. Use: msg, mutex, 2pc, or exit")


if __name__ == "__main__":
    main()