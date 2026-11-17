"""
Routes package initialization.
Exports all API blueprints for Trekking Management Application.
"""

from .auth_routes import auth_bp, token_required, role_required
from .admin_routes import admin_bp
from .staff_routes import staff_bp
from .trek_routes import trek_bp
from .booking_routes import booking_bp

__all__ = [
    'auth_bp',
    'admin_bp',
    'staff_bp',
    'trek_bp',
    'booking_bp',
    'token_required',
    'role_required'
]
