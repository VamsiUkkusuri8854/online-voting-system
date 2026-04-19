import os
import bcrypt
import time
import logging
import jwt
import datetime
from flask import Blueprint, request, jsonify
from database import get_db
from bson.objectid import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

auth_bp = Blueprint('auth', __name__)
SECRET_KEY = os.getenv('SECRET_KEY')

def get_users_collection():
    db = get_db()
    return db["users"] if db is not None else None

def generate_token(user_id, is_admin):
    payload = {
        'user_id': str(user_id),
        'is_admin': is_admin,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

@auth_bp.route('/register', methods=['POST'])
def register():
    users_collection = get_users_collection()
    if users_collection is None:
        return jsonify({'message': 'Database connection error!'}), 503

    start_total = time.perf_counter()
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not all([name, email, password]):
        return jsonify({'message': 'All fields are required!'}), 400

    start_db = time.perf_counter()
    if users_collection.find_one({'email': email}, {'_id': 1}):
        return jsonify({'message': 'User with this email already exists!'}), 400
    db_time = (time.perf_counter() - start_db) * 1000

    start_hash = time.perf_counter()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=10))
    hash_time = (time.perf_counter() - start_hash) * 1000

    start_insert = time.perf_counter()
    user_id = users_collection.insert_one({
        'name': name,
        'email': email,
        'password': hashed_password,
        'is_admin': False,
        'has_voted': False
    }).inserted_id
    insert_time = (time.perf_counter() - start_insert) * 1000

    total_time = (time.perf_counter() - start_total) * 1000
    logging.info(f"REGISTER: Total={total_time:.2f}ms | DB_Check={db_time:.2f}ms | Hash={hash_time:.2f}ms | Insert={insert_time:.2f}ms")

    return jsonify({'message': 'User registered successfully!'}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    users_collection = get_users_collection()
    if users_collection is None:
        return jsonify({'message': 'Database connection error!'}), 503

    start_total = time.perf_counter()
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'message': 'Email and password required!'}), 400

    start_db = time.perf_counter()
    user = users_collection.find_one({'email': email}, {'password': 1, 'name': 1, 'email': 1, 'is_admin': 1, 'has_voted': 1})
    db_time = (time.perf_counter() - start_db) * 1000

    if not user:
        return jsonify({'message': 'Invalid email or password!'}), 401

    start_hash = time.perf_counter()
    is_valid = bcrypt.checkpw(password.encode('utf-8'), user['password'])
    hash_time = (time.perf_counter() - start_hash) * 1000

    if is_valid:
        token = generate_token(user['_id'], user.get('is_admin', False))
        
        total_time = (time.perf_counter() - start_total) * 1000
        logging.info(f"LOGIN: Total={total_time:.2f}ms | DB_Fetch={db_time:.2f}ms | Check_Hash={hash_time:.2f}ms")

        return jsonify({
            'message': 'Login successful!',
            'token': token,
            'user': {
                'id': str(user['_id']),
                'name': user['name'],
                'email': user['email'],
                'is_admin': user.get('is_admin', False),
                'has_voted': user.get('has_voted', False)
            }
        }), 200

    return jsonify({'message': 'Invalid email or password!'}), 401

@auth_bp.route('/user', methods=['GET'])
def get_user_info():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({'message': 'Token missing or invalid!'}), 401
    
    token = auth_header.split(' ')[1]
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_id = decoded['user_id']
        
        users_collection = get_users_collection()
        user = users_collection.find_one({'_id': ObjectId(user_id)}, {'password': 0})
        
        if not user:
            return jsonify({'message': 'User not found!'}), 404
            
        user['id'] = str(user['_id'])
        del user['_id']
        return jsonify(user), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'message': 'Token expired!'}), 401
    except Exception as e:
        return jsonify({'message': 'Token invalid!'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    # With JWT, logout is handled by the client by deleting the token.
    # We can perform any server-side cleanup if needed (none required for simple JWT).
    return jsonify({'message': 'Logout successful!'}), 200
