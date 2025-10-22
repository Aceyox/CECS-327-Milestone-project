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



