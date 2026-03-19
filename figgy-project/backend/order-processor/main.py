import base64
import json

def process_order(event, context):
    """
    Triggered by a message on a Pub/Sub topic.
    This function processes the order and publishes an 'orders.created' event.
    """
    print(f"Received event: {event}")

    # The actual data is in the 'data' field, and it's base64-encoded.
    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    order_data = json.loads(pubsub_message)
    
    order_id = order_data.get('order_id')

    print(f"Processing order_id: {order_id}")
    
    # In a real application, you would:
    # 1. Validate the user and order data.
    # 2. Create the initial 'pending' order in Firestore.
    print(f"Order {order_id} created in Firestore with status: pending")

    # 3. Publish an 'orders.created' event.
    print(f"Publishing 'orders.created' event for order_id: {order_id}")

    return 'OK', 200

# Example of how to simulate a call to this function
if __name__ == '__main__':
    # This is a sample event payload.
    # In a real Cloud Run service triggered by Pub/Sub,
    # the request body would be a JSON object with a 'message' key.
    sample_data = {'order_id': '1', 'details': {'item': 'Pizza', 'quantity': 1}}
    sample_message = {
        "message": {
            "data": base64.b64encode(json.dumps(sample_data).encode('utf-8')).decode('utf-8'),
            "messageId": "1234567890",
            "publishTime": "2026-03-19T12:00:00Z"
        },
        "subscription": "projects/your-project-id/subscriptions/your-subscription-id"
    }
    
    # For a Pub/Sub-triggered service, the event is the body of the POST request.
    # The context object is not used in this simulation.
    process_order(sample_message['message'], None)
