from flask import Flask, jsonify, render_template, url_for
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# Initialize Firebase Admin SDK with your service account credentials
cred = credentials.Certificate('appmuahangnongsan-firebase-adminsdk-fbsvc-42a308608f.json')
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://appmuahangnongsan-default-rtdb.asia-southeast1.firebasedatabase.app'
})

#################################################################################################################################
#                                         UTILITIES                                                                             #
#################################################################################################################################


@app.template_global()
def now():
    return datetime.now().strftime('%Y-%m-%d')

def get_image_path(drawable_path):
    """Convert Android drawable path to web-compatible image path"""
    if not drawable_path:
        return url_for('static', filename='images/placeholder.png')
    
    # Remove 'drawable/' prefix if present
    image_name = drawable_path.replace('drawable/', '')
    
    # Check if the image exists in static/images
    image_path = os.path.join('static', 'images', f"{image_name}.png")
    if os.path.exists(image_path):
        return url_for('static', filename=f'images/{image_name}.png')
    
    # If image doesn't exist, return a placeholder
    return url_for('static', filename='images/placeholder.png')


@app.template_filter('datetime')
def format_datetime(value):
    """Format a timestamp to datetime."""
    if not value:
        return ''
    # Convert milliseconds to seconds if necessary
    if len(str(value)) > 10:
        value = value / 1000
    return datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')



#################################################################################################################################
#                                         DASHBOARD REQUEST MAPPING                                                             #
#################################################################################################################################


@app.route('/')
def dashboard():
    """Render the main dashboard"""
    return render_template('index.html')


#################################################################################################################################
#                                         CATEGORY REQUEST MAPPING                                                              #
#################################################################################################################################


