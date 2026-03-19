from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory data store for simplicity
orders = {}
users = {} # New: stores {'username': 'password'} for now

@app.route('/register', methods=['POST'])
def register():
    """
    Registers a new user.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    if username in users:
        return jsonify({'error': 'Username already exists'}), 409

    users[username] = password
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    """
    Authenticates a user.
    """
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400

    stored_password = users.get(username)
    if stored_password and stored_password == password:
        # In a real application, you would generate a JWT or session token
        return jsonify({'message': 'Login successful', 'token': username}), 200 # Using username as a simple token for now
restaurants_db = {
    "restaurantA": {
        "name": "Pizza Palace",
        "cuisine": "Italian",
        "menu": [
            {"id": "pizza-pepperoni", "name": "Pepperoni Pizza", "price": 15.00},
            {"id": "pizza-margherita", "name": "Margherita Pizza", "price": 12.00}
        ]
    },
    "restaurantB": {
        "name": "Burger Joint",
        "cuisine": "American",
        "menu": [
            {"id": "burger-classic", "name": "Classic Burger", "price": 10.00},
            {"id": "fries-large", "name": "Large Fries", "price": 3.00}
        ]
    }
}

@app.route('/restaurants', methods=['GET'])
def get_restaurants():
    """
    Returns a list of available restaurants and their menus.
    """
    # In a real application, this would fetch from Firestore or another database
    return jsonify(restaurants_db)

@app.route('/order', methods=['POST'])
def place_order():
    """
    Places a new order.
    This endpoint would typically publish a message to a Pub/Sub topic.
    """
    order_data = request.get_json()
    # In a real application, you would generate a unique order ID
    order_id = str(len(orders) + 1)
    orders[order_id] = {'status': 'pending', 'details': order_data}
    
    # Simulate publishing to Pub/Sub
    print(f"Publishing 'orders.place' event for order_id: {order_id}")
    
    return jsonify({'order_id': order_id, 'status': 'pending'}), 201

@app.route('/order/<order_id>', methods=['GET'])
def get_order_status(order_id):
    """
    Retrieves the status of an order.
    """
    order = orders.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({'order_id': order_id, 'status': order['status']})

if __name__ == '__main__':
    app.run(port=8080, debug=True)
