# publisher.py
import pika
import json
import time
from datetime import datetime

# Configuration
EXCHANGE_NAME = "alerts"
RABBITMQ_HOST = "localhost"

# Sample alert messages
alerts = [
    {
        "type": "earthquake",
        "message": "Magnitude 5.2 earthquake detected 15km north of city center",
        "severity": "high"
    },
    {
        "type": "flood",
        "message": "Flash flood warning issued for riverside areas",
        "severity": "critical"
    },
    {
        "type": "fire",
        "message": "Wildfire spotted near residential zone, evacuation recommended",
        "severity": "high"
    },
    {
        "type": "weather",
        "message": "Severe thunderstorm approaching, seek shelter",
        "severity": "medium"
    },
]


def publish_alerts():
    # Step 1: Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(RABBITMQ_HOST)
    )
    channel = connection.channel()
    
    # Step 2: Create exchange (like a mailbox sorter)
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="topic",
        durable=True
    )
    
    # Step 3: Send each alert
    for alert in alerts:
        # Add timestamp to alert
        alert["timestamp"] = datetime.now().isoformat()
        
        # Convert alert to JSON string
        message = json.dumps(alert)
        
        # Create routing key (like an address label)
        routing_key = f"alerts.{alert['type']}"
        
        # Publish the message
        channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(
                delivery_mode=2  # Make message persistent
            )
        )
        
        print(f"Sent: {routing_key} -> {alert['message'][:50]}...")
        time.sleep(1)  # Wait 1 second between messages
    
    # Step 4: Close connection
    connection.close()
    print("\nAll alerts published!")


if __name__ == "__main__":
    publish_alerts()