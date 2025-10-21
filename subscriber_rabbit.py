# subscriber.py
import pika
import json
import sys

# Configuration
EXCHANGE_NAME = "alerts"
RABBITMQ_HOST = "localhost"
QUEUE_NAME = "client_a"  # Change this for different subscribers
BINDING_KEY = "alerts.#"  # Subscribe to all alerts (# = wildcard)


def handle_message(channel, method, properties, body):
    """This function runs when we receive a message"""
    
    # Convert JSON string back to dictionary
    alert = json.loads(body)
    
    # Print the alert nicely
    print("=" * 60)
    print(f"Route:    {method.routing_key}")
    print(f"Type:     {alert['type']}")
    print(f"Severity: {alert['severity']}")
    print(f"Message:  {alert['message']}")
    print(f"Time:     {alert['timestamp']}")
    print("=" * 60)
    print()
    
    # Tell RabbitMQ we processed the message
    channel.basic_ack(delivery_tag=method.delivery_tag)


def start_subscriber():
    # Allow changing queue name and binding from command line
    # Example: python subscriber.py client_b alerts.fire
    queue_name = QUEUE_NAME
    binding_key = BINDING_KEY
    
    if len(sys.argv) > 1:
        queue_name = sys.argv[1]
    if len(sys.argv) > 2:
        binding_key = sys.argv[2]
    
    # Step 1: Connect to RabbitMQ
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(RABBITMQ_HOST)
    )
    channel = connection.channel()
    
    # Step 2: Declare exchange (must match publisher)
    channel.exchange_declare(
        exchange=EXCHANGE_NAME,
        exchange_type="topic",
        durable=True
    )
    
    # Step 3: Create our own queue
    channel.queue_declare(
        queue=queue_name,
        durable=True
    )
    
    # Step 4: Connect queue to exchange with binding key
    channel.queue_bind(
        queue=queue_name,
        exchange=EXCHANGE_NAME,
        routing_key=binding_key
    )
    
    # Step 5: Process one message at a time
    channel.basic_qos(prefetch_count=1)
    
    # Step 6: Start listening for messages
    print(f"Listening on queue: {queue_name}")
    print(f"Binding key: {binding_key}")
    print("Waiting for messages... Press Ctrl+C to exit\n")
    
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=handle_message,
        auto_ack=False
    )
    
    channel.start_consuming()


if __name__ == "__main__":
    try:
        start_subscriber()
    except KeyboardInterrupt:
        print("\n\nSubscriber stopped")
        sys.exit(0)