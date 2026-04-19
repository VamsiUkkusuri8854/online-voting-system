import os
import jwt
from functools import wraps
from flask import request, jsonify
from bson.objectid import ObjectId

SECRET_KEY = os.getenv('SECRET_KEY')

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message': 'Authentication required!'}), 401
        
        token = auth_header.split(' ')[1]
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user = {
                'user_id': decoded['user_id'],
                'is_admin': decoded.get('is_admin', False)
            }
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired!'}), 401
        except Exception:
            return jsonify({'message': 'Invalid token!'}), 401
            
        return f(current_user, *args, **kwargs)

    return decorated

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated(current_user, *args, **kwargs):
        if not current_user.get('is_admin'):
            return jsonify({'message': 'Admin privileges required!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated
