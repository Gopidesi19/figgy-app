from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def delivery_orchestrator():
    """
    HTTP-triggered function that assigns a delivery agent and creates a Cloud Task.
    """
    data = request.get_json()
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({'error': 'order_id is required'}), 400

    print(f"Delivery orchestrator processing order_id: {order_id}")

    # In a real application, you would:
    # 1. Assign a delivery agent.
    print(f"Assigning delivery agent for order_id: {order_id}")

    # 2. Update the order status to 'out_for_delivery' in Firestore.
    print(f"Updating order {order_id} in Firestore with status: out_for_delivery")

    # 3. Create a Cloud Task to simulate delivery duration.
    print(f"Enqueuing Cloud Task for delivery completion of order_id: {order_id}")

    return jsonify({'status': 'out_for_delivery'}), 200

if __name__ == '__main__':
    # This block allows you to run the function locally for testing.
    # You would send a POST request to http://localhost:8081/
    # with a JSON body like {'order_id': '1'}
    app.run(port=8081, debug=True)
