import socket
import threading
import json
import time
import random
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple, Optional, Set
import queue

PEERS = []  # (host, port, area) tuples

# Major US Cities
CITIES = {
    "1": {"name": "NEW YORK", "evac": "Central Park Evacuation Zone"},
    "2": {"name": "LOS ANGELES", "evac": "Dodger Stadium Emergency Center"},
    "3": {"name": "CHICAGO", "evac": "Grant Park Evacuation Point"},
    "4": {"name": "HOUSTON", "evac": "NRG Stadium Emergency Shelter"},
    "5": {"name": "PHOENIX", "evac": "Arizona Veterans Memorial Coliseum"}
}

# Disaster Types with variable severity
DISASTERS = {
    "EARTHQUAKE": {
        "severities": ["MODERATE", "HIGH", "CRITICAL", "EXTREME"],
        "tips": [
            "DROP, COVER, and HOLD ON immediately",
            "Stay away from windows and heavy furniture",
            "If outdoors, move away from buildings and power lines",
            "After shaking stops, evacuate to: {evac}"
        ]
    },
    "TSUNAMI": {
        "severities": ["HIGH", "CRITICAL", "EXTREME"],
        "tips": [
            "EVACUATE IMMEDIATELY to higher ground",
            "Do NOT wait for official warning",
            "Move at least 2 miles inland or 100 feet above sea level",
            "Emergency shelter location: {evac}"
        ]
    },
    "FLOOD": {
        "severities": ["LOW", "MODERATE", "HIGH", "CRITICAL"],
        "tips": [
            "Move to higher ground immediately",
            "Do NOT walk or drive through flood waters",
            "Turn off utilities at main switches",
            "Report to evacuation center: {evac}"
        ]
    },
    "WILDFIRE": {
        "severities": ["MODERATE", "HIGH", "CRITICAL", "EXTREME"],
        "tips": [
            "Evacuate immediately if ordered",
            "Close all windows and doors",
            "Wear N95 mask or wet cloth over nose/mouth",
            "Evacuation point: {evac}"
        ]
    },
    "TORNADO": {
        "severities": ["MODERATE", "HIGH", "CRITICAL", "EXTREME"],
        "tips": [
            "Seek shelter in basement or interior room",
            "Stay away from windows",
            "Cover yourself with mattress or heavy blankets",
            "After tornado passes, go to: {evac}"
        ]
    },
    "HURRICANE": {
        "severities": ["LOW", "MODERATE", "HIGH", "CRITICAL", "EXTREME"],
        "tips": [
            "Board up windows and secure outdoor items",
            "Fill bathtubs with water for emergency use",
            "Charge all electronic devices",
            "Emergency shelter: {evac}"
        ]
    },
    "HAZMAT": {
        "severities": ["MODERATE", "HIGH", "CRITICAL"],
        "tips": [
            "Stay indoors and seal all windows/doors",
            "Turn off ventilation systems",
            "Listen to emergency broadcasts",
            "If ordered to evacuate, go to: {evac}"
        ]
    },
    "NUCLEAR": {
        "severities": ["NATIONAL EMERGENCY"],
        "tips": [
            "Seek shelter in basement or center of building",
            "Remove contaminated clothing if outside",
            "Do NOT use phones - keep lines clear",
            "Await further government instructions"
        ]
    }
}

# National Emergency (goes to everyone)
NATIONAL_DISASTERS = ["NUCLEAR", "WAR", "BIOTERRORISM"]


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
    DISASTER = "disaster"
    NATIONAL = "national"
    REQUEST = "request"
    REPLY = "reply"
    RELEASE = "release"
    PREPARE = "prepare"
    COMMIT = "commit"
    ABORT = "abort"
    VOTE_YES = "vote_yes"
    VOTE_NO = "vote_no"
    ACK = "ack"


