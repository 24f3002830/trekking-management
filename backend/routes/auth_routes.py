"""
Authentication & Authorization Routes for Trekking Management Application.
Handles User (Trekker) registration, login for all roles, JWT issuance, and RBAC decorators.
"""

from functools import wraps
from datetime import datetime, timedelta
import jwt
from flask import Blueprint, request, jsonify, current_app
from backend.models import db, User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


def generate_token(user):
    """
    Generate a JWT token with user ID, role, and expiration.
    """
    secret_key = current_app.config.get('SECRET_KEY', 'default-jwt-secret-key-mad2')
    payload = {
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(days=1)  # Token valid for 24 hours
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token


def token_required(f):
    """
    Decorator to protect routes requiring authentication.
    Injects 'current_user' into the protected route handler.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', None)
        if not auth_header:
            return jsonify({'success': False, 'message': 'Authorization header is missing.'}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({'success': False, 'message': 'Invalid token format. Use: Bearer <token>'}), 401

        token = parts[1]
        secret_key = current_app.config.get('SECRET_KEY', 'default-jwt-secret-key-mad2')

        try:
            payload = jwt.decode(token, secret_key, algorithms=['HS256'])
            user_id = payload.get('user_id')
            current_user = User.query.get(user_id)

            if not current_user:
                return jsonify({'success': False, 'message': 'User associated with token not found.'}), 401

            if not current_user.is_active:
                return jsonify({
                    'success': False,
                    'message': 'Your account has been deactivated or blacklisted by the Administrator.'
                }), 403

        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Session expired. Please log in again.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid authentication token.'}), 401

        return f(current_user, *args, **kwargs)

    return decorated


def role_required(allowed_roles):
    """
    Decorator to enforce Role-Based Access Control (RBAC).
    Usage: @role_required(['admin']) or @role_required(['admin', 'staff'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(current_user, *args, **kwargs):
            if current_user.role not in allowed_roles:
                return jsonify({
                    'success': False,
                    'message': f'Access forbidden: required role is one of {allowed_roles}, but you have role "{current_user.role}".'
                }), 403
            return f(current_user, *args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User (Trekker) registration endpoint.
    Only general trekkers can self-register.
    Admin and Staff cannot register here (Admin is pre-seeded, Staff is created by Admin).
    """
    data = request.get_json() or {}

    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()

    # Field validations
    if not username or not email or not password or not full_name:
        return jsonify({
            'success': False,
            'message': 'Username, email, password, and full name are required.'
        }), 400

    if len(password) < 6:
        return jsonify({
            'success': False,
            'message': 'Password must be at least 6 characters long.'
        }), 400

    # Check for existing user
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username is already taken.'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email is already registered.'}), 409

    # Create new Trekker (User role is strictly 'user')
    new_user = User(
        username=username,
        email=email,
        full_name=full_name,
        phone=phone,
        role='user',  # Self-registration is strictly for Trekkers
        is_active=True
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Registration successful! You can now log in.',
        'user': new_user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Unified login endpoint for all roles: Admin, Trek Staff, and Trekkers.
    Accepts email or username along with password.
    """
    data = request.get_json() or {}

    identifier = data.get('username') or data.get('email', '')
    identifier = identifier.strip()
    password = data.get('password', '').strip()

    if not identifier or not password:
        return jsonify({
            'success': False,
            'message': 'Username/email and password are required.'
        }), 400

    # Search by either username or email
    user = User.query.filter(
        (User.username == identifier) | (User.email == identifier.lower())
    ).first()

    if not user or not user.check_password(password):
        return jsonify({
            'success': False,
            'message': 'Invalid credentials. Please check your username/email and password.'
        }), 401

    # Check if the account is deactivated or blacklisted
    if not user.is_active:
        return jsonify({
            'success': False,
            'message': 'Your account has been deactivated or blacklisted. Contact the administrator.'
        }), 403

    # Generate JWT token
    token = generate_token(user)

    return jsonify({
        'success': True,
        'message': f'Welcome back, {user.full_name}!',
        'token': token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """
    Get profile information of the currently authenticated user.
    """
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """
    Update profile details for the currently authenticated user.
    """
    data = request.get_json() or {}

    full_name = data.get('full_name')
    phone = data.get('phone')

    if full_name:
        current_user.full_name = full_name.strip()
    if phone is not None:
        current_user.phone = phone.strip()

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Profile updated successfully.',
        'user': current_user.to_dict()
    }), 200


@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """
    Verify if the provided token is valid and return active user profile.
    Useful for Vue frontend router navigation guards.
    """
    return jsonify({
        'success': True,
        'valid': True,
        'user': current_user.to_dict()
    }), 200
