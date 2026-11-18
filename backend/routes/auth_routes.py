from functools import wraps
from datetime import datetime, timedelta, timezone
import jwt
from flask import Blueprint, request, jsonify, current_app
from backend.models import db, User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def generate_token(user):
    # Create a 24-hour JWT token for the logged in user
    secret = current_app.config.get('SECRET_KEY', 'default-jwt-secret-key-mad2')
    payload = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(days=1)
    }
    return jwt.encode(payload, secret, algorithm='HS256')


def token_required(f):
    # Decorator to check if the user sent a valid Bearer token
    @wraps(f)
    def decorated(*args, **kwargs):
        header = request.headers.get('Authorization', '')
        if not header.startswith('Bearer '):
            return jsonify({'success': False, 'message': 'Missing or invalid token'}), 401

        token = header.split(' ')[1]
        secret = current_app.config.get('SECRET_KEY', 'default-jwt-secret-key-mad2')

        try:
            data = jwt.decode(token, secret, algorithms=['HS256'])
            user = User.query.get(data.get('user_id'))
            if not user:
                return jsonify({'success': False, 'message': 'User not found'}), 401
            if not user.is_active:
                return jsonify({'success': False, 'message': 'Account is deactivated'}), 403
        except Exception:
            return jsonify({'success': False, 'message': 'Invalid or expired token'}), 401

        return f(user, *args, **kwargs)
    return decorated


def role_required(allowed_roles):
    # Decorator to check user role (e.g. admin or staff)
    def decorator(f):
        @wraps(f)
        def wrapper(current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                return jsonify({'success': False, 'message': 'Permission denied'}), 403
            return f(current_user, *args, **kwargs)
        return wrapper
    return decorator


@auth_bp.route('/register', methods=['POST'])
def register():
    # User registration for regular trekkers
    data = request.get_json() or {}

    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()

    if not username or not email or not password or not full_name:
        return jsonify({'success': False, 'message': 'All fields are required'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 409

    user = User(
        username=username,
        email=email,
        full_name=full_name,
        phone=phone,
        role='user',
        is_active=True
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Registration successful',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    # Login for admin, staff, and trekkers
    data = request.get_json() or {}
    identifier = (data.get('username') or data.get('email', '')).strip()
    password = data.get('password', '').strip()

    if not identifier or not password:
        return jsonify({'success': False, 'message': 'Please enter username and password'}), 400

    # Look up user by username or email
    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if not user or not user.check_password(password):
        return jsonify({'success': False, 'message': 'Incorrect username or password'}), 401

    if not user.is_active:
        return jsonify({'success': False, 'message': 'Account is deactivated'}), 403

    token = generate_token(user)
    return jsonify({
        'success': True,
        'message': f'Welcome {user.full_name}',
        'token': token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    # Return profile of current user
    return jsonify({'success': True, 'user': current_user.to_dict()}), 200


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    # Update profile fields
    data = request.get_json() or {}

    if 'full_name' in data:
        current_user.full_name = data['full_name'].strip()
    if 'phone' in data:
        current_user.phone = data['phone'].strip()
    if 'emergency_contact_name' in data:
        current_user.emergency_contact_name = data['emergency_contact_name']
    if 'emergency_contact_phone' in data:
        current_user.emergency_contact_phone = data['emergency_contact_phone']
    if 'blood_group' in data:
        current_user.blood_group = data['blood_group']
    if 'medical_notes' in data:
        current_user.medical_notes = data['medical_notes']

    db.session.commit()
    return jsonify({
        'success': True,
        'message': 'Profile updated',
        'user': current_user.to_dict()
    }), 200


@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    # Quick check for frontend router
    return jsonify({'success': True, 'valid': True, 'user': current_user.to_dict()}), 200
