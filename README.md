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

net start RabbitMQ


(Optional) Enable the RabbitMQ management UI:

rabbitmq-plugins enable rabbitmq_management


Access UI at:

http://localhost:15672
User: guest
Pass: guest