@dataclass
class Message:
    msg_type: MessageType
    sender_port: int
    lamport_time: int
    content: str = ""
    transaction_id: Optional[str] = None
    target_areas: Optional[List[str]] = None
    sender_area: Optional[str] = None
    disaster_type: Optional[str] = None
    severity: Optional[str] = None
    tips: Optional[List[str]] = None
    
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
        self.deferred_replies: List[int] = []
        
        self.reply_queue = queue.Queue()
        self.lock = threading.Lock()
    
    def request_critical_section(self, send_func):
        """Request access to critical section"""
        with self.lock:
            self.requesting = True
            self.request_timestamp = self.clock.tick()
            self.replies_received = 0
        
        print(f"\n[MUTEX] Requesting critical section at Lamport time {self.request_timestamp}")
        
        msg = Message(
            msg_type=MessageType.REQUEST,
            sender_port=self.node_port,
            lamport_time=self.request_timestamp,
            content="critical_section_request"
        )
        send_func(msg)
        
        while self.replies_received < self.num_peers:
            time.sleep(0.1)
        
        with self.lock:
            self.in_critical_section = True
            self.requesting = False
        
        print(f"[MUTEX] Entered critical section")
    
    def release_critical_section(self, send_func):
        """Release critical section and send deferred replies"""
        with self.lock:
            self.in_critical_section = False
            deferred = self.deferred_replies.copy()
            self.deferred_replies.clear()
        
        print(f"[MUTEX] Released critical section")
        
        msg = Message(
            msg_type=MessageType.RELEASE,
            sender_port=self.node_port,
            lamport_time=self.clock.tick(),
            content="release"
        )
        send_func(msg)
        
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
        self.active_transactions: Dict[str, dict] = {}
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
        
        msg = Message(
            msg_type=MessageType.PREPARE,
            sender_port=self.node_port,
            lamport_time=self.clock.tick(),
            content=transaction_data,
            transaction_id=transaction_id
        )
        send_func(msg)
        
        timeout = time.time() + 5
        while time.time() < timeout:
            with self.lock:
                tx = self.active_transactions.get(transaction_id)
                if tx and len(tx['votes']) >= len(PEERS):
                    break
            time.sleep(0.1)
        
        with self.lock:
            tx = self.active_transactions[transaction_id]
            votes = tx['votes']
            all_yes = all(vote == 'yes' for vote in votes.values())
            decision = MessageType.COMMIT if all_yes else MessageType.ABORT
            tx['state'] = 'committed' if all_yes else 'aborted'
        
        print(f"[2PC COORDINATOR] Votes received: {votes}")
        print(f"[2PC COORDINATOR] Phase 2: Decision = {decision.value.upper()}")
        
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
        can_commit = True
        
        with self.lock:
            self.prepared_transactions[tx_id] = can_commit
        
        vote = MessageType.VOTE_YES if can_commit else MessageType.VOTE_NO
        print(f"[2PC PARTICIPANT] Received PREPARE for {tx_id}, voting {vote.value.upper()}")
        
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
    
    # (These demo methods won't be used; kept to avoid touching your logic)
    def demo_mutual_exclusion(self):
        if not hasattr(self, "ricart_agrawala"):
            print("[ERROR] Ricart-Agrawala not initialized on this object.")
            return

    def demo_two_phase_commit(self, transaction_data: str):
        pass


