from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from models import User
import jwt
import datetime
from functools import wraps
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

# Create a Blueprint for authentication-related routes
auth_bp = Blueprint('auth', __name__)

# Secret key for JWT encoding/decoding
SECRET_KEY = "your_secret_key_here"  # Replace this with a strong secret key in production

# Decorator to protect routes that require authentication
def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization'].split(" ")[1]  # Extract token from Authorization header

        if not token:
            return jsonify({'message': 'Token is missing!'}), 403

        try:
            # Decode the JWT token
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 401

        return f(current_user, *args, **kwargs)  # Pass the current user to the route function

    return decorated_function

# Registration endpoint
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields!'}), 400

    # Check if the user already exists
    existing_user = User.query.filter_by(email=data['email']).first()
    if existing_user:
        return jsonify({'message': 'User already exists!'}), 409

    # Hash the password before storing it
    hashed_password = generate_password_hash(data['password'], method='sha256')

    # Create a new user
    new_user = User(
        name=data['name'],
        email=data['email'],
        password_hash=hashed_password,
        role='customer'  # Default role can be set here, 'customer' for example
    )
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User registered successfully!'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error registering user: {str(e)}'}), 500

# Login endpoint to authenticate user and return JWT token
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing required fields!'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'message': 'Invalid email or password!'}), 401
    
    # Generate JWT token for the user
    access_token = create_access_token(identity=user.id, fresh=True)
    
    return jsonify({'access_token': access_token}), 200

# Protected route example: Get user profile
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    # Get the current user from the JWT identity
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()
    
    if not user:
        return jsonify({'message': 'User not found!'}), 404
    
    return jsonify({
        'id': user.id,
        'name': user.name,
        'email': user.email,
        'role': user.role
    }), 200

# Change password route (requires authentication)
@auth_bp.route('/change-password', methods=['PUT'])
@jwt_required()
def change_password():
    data = request.get_json()
    
    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({'message': 'Missing required fields!'}), 400

    # Get the current user from the JWT token
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()

    if not user or not check_password_hash(user.password_hash, data['old_password']):
        return jsonify({'message': 'Old password is incorrect!'}), 401
    
    # Hash the new password and update it
    user.password_hash = generate_password_hash(data['new_password'], method='sha256')

    try:
        db.session.commit()
        return jsonify({'message': 'Password updated successfully!'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating password: {str(e)}'}), 500

