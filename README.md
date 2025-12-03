# CECS-327-Milestone-project
A team of 6 are creating a Notification system for disasters 

CECS 327
Group 4
Aryan Patel
Deep Patel
Ethan Sergeant Araracap
Jorge Estrada
Mario Robles
Salvador Sanchez

# Milestone 2

# Part 1: Direct Communication – Interprocess Communication (IPC)

**Summary**
---
This project demonstrates direct interprocess communication (IPC) between two components of a Disaster Alert System (DAS) using TCP sockets and JSON messages in Python.

A **client** simulates a disaster sensor that sends alert data to a server, which acts as a central aggregator. 

The **server** receives and displays the alert details, then sends a confirmation message back to the client.

**Alert**
---
The project shows how two processes communicate directly over a network using Python’s built-in socket library.
The client sends a structured JSON alert containing disaster information, and the server decodes the message, prints the data in a readable format, and acknowledges receipt.

# Clone or download the project folder
```bash
cd 327_Project
python -m venv .venv
source .venv/bin/activate 
```

##  Running the Server


```bash
python server.py
```
<img width="561" height="171" alt="Screenshot 2025-10-21 at 7 30 29 PM" src="https://github.com/user-attachments/assets/6f685080-fa2b-4722-97a0-4636bb6c37a7"/>

---

##  Running the Client


Open another terminal window and run:
```bash
python client.py
```

<img width="554" height="36" alt="Screenshot 2025-10-21 at 7 36 30 PM" src="https://github.com/user-attachments/assets/2a7f71b8-a82d-465a-8d2d-1f64ab42dc45" />

---

**Technologies Used:**
---
- Python 3
- socket
- json
- uuid

---

# Part 2: Remote Communication – REST API

**Summary**  
---  
This part of the Disaster Alert System demonstrates **remote communication** between the admin and clients using a **REST API built with FastAPI**.  
The admin can send alert messages through an HTTP POST request, and clients can check the latest system status through an HTTP GET request.

**Endpoints**  
---  
- **POST `/send_alert`** – Admin sends a new alert message and severity level.  
- **GET `/get_status`** – Clients retrieve the latest alert and overall status.  

Each alert is stored temporarily in memory with a timestamp to simulate real-time updates.

**Running the API**  
---  
1. Install dependencies:  
   ```bash
   pip install fastapi uvicorn
2. uvicorn rest_api:app --reload

3. Open your browser and go to http://127.0.0.1:8000/docs
to test the API interactively.

**POST /send_alert body:**

```
{
  "message": "Flood warning in Cerritos",
  "severity": "High"
}
```

**Response**

```
{
  "status": "Alert sent successfully",
  "alert": {
    "message": "Flood warning in Cerritos",
    "severity": "High",
    "timestamp": "2025-10-13 22:34:14"
  }
}
```

**GET /get_status response:**

```
{
  "status": "Active",
  "latest_alert": {
    "message": "Flood warning in Cerritos",
    "severity": "High",
    "timestamp": "2025-10-13 22:34:14"
  },
  "total_alerts": 1
}
```

**Technologies Used:**
Python 3

FastAPI

Uvicorn

Pydantic





# Part 3: Indirect Communication (Pub-Sub)

## Summary
This project demonstrates a **publish–subscribe (pub/sub)** alert system using **RabbitMQ** and Python’s **`pika`** library.  
A **publisher** sends JSON alerts (earthquake, fire, flood, weather) to a **topic exchange** named `alerts`.  
One or more **subscribers** create their own queues and bind with patterns (e.g., `alerts.fire`, `alerts.*`, `alerts.#`) to receive relevant messages.

## Alert 
This project demonstrates RabbitMQ topic-based messaging using a Python publisher and subscriber. The publisher sends structured alert messages (fire, flood, weather, etc.) while the subscriber listens on a bound queue and prints received alerts.

## Prerequisites (Windows)

