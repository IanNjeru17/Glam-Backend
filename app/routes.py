from flask import Blueprint, request, jsonify
from datetime import timedelta
from . import db, bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from .model import User, ProductCategory, Product, Order, OrderItem, Transaction
from sqlalchemy.exc import IntegrityError
import random
import string

main_bp = Blueprint('main', __name__)

# Login route
@main_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()

    if user and bcrypt.check_password_hash(user.password, password):
        # Set JWT token to expire in 2 days
        access_token = create_access_token(identity=user.uid, expires_delta=timedelta(days=2))
        return jsonify({"isAdmin" : user.is_admin, "access_token": access_token}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401
    
# Protect routes with JWT
@main_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])
# Get a single user by ID
@main_bp.route('/users/<string:uid>', methods=['GET'])
def get_user(uid):
    user = User.query.get_or_404(uid)
    return jsonify(user.to_dict())

def generate_uid():
    return ''.join(random.choices(string.digits, k=6))  # Random 6-digit UID


@main_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    
    # Hash the password before storing it
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    # Create a new user instance with hashed password
    new_user = User(
        uid=generate_uid(),
        name=data['name'],
        email=data['email'],
        phone=data['phone'],
        password=hashed_password,  # Use the hashed password
        is_admin=data.get('is_admin', False)
    )
    
    # Try to add the user to the database
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"status": True, "message": "User created successfully"}), 201
    except IntegrityError:
        db.session.rollback()
        return jsonify({"status": False, "error": "Email already exists"}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": False,  "error": "An internal server error occurred"}), 500
    
# Update an existing user
@main_bp.route('/users/<string:uid>', methods=['PUT'])
@jwt_required()
def update_user(uid):
    user = User.query.get_or_404(uid)
    data = request.get_json()
    user.name = data.get('name', user.name)
    user.email = data.get('email', user.email)
    user.phone = data.get('phone', user.phone)
    user.password = data.get('password', user.password)
    user.is_admin = data.get('is_admin', user.is_admin)
    db.session.commit()
    return jsonify(user.to_dict())

# Delete a user
@main_bp.route('/users/<string:uid>', methods=['DELETE'])
@jwt_required()
def delete_user(uid):
    user = User.query.get_or_404(uid)
    db.session.delete(user)
    db.session.commit()
    return '', 204


# Get all product categories
@main_bp.route('/product_categories', methods=['GET'])
# @jwt_required()
def get_product_categories():
    categories = ProductCategory.query.all()
    return jsonify([category.to_dict() for category in categories])

# Get a single product category by ID
@main_bp.route('/product_categories/<string:category_id>', methods=['GET'])
def get_product_category(category_id):
    category = ProductCategory.query.get_or_404(category_id)
    return jsonify(category.to_dict())

# Create a new product category
@main_bp.route('/product_categories', methods=['POST'])
def create_product_category():
    data = request.get_json()
    new_category = ProductCategory(id=generate_uid(), category_name=data['category_name'])
    db.session.add(new_category)
    db.session.commit()
    return jsonify(new_category.to_dict()), 201

# Update an existing product category
@main_bp.route('/product_categories/<string:category_id>', methods=['PUT'])
def update_product_category(category_id):
    category = ProductCategory.query.get_or_404(category_id)
    data = request.get_json()
    category.category_name = data.get('category_name', category.category_name)
    db.session.commit()
    return jsonify(category.to_dict())

# Delete a product category
@main_bp.route('/product_categories/<string:category_id>', methods=['DELETE'])
def delete_product_category(category_id):
    category = ProductCategory.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    return '', 204

# Get all products
@main_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])

# Get a single product by ID
@main_bp.route('/products/<string:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

# Create a new product
@main_bp.route('/products', methods=['POST'])
def create_product():
    data = request.get_json()
    new_product = Product(
        id=generate_uid(),
        category_id=data['category_id'],
        name=data['name'],
        description=data['description'],
        image_url=data.get('image_url'),
        price=data['price'],
        stock=data['stock'],
        status=data.get('status', True)
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify(new_product.to_dict()), 201

# Update an existing product
@main_bp.route('/products/<string:product_id>', methods=['PUT'])
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    data = request.get_json()
    product.category_id = data.get('category_id', product.category_id)
    product.name = data.get('name', product.name)
    product.description = data.get('description', product.description)
    product.image_url = data.get('image_url', product.image_url)
    product.price = data.get('price', product.price)
    product.stock = data.get('stock', product.stock)
    product.status = data.get('status', product.status)
    db.session.commit()
    return jsonify(product.to_dict())

# Delete a product
@main_bp.route('/products/<string:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return '', 204

# Get all orders
@main_bp.route('/orders', methods=['GET'])
def get_orders():
    orders = Order.query.all()
    return jsonify([order.to_dict() for order in orders])

# Get a single order by ID
@main_bp.route('/orders/<string:order_id>', methods=['GET'])
def get_order(order_id):
    order = Order.query.get_or_404(order_id)
    return jsonify(order.to_dict())

# Create a new order
@main_bp.route('/orders', methods=['POST'])
def create_order():
    data = request.get_json()
    new_order = Order(
        id=generate_uid(),
        user_id=data['user_id'],
        total_amount=data['total_amount'],
        status=data['status']
    )
    db.session.add(new_order)
    db.session.commit()
    return jsonify(new_order.to_dict()), 201

# Update an existing order
@main_bp.route('/orders/<string:order_id>', methods=['PUT'])
def update_order(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.get_json()
    order.status = data.get('status', order.status)
    db.session.commit()
    return jsonify(order.to_dict())

# Delete an order
@main_bp.route('/orders/<string:order_id>', methods=['DELETE'])
def delete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)
    db.session.commit()
    return '', 204


# Get all transactions
@main_bp.route('/transactions', methods=['GET'])
def get_transactions():
    transactions = Transaction.query.all()
    return jsonify([transaction.to_dict() for transaction in transactions])

# Get a single transaction by ID
@main_bp.route('/transactions/<string:transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    return jsonify(transaction.to_dict())

# Create a new transaction
@main_bp.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.get_json()
    new_transaction = Transaction(
        id=generate_uid(),
        user_id=data['user_id'],
        order_id=data['order_id'],
        amount=data['amount'],
        status=data['status']
    )
    db.session.add(new_transaction)
    db.session.commit()
    return jsonify(new_transaction.to_dict()), 201

# Update an existing transaction
@main_bp.route('/transactions/<string:transaction_id>', methods=['PUT'])
def update_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    data = request.get_json()
    transaction.status = data.get('status', transaction.status)
    db.session.commit()
    return jsonify(transaction.to_dict())

# Delete a transaction
@main_bp.route('/transactions/<string:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    db.session.commit()
    return '', 204
