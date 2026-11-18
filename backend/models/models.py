from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    """
    User model representing all roles: 'admin', 'staff', and 'user' (trekker).
    """
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # 'admin', 'staff', 'user'
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)

    # Trekker Emergency & Medical Information
    emergency_contact_name = db.Column(db.String(100), nullable=True)
    emergency_contact_phone = db.Column(db.String(30), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    medical_notes = db.Column(db.Text, nullable=True)

    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    staff_profile = db.relationship('StaffProfile', backref='user', uselist=False, lazy=True, cascade='all, delete-orphan')
    assigned_treks = db.relationship('Trek', backref='assigned_staff', lazy=True)
    notifications = db.relationship('Notification', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Hash and save the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Convert model data into dictionary for JSON response."""
        created_at_str = None
        if self.created_at:
            created_at_str = self.created_at.strftime('%Y-%m-%d %H:%M:%S')

        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'phone': self.phone,
            'emergency_contact_name': self.emergency_contact_name,
            'emergency_contact_phone': self.emergency_contact_phone,
            'blood_group': self.blood_group,
            'medical_notes': self.medical_notes,
            'is_active': self.is_active,
            'created_at': created_at_str
        }


class StaffProfile(db.Model):
    """
    Profile for staff/guides with experience and background info.
    """
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
    Trek route/event with slot management and itinerary details.
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
    itinerary = db.Column(db.Text, nullable=True)
    gear_checklist = db.Column(db.Text, nullable=True)

    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.String(50), default='Open')  # 'Open', 'Closed', 'Started', 'Completed'
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    bookings = db.relationship('Booking', backref='trek', lazy=True, cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='trek', lazy=True, cascade='all, delete-orphan')

    @property
    def average_rating(self):
        """Calculate average rating across all reviews."""
        if not self.reviews:
            return 5.0
        total_rating = 0
        for review in self.reviews:
            total_rating += review.rating
        return round(total_rating / len(self.reviews), 1)

    @property
    def review_count(self):
        """Total count of reviews for this trek."""
        return len(self.reviews)

    def to_dict(self):
        """Convert trek to dictionary for API responses."""
        staff_name = None
        if self.assigned_staff:
            staff_name = self.assigned_staff.full_name

        start_date_str = None
        if self.start_date:
            start_date_str = self.start_date.strftime('%Y-%m-%d')

        end_date_str = None
        if self.end_date:
            end_date_str = self.end_date.strftime('%Y-%m-%d')

        created_at_str = None
        if self.created_at:
            created_at_str = self.created_at.strftime('%Y-%m-%d %H:%M:%S')

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
            'itinerary': self.itinerary,
            'gear_checklist': self.gear_checklist,
            'assigned_staff_id': self.assigned_staff_id,
            'assigned_staff_name': staff_name,
            'status': self.status,
            'average_rating': self.average_rating,
            'review_count': self.review_count,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'created_at': created_at_str
        }


class Booking(db.Model):
    """
    Booking made by a trekker for a trek.
    """
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    slots_booked = db.Column(db.Integer, default=1, nullable=False)
    total_price = db.Column(db.Float, default=0.0, nullable=False)
    booking_date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(50), default='Booked')  # 'Booked', 'Cancelled', 'Completed'
    payment_status = db.Column(db.String(50), default='Paid')  # 'Pending', 'Paid'
    transaction_id = db.Column(db.String(80), nullable=True)
    payment_method = db.Column(db.String(50), default='Simulated UPI')
    check_in_status = db.Column(db.String(30), default='Pending')  # 'Pending', 'Checked In', 'No Show'
    medical_cleared = db.Column(db.Boolean, default=True)

    def to_dict(self):
        """Convert booking to dictionary format for JSON responses."""
        user_name = None
        if self.user:
            user_name = self.user.full_name

        trek_name = None
        trek_location = None
        if self.trek:
            trek_name = self.trek.name
            trek_location = self.trek.location

        booking_date_str = None
        if self.booking_date:
            booking_date_str = self.booking_date.strftime('%Y-%m-%d %H:%M:%S')

        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': user_name,
            'trek_id': self.trek_id,
            'trek_name': trek_name,
            'trek_location': trek_location,
            'slots_booked': self.slots_booked,
            'total_price': self.total_price,
            'booking_date': booking_date_str,
            'status': self.status,
            'payment_status': self.payment_status,
            'transaction_id': self.transaction_id,
            'payment_method': self.payment_method,
            'check_in_status': self.check_in_status,
            'medical_cleared': self.medical_cleared
        }


class Notification(db.Model):
    """
    In-app user notifications for confirmations, cancellations, and alerts.
    """
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default='info')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        created_at_str = None
        if self.created_at:
            created_at_str = self.created_at.strftime('%Y-%m-%d %H:%M:%S')

        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'message': self.message,
            'notification_type': self.notification_type,
            'is_read': self.is_read,
            'created_at': created_at_str
        }


class Review(db.Model):
    """
    User review and rating for a trek (1 to 5 stars).
    """
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey('treks.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('reviews', lazy=True, cascade='all, delete-orphan'))

    def to_dict(self):
        user_name = 'Anonymous Trekker'
        if self.user:
            user_name = self.user.full_name

        created_at_str = None
        if self.created_at:
            created_at_str = self.created_at.strftime('%Y-%m-%d %H:%M:%S')

        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': user_name,
            'trek_id': self.trek_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': created_at_str
        }


def init_db(app):
    """
    Creates tables and seeds default admin account on startup.
    """
    with app.app_context():
        # Create all database tables
        db.create_all()

        # Add any missing columns for backward compatibility
        from sqlalchemy import text
        with db.engine.connect() as connection:
            migration_queries = [
                "ALTER TABLE bookings ADD COLUMN transaction_id VARCHAR(80)",
                "ALTER TABLE bookings ADD COLUMN payment_method VARCHAR(50) DEFAULT 'Simulated UPI'",
                "ALTER TABLE users ADD COLUMN emergency_contact_name VARCHAR(100)",
                "ALTER TABLE users ADD COLUMN emergency_contact_phone VARCHAR(30)",
                "ALTER TABLE users ADD COLUMN blood_group VARCHAR(10)",
                "ALTER TABLE users ADD COLUMN medical_notes TEXT",
                "ALTER TABLE treks ADD COLUMN itinerary TEXT",
                "ALTER TABLE treks ADD COLUMN gear_checklist TEXT",
                "ALTER TABLE bookings ADD COLUMN check_in_status VARCHAR(30) DEFAULT 'Pending'",
                "ALTER TABLE bookings ADD COLUMN medical_cleared BOOLEAN DEFAULT 1"
            ]
            for query in migration_queries:
                try:
                    connection.execute(text(query))
                    connection.commit()
                except Exception:
                    # Column already exists, safe to ignore
                    pass

        # Ensure default superuser admin exists
        existing_admin = User.query.filter_by(role='admin').first()
        if not existing_admin:
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
            print(" Default Admin created: admin@trekking.com / Admin@123")
        else:
            print(" Admin user already exists.")
