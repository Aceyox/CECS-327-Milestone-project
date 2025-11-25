class LamportClock:
    def __init__(self, node_id):
        self.node_id = node_id
        self.time = 0

    def increment(self):
        # increase local clock for internal events
        self.time += 1

    def update(self, received_time):
        # update local clock when receiving message
        self.time = max(self.time, received_time) + 1

    def send_event(self, msg):
        # simulate sending a message with timestamp
        self.increment()
        print(f"[SEND] {self.node_id} -> time: {self.time} | msg: {msg}")
        return (self.node_id, self.time, msg)

    def receive_event(self, event):
        # simulate receiving message and updating local time
        sender, ts, msg = event
        self.update(ts)
        print(f"[RECV] {self.node_id} got '{msg}' from {sender} | new time: {self.time}")


# Simulation Example
if __name__ == "__main__":
    A = LamportClock("A")  # earthquake sensor
    B = LamportClock("B")  # fire alert system
    C = LamportClock("C")  # central emergency hub

    # internal event at A
    A.increment()
    print(f"[INTERNAL] {A.node_id} detected earthquake | time: {A.time}")

    # A sends earthquake alert to B and C
    e1 = A.send_event("Earthquake detected in Zone 3")

    # B receives it
    B.receive_event(e1)

    # internal event at B
    B.increment()
    print(f"[INTERNAL] {B.node_id} running fire check | time: {B.time}")

    # B sends update to C
    e2 = B.send_event("No fire detected, monitoring continues")

    # C receives alerts
    C.receive_event(e1)
    C.receive_event(e2)

    # internal event at C
    C.increment()
    e3 = C.send_event("Evacuation alert issued")
    A.receive_event(e3)
    B.receive_event(e3)

    print("\nFinal clock values:")
    print(f"A: {A.time}, B: {B.time}, C: {C.time}")
