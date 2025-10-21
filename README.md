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




