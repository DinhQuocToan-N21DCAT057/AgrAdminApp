from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Initialize Flask app
app = Flask(__name__)

# Force UTF-8 encoding for console output
#sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Initialize Firebase Admin SDK with your service account credentials
cred = credentials.Certificate('appmuahangnongsan-firebase-adminsdk-fbsvc-42a308608f.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://appmuahangnongsan-default-rtdb.asia-southeast1.firebasedatabase.app'
})

@app.route('/users', methods=['GET'])
def get_all_users():
    """Get all users from Firebase"""
    try:
        # Get reference to the Users node
        users_ref = db.reference('Data/Users')  # Changed to correct path
        # Get all users
        users = users_ref.get()
        if not users:
            return jsonify({'error': 'No users found'}), 404
        return jsonify(users)
    except Exception as e:
        print(f"Error getting users: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Get a specific user by their ID"""
    try:
        user_ref = db.reference(f'Data/Users/{user_id}')  # Changed to correct path
        user = user_ref.get()
        if user is None:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(user)
    except Exception as e:
        print(f"Error getting user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/users/<user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    """Get orders for a specific user"""
    try:
        # Get user's order IDs from Data/Users
        user_orders_ref = db.reference(f'Data/Users/{user_id}/orderBills')  # Changed to correct path
        user_order_ids = user_orders_ref.get()
        
        if not user_order_ids:
            return jsonify({'error': 'No orders found for this user'}), 404
            
        # Get full order details from Data/OrderBills
        orders_ref = db.reference('Data/OrderBills')
        all_orders = orders_ref.get() or {}
        
        # Filter orders for this user
        user_orders = {
            order_id: order_data 
            for order_id, order_data in all_orders.items() 
            if order_id in user_order_ids
        }
        
        return jsonify(user_orders)
    except Exception as e:
        print(f"Error getting orders for user {user_id}: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)