@app.route('/categories', methods=['GET'])
def get_categories():
    """Get all categories from Firebase"""
    try:
        categories_ref = db.reference('Data/Categories')
        categories = categories_ref.get()
        if not categories:
            return render_template('Categories/categories.html', error='No categories found')
        
        for category in categories.values():
            category['Image'] = get_image_path(category['Image'])
            
        return render_template('Categories/categories.html', categories=categories)
    except Exception as e:
        print(f"Error getting categories: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/categories.html', error=str(e))


    
@app.route('/categories/<category_id>', methods=['GET'])
def get_categories_items(category_id):
    """Get all items in a specific category"""
    try:
        # Get category details
        category_ref = db.reference(f'Data/Categories/{category_id}')
        category = category_ref.get()
        
        if not category:
            return render_template('Categories/categories_items.html', error='Category not found')
            
        # Get items for this category
        items_ref = db.reference('Data/CategoriesItems')
        all_items = items_ref.get()
        
        if not all_items or category_id not in all_items:
            return render_template('Categories/categories_items.html', 
                                 category=category,
                                 error='No items found in this category')
        
        category_items = all_items[category_id]
        
        # Process images for items
        for item in category_items.values():
            if 'Image' in item:
                item['Image'] = get_image_path(item['Image'])
        
        return render_template('Categories/categories_items.html', 
                             category=category,
                             items=category_items)
    except Exception as e:
        print(f"Error getting items for category {category_id}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Categories/categories_items.html', error=str(e))
    

#################################################################################################################################
#                                         ITEMS REQUEST MAPPING                                                                 #
#################################################################################################################################


@app.route('/all-items', methods=['GET'])
def get_all_items():
    """Get all items from Firebase"""
    try:
        categories_items_ref = db.reference('Data/CategoriesItems')
        categories_items = categories_items_ref.get()
        
        if not categories_items:
            return render_template('Items/all_items.html', error='No items found')
            
        # Process images for nested items
        for category_items in categories_items.values():
            for item in category_items.values():
                if 'Image' in item:
                    item['Image'] = get_image_path(item['Image'])
        
        return render_template('Items/all_items.html', items=categories_items)
    except Exception as e:
        print(f"Error getting all items: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Items/all_items.html', error=str(e))
    

#################################################################################################################################
#                                         COUPONS REQUEST MAPPING                                                               #
#################################################################################################################################


@app.route('/coupons', methods=['GET'])
def get_coupons():
    """Get all coupons from Firebase"""
    try:
        coupons_ref = db.reference('Data/Coupons')
        coupons = coupons_ref.get()

        if not coupons:
            return render_template('Coupons/coupons.html', error='No coupons found')
            
        # Process coupons to add status
        current_date = datetime.now().strftime('%Y-%m-%d')
        for coupon in coupons.values():
            if coupon['startDate'] > current_date:
                coupon['status'] = 'upcoming'
            elif coupon['endDate'] < current_date:
                coupon['status'] = 'expired'
            else:
                coupon['status'] = 'active'
            
        return render_template('Coupons/coupons.html', coupons=coupons)
    except Exception as e:
        print(f"Error getting coupons: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Coupons/coupons.html', error=str(e))


#################################################################################################################################
#                                         LIKED ITEMS REQUEST MAPPING                                                           #
#################################################################################################################################


@app.route('/liked-items', methods=['GET'])
def get_liked_items():
    """Get all liked items from Firebase"""
    try:
        liked_items_ref = db.reference('Data/LikedItems')
        liked_items = liked_items_ref.get()

        if not liked_items:
            return render_template('LikedItems/liked_items.html', error='No liked items found')

        # Process nested structure: users -> items
        for user_items in liked_items.values():
            if isinstance(user_items, dict):  # Ensure it's a dictionary
                for item in user_items.values():
                    if isinstance(item, dict) and 'image' in item:  # Check if item has image
                        item['Image'] = get_image_path(item['image'])
                    elif isinstance(item, dict) and 'Image' in item:  # Check for capitalized Image
                        item['Image'] = get_image_path(item['Image'])

        return render_template('LikedItems/liked_items.html', liked_items=liked_items)
    except Exception as e:
        print(f"Error getting liked items: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('LikedItems/liked_items.html', error=str(e))


#################################################################################################################################
#                                         ORDER BILLS REQUEST MAPPING                                                           #
#################################################################################################################################


@app.route('/orders', methods=['GET'])
def get_all_orders():
    """Get all orders from Firebase"""
    try:
        orders_ref = db.reference('Data/OrderBills')
        orders = orders_ref.get()

        if not orders:
            return render_template('OrderBills/orders.html', error='No orders found')
        
        # Process orders
        for order in orders.values():
            # Convert timestamp to date string
            if 'orderDate' in order:
                timestamp = order['orderDate']
                # Convert milliseconds to seconds if necessary
                if len(str(timestamp)) > 10:
                    timestamp = timestamp / 1000
                order['orderDate'] = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
            
            # Ensure items is a dictionary
            if 'items' in order:
                if isinstance(order['items'], firebase_admin.db.Reference):
                    order['items'] = order['items'].get() or {}
                elif not isinstance(order['items'], dict):
                    order['items'] = {}
                    
            # Ensure totalPrice exists and is a number
            if 'totalPrice' not in order or not isinstance(order['totalPrice'], (int, float)):
                # Calculate total price from items if available
                if 'items' in order and order['items']:
                    total = sum(
                        float(item.get('salePrice', 0)) * int(item.get('quantity', 0))
                        for item in order['items'].values()
                    )
                    order['totalPrice'] = total
                else:
                    order['totalPrice'] = 0.0

        return render_template('OrderBills/orders.html', orders=orders)
    except Exception as e:
        print(f"Error getting orders: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('OrderBills/orders.html', error=str(e))


@app.route('/orders/<order_id>/details', methods=['GET'])
def get_order_details(order_id):
    """Get detailed information for a specific order"""
    try:
        order_ref = db.reference(f'Data/OrderBills/{order_id}')
        order = order_ref.get()
        
        if not order:
            return render_template('OrderBills/order_details.html', error='Order not found')
        
        # Convert order to a mutable dictionary if it's not already
        if not isinstance(order, dict):
            order = dict(order)
        
        # Ensure items is a regular dictionary
        if not isinstance(order.get('items'), dict):
            # If items is a reference, get its value
            if isinstance(order.get('items'), firebase_admin.db.Reference):
                order['items'] = order['items'].get('/')
            else:
                # If items doesn't exist or is not a dict, initialize it
                order['items'] = {}
        
        # Convert drawable paths to web-compatible image paths
        for item in order['items'].values():
            if isinstance(item, dict) and 'image' in item:
                item['image'] = get_image_path(item['image'])
            
        return render_template('OrderBills/order_details.html', order=order)
    except Exception as e:
        print(f"Error getting order details for order {order_id}: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('OrderBills/order_details.html', error=str(e))


#################################################################################################################################
#                                         REVIEWS REQUEST MAPPING                                                               #
#################################################################################################################################


@app.route('/reviews', methods=['GET'])
def get_all_reviews_items():
    """Get all reviews items from Firebase"""
    try:
        reviews_items_ref = db.reference('Data/Reviews')
        reviews_items = reviews_items_ref.get()

        if not reviews_items:
            return render_template('Reviews/reviews_items.html', error='No reviews items found')
        
        return render_template('Reviews/reviews_items.html', reviews=reviews_items)
    except Exception as e:
        print(f"Error getting reviews items: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Reviews/reviews_items.html', error=str(e))


@app.route('/reviews/<category>/<item_id>', methods=['GET'])
def get_reviews_item_details(category, item_id):
    """Get detailed reviews for a specific item"""
    try:
        reviews_ref = db.reference(f'Data/Reviews/{category}/{item_id}')
        reviews = reviews_ref.get()

        if not reviews:
            return render_template('Reviews/reviews_items_details.html', 
                                 error='No reviews found for this item',
                                 category=category,
                                 item_id=item_id)

        return render_template('Reviews/reviews_items_details.html',
                             reviews=reviews,
                             category=category,
                             item_id=item_id)
    except Exception as e:
        print(f"Error getting reviews for {category}/{item_id}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Reviews/reviews_items_details.html', 
                             error=str(e),
                             category=category,
                             item_id=item_id)


#################################################################################################################################
#                                         Sold Items REQUEST MAPPING                                                               #
#################################################################################################################################


@app.route('/sold-items', methods=['GET'])
def get_sold_items():
    """Get all sold items from Firebase"""
    try:
        sold_items_ref = db.reference('Data/SoldItems')
        sold_items = sold_items_ref.get()

        if not sold_items:
            return render_template('SoldItems/sold_items.html', error='No sold items found')

        return render_template('SoldItems/sold_items.html', sold_items=sold_items)
    except Exception as e:
        print(f"Error getting sold items: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('SoldItems/sold_items.html', error=str(e))


@app.route('/sold-items/<date>', methods=['GET'])
def get_sold_items_details(date):
    """Get detailed sold items for a specific date"""
    try:
        sold_items_ref = db.reference(f'Data/SoldItems/{date}')
        sold_items = sold_items_ref.get()

        if not sold_items:
            return render_template('SoldItems/sold_items_details.html', 
                                 error='No sold items found for this date',
                                 date=date)

        # Get category and item details for each sold item
        categories_ref = db.reference('Data/Categories')
        categories = categories_ref.get() or {}
        
        items_ref = db.reference('Data/CategoriesItems')
        all_items = items_ref.get() or {}
        
        # Enrich sold items with category and item details
        enriched_items = {}
        for item_key, item_data in sold_items.items():
            # Parse category and item ID from the composite key
            category_id, item_id = item_data['Id'].split('/')
            
            # Get category details
            category = categories.get(category_id, {})
            
            # Get item details
            item_details = all_items.get(category_id, {}).get(item_id, {})
            
            enriched_items[item_key] = {
                **item_data,
                'category': category.get('Name', 'Unknown Category'),
                'itemName': item_details.get('Name', 'Unknown Item'),
                'price': item_details.get('Price', 0),
                'unit': item_details.get('Unit', ''),
                'image': get_image_path(item_details.get('Image', ''))
            }

        return render_template('SoldItems/sold_items_details.html',
                             items=enriched_items,
                             date=date)
    except Exception as e:
        print(f"Error getting sold items for date {date}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('SoldItems/sold_items_details.html', 
                             error=str(e),
                             date=date)


#################################################################################################################################
#                                         USERS REQUEST MAPPING                                                                 #
#################################################################################################################################


@app.route('/users', methods=['GET'])
def get_all_users():
    """Get all users from Firebase"""
    try:
        # Get reference to the Users node
        users_ref = db.reference('Data/Users')
        # Get all users
        users = users_ref.get()
        if not users:
            return render_template('Users/users.html', error='No users found')
        
        return render_template('Users/users.html', users=users)
    except Exception as e:
        print(f"Error getting users: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Users/users.html', error=str(e))
        

@app.route('/users/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Get a specific user by their ID"""
    try:
        user_ref = db.reference(f'Data/Users/{user_id}')
        user = user_ref.get()
        if user is None:
            return render_template('Users/user.html', error='User not found')
        return render_template('Users/user.html', user=user)
    except Exception as e:
        print(f"Error getting user {user_id}: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Users/user.html', error=str(e))


@app.route('/users/<user_id>/orders', methods=['GET'])
def get_user_orders(user_id):
    """Get basic order information for a user"""
    try:
        # Get user's order IDs from Data/Users
        user_ref = db.reference(f'Data/Users/{user_id}')
        user_data = user_ref.get()
        
        if not user_data or 'orderBills' not in user_data:
            return render_template('Users/user_orders.html', error='No orders found for this user')
            
        user_order_ids = user_data['orderBills']
        if not user_order_ids:
            return render_template('Users/user_orders.html', error='No orders found for this user')
            
        # If orderBills is a reference, get its value
        if isinstance(user_order_ids, firebase_admin.db.Reference):
            user_order_ids = user_order_ids.get('/')
            
        # Get full order details from Data/OrderBills
        orders_ref = db.reference('Data/OrderBills')
        all_orders = orders_ref.get() or {}
        
        # Filter orders for this user and get basic info
        user_orders = {}
        if isinstance(user_order_ids, dict):
            for order_id, _ in user_order_ids.items():
                if order_id in all_orders:
                    order = all_orders[order_id]
                    # Only include basic order information
                    user_orders[order_id] = {
                        'orderBillId': order.get('orderBillId', ''),
                        'orderDate': order.get('orderDate', ''),
                        'status': order.get('status', ''),
                        'totalPrice': order.get('totalPrice', 0)
                    }
        
        return render_template('Users/user_orders.html', orders=user_orders, user_id=user_id)
    except Exception as e:
        print(f"Error getting orders for user {user_id}: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return render_template('Users/user_orders.html', error=str(e))


if __name__ == "__main__":
    app.run(debug=True)