- Python 3.9+
- RabbitMQ server running on localhost
- `pika` Python package

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install pika

# Ensure RabbitMQ service is running:
```
net start RabbitMQ


(Optional) Enable the RabbitMQ management UI:

rabbitmq-plugins enable rabbitmq_management


Access UI at:

```
http://localhost:15672
User: guest
Pass: guest
```
## Running the Subscriber

Default mode (receives all alerts):
```
.\.venv\Scripts\python.exe .\subscriber_rabbit.py
```
## General syntax:
```
subscriber_rabbit.py <queue_name> <binding_key>
```

Example binding keys:

Binding Key	Meaning
alerts.#	receive all alerts
alerts.fire	receive only fire alerts
alerts.flood	receive only flood alerts

## Running the Publisher
```
.\.venv\Scripts\python.exe .\publisher_rabbit.py
```

The publisher sends multiple sample alerts using a topic exchange named alerts.

##Testing via RabbitMQ UI (Manual Publish)

You can manually publish a message through the UI without using the Python publisher.

1. Open http://localhost:15672

2. Navigate to Exchanges

3. Click on the alerts exchange

4. Scroll to Publish message

5. Use routing key, for example:
```
alerts.powerout
```
## Use JSON payload:
```
{"type":"powerout","message":"UI test: outage in Zone 3","severity":"medium","timestamp":"now"}
```


## Screenshots
<img width="1500" height="1360" alt="image" src="https://github.com/user-attachments/assets/32700996-f77b-4f01-81ab-2982453627ff" />
When the subscriber receives a published alert, it prints the routing key, alert type, severity, message, and timestamp. The output confirms that the queue is bound correctly to the topic exchange and that messages are being routed successfully.


<img width="750" height="450" alt="image" src="https://github.com/user-attachments/assets/15f8f674-7552-48be-a601-f8853016bb7d" />

The screenshot below shows the subscriber receiving a message that was manually published through the RabbitMQ Management UI using the routing key `alerts.powerout`. This confirms that the subscriber is correctly bound to the topic exchange and can consume messages from both the Python publisher and UI-based manual input.

<img width="1610" height="350" alt="image" src="https://github.com/user-attachments/assets/117b9a25-d2ef-41b6-8c2b-fe83b583dca9" />

The publisher prints a confirmation for each alert it sends to the `alerts` exchange, showing the routing key used and a preview of the message. When all alerts are sent, it prints "All alerts published!". This confirms the messages were successfully pushed into RabbitMQ and are ready to be consumed by any subscribers bound to the exchange.



## Opitional 
<img width="2022" height="985" alt="image" src="https://github.com/user-attachments/assets/f3939d66-abee-469a-9dfb-d8fff83d3586" />

You can also publish alerts manually from the RabbitMQ Management UI by selecting the `alerts` exchange and using the "Publish message" panel. Enter a routing key such as `alerts.powerout` and a JSON payload. Any subscriber that is bound to a matching binding key (e.g., `alerts.#`) will immediately receive the message even without running the Python publisher.

# Milestone 3

We extended the Disaster Alert System with OS level concurrency and peer to peer communication. OS level concurrency allows us to enable simultaneous alert handling by using multithreading. Peer to peer communication allows distributed alert exchange between multiple peer nodes and removes the need for a central server.

## Added/edited files

### synch_demo.py
Demonstration script for synchronization and race condition handling
### concurrent_alert_server.py
Enhanced alert server using threads and locks for concurrent client handling
### peer_node.py
Implements a peer-to-peer communication model

## How to Run

