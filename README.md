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
