
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin', 'staff', 'user'
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)  # Admin can deactivate / blacklist
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False, lazy=True, cascade='all, delete-orphan')
    assigned_treks = db.relationship('Trek', backref='assigned_staff', lazy=True)

    def set_password(self, password):
        """Hash and store user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify stored password hash against provided password."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Serialize user data for API responses (excluding password hash)."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'phone': self.phone,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class StaffProfile(db.Model):
    #Staff Profile containing specialized details for trek guides/staff.
    
    __tablename__ = 'staff_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    experience_years = db.Column(db.Integer, default=0)
    bio = db.Column(db.Text, nullable=True)
    emergency_contact = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), default='Active')  # 'Active', 'Inactive'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'experience_years': self.experience_years,
            'bio': self.bio,
            'emergency_contact': self.emergency_contact,
            'status': self.status
        }


class Trek(db.Model):
    """
    Trek model representing a trekking expedition/route.
    """
    __tablename__ = 'treks'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)  # 'Easy', 'Moderate', 'Hard'
    duration_days = db.Column(db.Integer, nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.0)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(50), default='Open')  # 'Pending', 'Approved', 'Open', 'Closed', 'Completed'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship with bookings
    bookings = db.relationship('Booking', backref='trek', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'location': self.location,
            'difficulty': self.difficulty,
            'duration_days': self.duration_days,
            'total_slots': self.total_slots,
            'available_slots': self.available_slots,
            'price': self.price,
            'assigned_staff_id': self.assigned_staff_id,
            'assigned_staff_name': self.assigned_staff.full_name if self.assigned_staff else None,
            'status': self.status,
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else None,
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Booking(db.Model):
    """
    Booking record linking a Trekker to a Trek.
    """
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    slots_booked = db.Column(db.Integer, default=1, nullable=False)
    total_price = db.Column(db.Float, default=0.0, nullable=False)
    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50), default='Booked')  # 'Booked', 'Cancelled', 'Completed'
    payment_status = db.Column(db.String(50), default='Paid')  # 'Pending', 'Paid'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'trek_id': self.trek_id,
            'trek_name': self.trek.name if self.trek else None,
            'trek_location': self.trek.location if self.trek else None,
            'slots_booked': self.slots_booked,
            'total_price': self.total_price,
            'booking_date': self.booking_date.strftime('%Y-%m-%d %H:%M:%S') if self.booking_date else None,
            'status': self.status,
            'payment_status': self.payment_status
        }


def init_db(app):
    """
    Programmatically creates all tables and seeds the default superuser Admin.
    Manual database creation is strictly avoided per project specifications.
    """
    with app.app_context():
        # Create all tables programmatically
        db.create_all()

        # Check if an Admin user already exists
        admin_user = User.query.filter_by(role='admin').first()
        if not admin_user:
            admin = User(
                username='admin',
                email='admin@trekking.com',
                role='admin',
                full_name='System Administrator',
                phone='9876543210',
                is_active=True
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Default Admin created: admin@trekking.com / Admin@123")
        else:
            print("ℹ️ Admin user already exists.")