class P2PNode:
    def __init__(self, port: int, area: str):
        self.port = port
        self.area = area.upper()
        self.clock = LamportClock()
        self.ricart_agrawala: Optional[RicartAgrawala] = None
        self.two_phase_commit = TwoPhaseCommit(port, self.clock)
        self.log_file = f"peer_{port}_{area}_log.txt"
        self.auto_alerts_enabled = False
        
        # Get evacuation location for this city
        self.evac_location = "Local Emergency Shelter"
        for city_data in CITIES.values():
            if city_data["name"] == self.area:
                self.evac_location = city_data["evac"]
                break
        
        with open(self.log_file, 'w') as f:
            f.write(f"=== NATIONAL DISASTER ALERT SYSTEM ===\n")
            f.write(f"Peer {port} - {self.area}\n")
            f.write(f"Evacuation Location: {self.evac_location}\n")
            f.write(f"{'='*50}\n\n")
    
    def log_event(self, event: str):
        """Log events with Lamport timestamp"""
        timestamp = self.clock.get()
        log_entry = f"[LC:{timestamp}] {time.strftime('%H:%M:%S')} - {event}\n"
        with open(self.log_file, 'a') as f:
            f.write(log_entry)
    
    def should_receive_alert(self, msg: Message) -> bool:
        """Determine if this node should receive an alert"""
        if msg.msg_type == MessageType.NATIONAL:
            return True
        
        if not msg.target_areas:
            return True
        
        return self.area in [a.upper() for a in msg.target_areas]
    
    def display_disaster_alert(self, msg: Message):
        """Display formatted disaster alert"""
        is_national = msg.msg_type == MessageType.NATIONAL
        
        if is_national:
            print(f"\n{'='*60}")
            print(f"*** NATIONAL EMERGENCY - ALL AREAS ***")
            print(f"{'='*60}")
        else:
            print(f"\n{'='*60}")
            print(f"*** {msg.disaster_type} ALERT ***")
            print(f"SEVERITY: {msg.severity}")
        
        print(f"FROM: {msg.sender_area}")
        print(f"MESSAGE: {msg.content}")
        print(f"\nSAFETY INSTRUCTIONS:")
        
        if msg.tips:
            for i, tip in enumerate(msg.tips, 1):
                tip = tip.replace("{evac}", self.evac_location)
                print(f"  {i}. {tip}")
        
        if is_national:
            print(f"\n*** STAY CALM - FOLLOW ALL OFFICIAL INSTRUCTIONS ***")
        
        print(f"{'='*60}\n")
        
        self.log_event(f"DISASTER ALERT: {msg.disaster_type} - {msg.content}")
    
    def listen_for_peers(self):
        """Listen for incoming messages"""
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("0.0.0.0", self.port))
        s.listen(5)
        print(f"[PEER {self.port} - {self.area}] Listening for connections...")

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
        if msg.msg_type in [MessageType.DISASTER, MessageType.NATIONAL]:
            if self.should_receive_alert(msg):
                self.display_disaster_alert(msg)
        
        elif msg.msg_type == MessageType.ALERT:
            if self.should_receive_alert(msg):
                areas_str = f"[{', '.join(msg.target_areas)}]" if msg.target_areas else "[ALL AREAS]"
                print(f"\n{'='*60}")
                print(f"CUSTOM ALERT - {areas_str}")
                print(f"From: {msg.sender_area}")
                print(f"Message: {msg.content}")
                print(f"{'='*60}\n")
                self.log_event(f"Custom alert: {msg.content}")
        
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
        """Send message to peers"""
        self.clock.tick()
        msg.lamport_time = self.clock.get()
        msg.sender_area = self.area
        encoded_msg = msg.to_json().encode()
        
        targets = [(h, p, a) for h, p, a in PEERS if p == specific_port] if specific_port else PEERS
        
        for host, port, area in targets:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((host, port))
                s.sendall(encoded_msg)
                s.close()
            except Exception:
                pass
    
    def send_disaster_alert(self, disaster_type: str, custom_message: str = "", target_areas: Optional[List[str]] = None, severity: Optional[str] = None):
        """Send structured disaster alert"""
        if disaster_type not in DISASTERS:
            print(f"[ERROR] Unknown disaster type: {disaster_type}")
            return
        
        disaster_info = DISASTERS[disaster_type]
        is_national = disaster_type in NATIONAL_DISASTERS
        
        # Pick random severity if not specified
        if severity is None:
            severity = random.choice(disaster_info["severities"])
        
        msg_type = MessageType.NATIONAL if is_national else MessageType.DISASTER
        message = custom_message if custom_message else f"{disaster_type} detected in {self.area}"
        
        msg = Message(
            msg_type=msg_type,
            sender_port=self.port,
            lamport_time=self.clock.tick(),
            content=message,
            target_areas=None if is_national else target_areas,
            sender_area=self.area,
            disaster_type=disaster_type,
            severity=severity,
            tips=disaster_info["tips"]
        )
        
        self.send_message(msg)
        
        if is_national:
            print(f"[SENT] *** NATIONAL EMERGENCY ALERT BROADCAST TO ALL AREAS ***")
        else:
            areas_str = ", ".join(target_areas) if target_areas else "ALL AREAS"
            print(f"[SENT] {disaster_type} ({severity}) alert to: {areas_str}")
    
    def auto_disaster_simulator(self):
        """Simulate random disasters automatically"""
        while self.auto_alerts_enabled:
            # Faster alert rate
            time.sleep(random.randint(5, 15))
            
            if not self.auto_alerts_enabled:
                break
            
            disaster_types = list(DISASTERS.keys())
            # National events are still rarer than regional ones
            weights = [1 if d not in NATIONAL_DISASTERS else 0.3 for d in disaster_types]
            disaster = random.choices(disaster_types, weights=weights)[0]
            
            # NATIONAL disasters go to ALL AREAS
            if disaster in NATIONAL_DISASTERS:
                target_areas = None
            else:
                # Non-national disasters only affect specific cities
                all_areas = [city["name"] for city in CITIES.values()]
                num_areas = random.randint(1, min(3, len(all_areas)))
                target_areas = random.sample(all_areas, num_areas)
            
            messages = [
                f"Magnitude 7.2 {disaster.lower()} detected",
                f"Emergency services responding to {disaster.lower()}",
                f"Severe {disaster.lower()} warning in effect",
                f"Multiple reports of {disaster.lower()} activity"
            ]
            
            self.send_disaster_alert(disaster, random.choice(messages), target_areas)
    
    def broadcast_custom_alert(self, message: str, target_areas: Optional[List[str]] = None):
        """Broadcast custom text alert"""
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
        """Demo: Access critical section"""
        if not self.ricart_agrawala:
            print("[ERROR] Ricart-Agrawala not initialized!")
            return
        
        print(f"\n{'='*60}")
        print(f"TRAFFIC SIGNAL COORDINATION DEMO")
        print(f"Peer {self.port} ({self.area}) coordinating signals")
        print(f"{'='*60}")
        
        self.ricart_agrawala.request_critical_section(self.send_message)
        
        self.log_event("CRITICAL SECTION: Adjusting traffic signals")
        print(f"[CRITICAL SECTION] Peer {self.port} coordinating...")
        time.sleep(2)
        self.log_event("CRITICAL SECTION: Complete")
        
        self.ricart_agrawala.release_critical_section(self.send_message)
    
    def demo_two_phase_commit(self, transaction_data: str):
        """Demo: Coordinate atomic transaction"""
        tx_id = f"tx_{self.port}_{int(time.time())}"
        
        print(f"\n{'='*60}")
        print(f"TWO-PHASE COMMIT DEMO")
        print(f"Peer {self.port} ({self.area}) coordinating: {transaction_data}")
        print(f"{'='*60}")
        
        success = self.two_phase_commit.start_transaction_as_coordinator(
            tx_id, transaction_data, self.send_message
        )
        
        result = "SUCCESS" if success else "FAILED"
        self.log_event(f"Transaction {tx_id}: {result}")
        print(f"\n[RESULT] Transaction {result}")

    def auto_discover_local_peers(self_port: int):
        """Interactively auto-discover peers on localhost (like option 2, but callable later)."""
        global PEERS

        print("\nEnter port range to scan (e.g., 6001-6005)")
        port_range = input("Port range: ").strip()

        try:
            start_port, end_port = map(int, port_range.split('-'))
            print(f"\nScanning localhost ports {start_port}-{end_port}...")

            for p in range(start_port, end_port + 1):
                if p != self_port:  # Don't connect to self
                    try:
                        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        test_sock.settimeout(0.5)
                        test_sock.connect(("localhost", p))
                        test_sock.close()

                        # Avoid duplicates
                        if any(peer_port == p for _, peer_port, _ in PEERS):
                            continue

                        print(f"\nFound peer on port {p}")
                        print("Which city is this peer?")
                        for key, city in CITIES.items():
                            print(f"  {key}. {city['name']}")
                        city_num = input("City number: ").strip()

                        if city_num in CITIES:
                            peer_area = CITIES[city_num]["name"]
                            PEERS.append(("localhost", p, peer_area))
                            print(f"Added: localhost:{p} ({peer_area})")
                        else:
                            print("Invalid city number. Skipping this peer.")
                    except Exception:
                        # Port not active, skip
                        pass

            print(f"\nAuto-discovery complete! Now know {len(PEERS)} peers")
        except Exception:
            print("Invalid format. Use something like 6001-6005.")


def main():
    print("="*60)
    print("*** NATIONAL DISASTER ALERT SYSTEM ***")
    print("="*60)
    
    port = int(input("\nEnter this peer's port: "))
    
    print("\nSelect your city:")
    for key, city in CITIES.items():
        print(f"  {key}. {city['name']}")
    
    city_choice = input("\nEnter city number (1-5): ").strip()
    if city_choice not in CITIES:
        print("Invalid choice! Using NEW YORK as default.")
        city_choice = "1"
    
    area = CITIES[city_choice]["name"]
    evac = CITIES[city_choice]["evac"]
    
    print(f"\nConnected to {area}")
    print(f"Your evacuation location: {evac}")
    
    node = P2PNode(port, area)

    print("\n=== PEER CONNECTION SETUP ===")
    print("1. Manual entry (type each peer)")
    print("2. Auto-connect (localhost ports)")
    
    choice = input("\nChoice (1 or 2): ").strip()
    
    if choice == "2":
        # Auto-connect to localhost ports
        print("\nEnter port range to scan (e.g., 6001-6005)")
        port_range = input("Port range: ").strip()
        
        try:
            start_port, end_port = map(int, port_range.split('-'))
            print(f"\nScanning localhost ports {start_port}-{end_port}...")
            
            for p in range(start_port, end_port + 1):
                if p != port:  # Don't connect to self
                    try:
                        test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        test_sock.settimeout(0.5)
                        test_sock.connect(("localhost", p))
                        test_sock.close()
                        
                        print(f"\nFound peer on port {p}")
                        print("Which city is this peer?")
                        for key, city in CITIES.items():
                            print(f"  {key}. {city['name']}")
                        city_num = input("City number: ").strip()
                        
                        if city_num in CITIES:
                            peer_area = CITIES[city_num]["name"]
                            PEERS.append(("localhost", p, peer_area))
                            print(f"Added: localhost:{p} ({peer_area})")
                    except:
                        pass  # Port not active, skip
            
            print(f"\nAuto-discovery complete! Found {len(PEERS)} peers")
        except:
            print("Invalid format. Using manual entry instead.")
            choice = "1"
    
    if choice == "1":
        print("\nEnter peer connections (IP:port:city_number)")
        print("Example: 192.168.1.100:6002:2")
        print("Press ENTER when done.")
        
        while True:
            peer = input("Peer: ").strip()
            if peer == "":
                break
            try:
                parts = peer.split(":")
                if len(parts) == 3:
                    host, p, city_num = parts
                    if city_num in CITIES:
                        peer_area = CITIES[city_num]["name"]
                        PEERS.append((host, int(p), peer_area))
                    else:
                        print(f"Invalid city number. Use 1-5.")
                else:
                    print("Invalid format. Use IP:port:city_number")
            except Exception:
                print("Invalid format. Use IP:port:city_number")

    print(f"\n[PEER {port} - {area}] Known peers:")
    for host, p, a in PEERS:
        print(f"  - {host}:{p} ({a})")
    
    if PEERS:
        node.ricart_agrawala = RicartAgrawala(port, node.clock, len(PEERS))

    threading.Thread(target=node.listen_for_peers, daemon=True).start()
    time.sleep(1)

    print(f"\n{'='*60}")
    print(f"{area} Emergency Center Online")
    print(f"{'='*60}")
    print("\nCOMMANDS:")
    print("  disaster                      - Manual disaster menu")
    print("  national <type>               - Send NATIONAL emergency")
    print("  auto start                    - Start random disaster simulation")
    print("  auto stop                     - Stop random disasters")
    print("  msg <text>                    - Custom alert (your area)")
    print("  msg <city1,city2> <text>      - Custom alert (specific cities)")
    print("  mutex                         - Demo mutual exclusion")
    print("  2pc <data>                    - Demo two-phase commit")
    print("  exit                          - Exit system")
    print(f"{'='*60}")
    print("\nEXAMPLES:")
    print('  disaster')
    print('  national NUCLEAR')
    print('  auto start')
    print('  msg NEW YORK,CHICAGO Power outage reported')
    print(f"{'='*60}\n")

    while True:
        cmd = input(f"[{area}]> ").strip()
        
        if cmd.lower() == "exit":
            node.auto_alerts_enabled = False
            break
        
        elif cmd == "disaster":
            print("\nSELECT DISASTER TYPE:")
            disaster_list = [d for d in DISASTERS.keys() if d not in NATIONAL_DISASTERS]
            for i, disaster in enumerate(disaster_list, 1):
                print(f"  {i}. {disaster}")
            
            choice = input("\nSelect disaster (number): ").strip()
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(disaster_list):
                    disaster = disaster_list[idx]
                    
                    print("\nTarget areas:")
                    print("  0. Your area only")
                    print("  1. All areas")
                    print("  2. Specific areas")
                    
                    target_choice = input("Choice: ").strip()
                    
                    if target_choice == "0":
                        target_areas = [area]
                    elif target_choice == "1":
                        target_areas = None
                    elif target_choice == "2":
                        print("\nAvailable cities:")
                        for key, city in CITIES.items():
                            print(f"  {city['name']}")
                        areas_input = input("Enter cities (comma-separated): ").strip()
                        target_areas = [a.strip().upper() for a in areas_input.split(',') if a.strip()]
                        if not target_areas:
                            target_areas = [area]
                    else:
                        target_areas = [area]
                    
                    custom_msg = input("Custom message (or press ENTER to use default): ").strip()
                    node.send_disaster_alert(disaster, custom_msg, target_areas)
                else:
                    print("Invalid disaster selection.")
            except ValueError:
                print("Please enter a valid number for the disaster.")
        
        elif cmd.lower().startswith("national"):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                print("Usage: national <DISASTER_TYPE> (e.g., national NUCLEAR)")
                continue
            disaster_type = parts[1].strip().upper()
            if disaster_type not in DISASTERS:
                print(f"[ERROR] Unknown national disaster type: {disaster_type}")
                print(f"Available types: {', '.join(d for d in DISASTERS.keys() if d in NATIONAL_DISASTERS)}")
                continue
            custom_msg = input("Custom national message (or press ENTER to use default): ").strip()
            node.send_disaster_alert(disaster_type, custom_msg)
        
        elif cmd.lower().startswith("auto"):
            parts = cmd.split()
            if len(parts) >= 2 and parts[1].lower() == "start":
                if not node.auto_alerts_enabled:
                    node.auto_alerts_enabled = True
                    threading.Thread(target=node.auto_disaster_simulator, daemon=True).start()
                    print("[AUTO] Random disaster simulation started.")
                else:
                    print("[AUTO] Simulation already running.")
            elif len(parts) >= 2 and parts[1].lower() == "stop":
                if node.auto_alerts_enabled:
                    node.auto_alerts_enabled = False
                    print("[AUTO] Random disaster simulation stopping...")
                else:
                    print("[AUTO] Simulation is not running.")
            else:
                print("Usage: auto start | auto stop")
        
        elif cmd.lower().startswith("msg "):
            args = cmd[4:].strip()
            if not args:
                print("Usage: msg <text>  OR  msg <city1,city2> <text>")
                continue

            known_city_names = {city["name"] for city in CITIES.values()}

            # If there is a comma, treat the stuff before the first space AFTER the last comma
            # as the city list. Example: "NEW YORK,CHICAGO Power outage reported"
            if "," in args:
                last_comma = args.rfind(",")
                first_space_after_last_comma = args.find(" ", last_comma)

                if first_space_after_last_comma == -1:
                    # No message text, everything is treated as the city list
                    city_part = args
                    message_text = ""
                else:
                    city_part = args[:first_space_after_last_comma]
                    message_text = args[first_space_after_last_comma + 1 :].strip()

                raw_cities = [c.strip().upper() for c in city_part.split(",") if c.strip()]
                target_areas = [c for c in raw_cities if c in known_city_names]

                if not target_areas:
                    print("[ERROR] None of the specified cities matched known cities. Sending to your area only.")
                    target_areas = [area]
            else:
                # No comma => just a message to your own area
                message_text = args
                target_areas = [area]

            node.broadcast_custom_alert(message_text, target_areas)
            print(f"[SENT] Custom alert to {', '.join(target_areas) if target_areas else 'ALL AREAS'}")

        
        elif cmd.lower() == "mutex":
            node.demo_mutual_exclusion()
        
        elif cmd.lower().startswith("2pc"):
            parts = cmd.split(maxsplit=1)
            if len(parts) < 2:
                print("Usage: 2pc <transaction_data>")
                continue
            tx_data = parts[1]
            node.demo_two_phase_commit(tx_data)
        
        else:
            print("Unknown command. Type 'disaster', 'national', 'auto', 'msg', 'mutex', '2pc', or 'exit'.")


if __name__ == "__main__":
    main()
