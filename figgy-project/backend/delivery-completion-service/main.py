from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/', methods=['POST'])
def delivery_completion_service():
    """
    HTTP-triggered function that marks an order as delivered.
    Triggered by a Cloud Task after a delay.
    """
    data = request.get_json()
    order_id = data.get('order_id')

    if not order_id:
        return jsonify({'error': 'order_id is required'}), 400

    print(f"Delivery completion service processing order_id: {order_id}")

    # In a real application, you would:
    # 1. Update the order status to 'delivered' in Firestore.
    print(f"Updating order {order_id} in Firestore with status: delivered")

    return jsonify({'status': 'delivered'}), 200

if __name__ == '__main__':
    # This block allows you to run the function locally for testing.
    # You would send a POST request to http://localhost:8082/
    # with a JSON body like {'order_id': '1'}
    app.run(port=8082, debug=True)