## synch_demo.py — Concurrency & Synchronization Demo 
1. Open your terminal and navigate to the project folder:
   ```bash
   cd CECS-327-Milestone-project
Run the script:

bash
Copy code
python3 synch_demo.py

### Output
<img width="1205" height="262" alt="output demo1" src="https://github.com/user-attachments/assets/54b6f70f-f69c-4ead-8370-1531b21292d6" />
<img width="1696" height="158" alt="output demo2" src="https://github.com/user-attachments/assets/20da6e9f-3135-401a-bc2c-b075b79bff6d" />
<img width="1700" height="146" alt="output demo3" src="https://github.com/user-attachments/assets/0c668df4-0e4a-45c3-8137-a8dde3cbd468" />



## concurrent_alert_server.py — Concurrency Demo
1. Open your terminal and navigate to the project folder:
   ```bash
   cd CECS-327-Milestone-project
Run the script:

```bash
python3 concurrent_alert_server.py
```
### Output: 
<img width="1235" height="398" alt="Screenshot 2025-11-04 at 1 46 51 PM" src="https://github.com/user-attachments/assets/c3e591b5-a709-4b9e-b952-5167ff7bcb15" />

# Milestone 4

## logical_clock.py

This file simulates event ordering between disaster alert nodes using Lamport timestamps.
To run it, open a terminal in the project folder and type:

python3 logical_clock.py

It shows how alerts like earthquake, fire, and evacuation are timestamped and ordered consistently across all nodes.

Output:
<img width="1507" height="575" alt="image" src="https://github.com/user-attachments/assets/e5e79b87-3de0-4747-8595-6522e924c4ee" />

Ricart-Agrawala

The Ricart–Agrawala algorithm enforces mutual exclusion within a system that is composed of a large number of unaffiliated peers, any of which can perform operations that affect the external world. These operations are often time-critical, as is the case when they involve adjusting the behavior of a traffic signal. In such a system, it is essential that only one peer perform a concerted operation at any given time; otherwise, the external world might be negatively affected by the operation of two or more peers that are trying to do the same thing at once (and failing, in the case of a time-critical operation, for 

reasons of overlap and concurrency). To enforce this mutual exclusion, Ricart and Agrawala devised a simple and elegantly effective algorithm.

<img width="688" height="510" alt="image" src="https://github.com/user-attachments/assets/a87740dd-dc35-449a-a13c-43e5fceae7ff" />

The Ricart–Agrawala protocol guarantees that only one node enters the critical section at any given moment, and it does so without a central coordinator. Instead, each node maintains a logically consistent timestamp based on Lamport logical clocks. When a node wishes to enter the critical section, it increments its timestamp, sends a REQUEST message to every other node in the system, and waits. Each receiving node, upon getting the REQUEST message, compares its own timestamp with that of the requester. If the receiving node is not already in the critical section, or if it has a logically later timestamp (meaning the REQUESTer has higher priority and should go first), it sends back a REPLY with no further ado. If the receiving node is in the critical section (which it shouldn't be, because this is a correct protocol), it sends back a REPLY as soon 

<img width="255" height="387" alt="image" src="https://github.com/user-attachments/assets/5f7117ac-b919-4a01-b32d-c884bad10a4f" />
<img width="422" height="310" alt="image" src="https://github.com/user-attachments/assets/50fb361b-cd20-456c-8e13-88ce42f4a55a" />
**Coordination_protocol.py**
Distributed nodes in our system do not update at the same time, which would cause inconsistent data. To do this, I implemented a distributed mutual exclusion protocol using Ricart Agrawala along with Lamport timestamps.

This allows all our nodes to reach agreement on who gets to perform an update first even if messages arrive late or out of order.


**TEST CASES:**
<img width="429" height="406" alt="image" src="https://github.com/user-attachments/assets/55125bc6-8b27-4f82-af79-93c5ec714a88" />

<img width="299" height="277" alt="image" src="https://github.com/user-attachments/assets/c3410f2e-47d2-466b-9a42-281f2505e907" />

<img width="394" height="309" alt="image" src="https://github.com/user-attachments/assets/bc217710-8aca-42c8-bb7f-e56aa95a83ff" />
<img width="245" height="334" alt="image" src="https://github.com/user-attachments/assets/7b52f1f2-da4c-471e-a8e9-8f3f40a042cf" />






