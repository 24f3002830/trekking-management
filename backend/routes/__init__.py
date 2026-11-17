"""
Routes package initialization.
"""

from .auth_routes import auth_bp, token_required, role_required

__all__ = ['auth_bp', 'token_required', 'role_required']
