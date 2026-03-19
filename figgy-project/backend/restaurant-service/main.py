import base64
import json
import random

def restaurant_service(event, context):
    """
    Triggered by a message on a Pub/Sub topic.
    This function decides whether to accept or reject an order.
    """
    print(f"Received event: {event}")

    pubsub_message = base64.b64decode(event['data']).decode('utf-8')
    order_data = json.loads(pubsub_message)
    
    order_id = order_data.get('order_id')

    print(f"Restaurant service processing order_id: {order_id}")
    
    # In a real application, you would:
    # 1. Assign a restaurant.
    # 2. Decide to accept or reject the order.
    decision = random.choice(['accepted', 'rejected'])
    print(f"Order {order_id} was {decision}")

    # 3. Update the order status in Firestore.
    print(f"Updating order {order_id} in Firestore with status: {decision}")

    # 4. Publish an 'orders.accepted' or 'orders.rejected' event.
    if decision == 'accepted':
        print(f"Publishing 'orders.accepted' event for order_id: {order_id}")
    else:
        print(f"Publishing 'orders.rejected' event for order_id: {order_id}")

    return 'OK', 200

# Example of how to simulate a call to this function
if __name__ == '__main__':
    sample_data = {'order_id': '1'}
    sample_message = {
        "message": {
            "data": base64.b64encode(json.dumps(sample_data).encode('utf-8')).decode('utf-8'),
            "messageId": "2345678901",
            "publishTime": "2026-03-19T12:05:00Z"
        },
        "subscription": "projects/your-project-id/subscriptions/your-subscription-id"
    }
    
    restaurant_service(sample_message['message'], None)
