"""
Main Flask application entry point for Trekking Management Application (TMA).
Configures SQLite database, CORS, JWT secrets, and blueprints.
"""

import os
import sys

# Ensure parent directory is in python path for module imports
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify
from flask_cors import CORS
from backend.models import db, init_db
from backend.routes import auth_bp


def create_app():
    """Application factory for Trekking Management Application."""
    app = Flask(__name__)

    # Database configuration - SQLite only (per project specification)
    db_path = os.path.join(BASE_DIR, 'trekking.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Security configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'tma-mad2-super-secret-key-2026')

    # Enable CORS for Vue.js frontend integration
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Initialize database
    db.init_app(app)

    # Register API blueprints
    app.register_blueprint(auth_bp)

    # Programmatically create database tables and seed initial Admin
    init_db(app)

    # Health check route
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({
            'success': True,
            'message': 'Trekking Management API is running healthy.',
            'version': '2.0'
        }), 200

    return app


# Create application instance
app = create_app()

if __name__ == '__main__':
    print("🚀 Starting Trekking Management Application on http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
