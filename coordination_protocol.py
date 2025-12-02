import threading
import time
import random



class Node:
    def __init__(self, node_id, total_nodes):
        self.node_id = node_id
        self.total_nodes = total_nodes


        self.timestamp = 0


        self.requesting = False
        self.replies_needed = 0
        self.deferred_replies = []

        # Lock for thread safety
        self.lock = threading.Lock()


        self.network = None



    def increment_time(self):
        self.timestamp += 1

    def update_time(self, other_ts):
        self.timestamp = max(self.timestamp, other_ts) + 1



    def request_cs(self):
        with self.lock:
            self.increment_time()
            self.requesting = True
            self.replies_needed = self.total_nodes - 1

            print(f"[Node {self.node_id}] REQUEST → t={self.timestamp}")

        # broadcast request
        for node in self.network:
            if node.node_id != self.node_id:
                node.receive_request(self.timestamp, self.node_id)



    def receive_request(self, ts, requester_id):
        time.sleep(random.uniform(0.05, 0.15))

        with self.lock:
            self.update_time(ts)


            should_reply = False

            if not self.requesting:
                should_reply = True
            else:
                my_tuple = (self.timestamp, self.node_id)
                requester_tuple = (ts, requester_id)


                if requester_tuple < my_tuple:
                    should_reply = True

            if should_reply:

                for node in self.network:
                    if node.node_id == requester_id:
                        node.receive_reply()
                # Debug
                print(f"[Node {self.node_id}] REPLY → Node {requester_id}")
            else:

                self.deferred_replies.append(requester_id)
                print(f"[Node {self.node_id}] DEFERRED REPLY → Node {requester_id}")



    def receive_reply(self):
        with self.lock:
            self.replies_needed -= 1



    def enter_cs(self):
        while True:
            with self.lock:
                if self.requesting and self.replies_needed == 0:
                    break
            time.sleep(0.01)

        print(f"\n🔥🔥 [Node {self.node_id}] ENTER CS @ t={self.timestamp}\n")
        time.sleep(random.uniform(0.2, 0.4))  # simulate work
        print(f"🟢 [Node {self.node_id}] EXIT CS\n")

        self.release_cs()



    def release_cs(self):
        with self.lock:
            self.requesting = False


            for rid in self.deferred_replies:
                for node in self.network:
                    if node.node_id == rid:
                        node.receive_reply()
                print(f"[Node {self.node_id}] RELEASE → Replying to Node {rid}")

            self.deferred_replies = []



def simulate():
    print("\n===== Distributed Coordination Protocol (Ricart–Agrawala) =====\n")

    NUM_NODES = 3

    nodes = [Node(i, NUM_NODES) for i in range(NUM_NODES)]


    for n in nodes:
        n.network = nodes


    threads = []
    for node in nodes:
        t = threading.Thread(
            target=lambda n=node: simulate_node_activity(n),
            daemon=True
        )
        threads.append(t)
        t.start()


    time.sleep(5)

    print("\n===== Simulation Finished =====\n")


def simulate_node_activity(node):

    for _ in range(2):
        time.sleep(random.uniform(0.3, 0.7))
        node.request_cs()
        node.enter_cs()




if __name__ == "__main__":
    simulate()
