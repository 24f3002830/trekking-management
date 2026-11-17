"""
Admin Routes for Trekking Management Application.
Handles superuser dashboard, staff management, user moderation (blacklist/deactivate),
staff-to-trek assignment, bookings overview, and statistical reports.
"""

from flask import Blueprint, request, jsonify
from backend.models import db, User, StaffProfile, Trek, Booking
from backend.routes.auth_routes import token_required, role_required
from backend.cache import clear_cache

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/dashboard', methods=['GET'])
@token_required
@role_required(['admin'])
def admin_dashboard(current_user):
    """
    Admin Dashboard summary metrics:
      - Total treks
      - Total regular users (trekkers)
      - Total staff members
      - Total bookings
      - Total revenue
    """
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    active_bookings = Booking.query.filter_by(status='Booked').count()

    # Calculate total revenue
    all_bookings = Booking.query.filter(Booking.status != 'Cancelled').all()
    total_revenue = sum(b.total_price for b in all_bookings)

    recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()

    return jsonify({
        'success': True,
        'metrics': {
            'total_treks': total_treks,
            'total_users': total_users,
            'total_staff': total_staff,
            'total_bookings': total_bookings,
            'active_bookings': active_bookings,
            'total_revenue': round(total_revenue, 2)
        },
        'recent_bookings': [b.to_dict() for b in recent_bookings]
    }), 200


@admin_bp.route('/users', methods=['GET'])
@token_required
@role_required(['admin'])
def list_users(current_user):
    """
    Search and list users, optionally filtered by role and active status.
    Query params:
      - role: 'user', 'staff', 'admin'
      - search: search by username, email, or full_name
      - active: 'true' or 'false'
    """
    role = request.args.get('role', '').strip()
    search = request.args.get('search', '').strip().lower()
    active = request.args.get('active', '').strip().lower()

    query = User.query

    if role:
        query = query.filter_by(role=role)
    if active in ['true', 'false']:
        query = query.filter_by(is_active=(active == 'true'))
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%'))
        )

    users = query.order_by(User.created_at.desc()).all()
    return jsonify({
        'success': True,
        'count': len(users),
        'users': [u.to_dict() for u in users]
    }), 200


@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@token_required
@role_required(['admin'])
def toggle_user_status(current_user, user_id):
    """
    Deactivate or blacklist / reactivate a user or staff member.
    Admin cannot deactivate themselves.
    """
    if current_user.id == user_id:
        return jsonify({'success': False, 'message': 'Admin cannot deactivate their own account.'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found.'}), 404

    data = request.get_json() or {}
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])
    else:
        # Toggle current status
        user.is_active = not user.is_active

    db.session.commit()

    action = "activated" if user.is_active else "deactivated / blacklisted"
    return jsonify({
        'success': True,
        'message': f'User "{user.username}" has been {action}.',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/staff', methods=['POST'])
@token_required
@role_required(['admin'])
def create_staff(current_user):
    """
    Admin creates a new Trek Staff member.
    Trek Staff cannot self-register; they must be created by Admin.
    """
    data = request.get_json() or {}

    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    experience_years = data.get('experience_years', 0)
    bio = data.get('bio', '').strip()
    emergency_contact = data.get('emergency_contact', '').strip()

    if not username or not email or not password or not full_name:
        return jsonify({
            'success': False,
            'message': 'Username, email, password, and full name are required.'
        }), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username is already taken.'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email is already registered.'}), 409

    # Create User with role='staff'
    staff_user = User(
        username=username,
        email=email,
        full_name=full_name,
        phone=phone,
        role='staff',
        is_active=True
    )
    staff_user.set_password(password)
    db.session.add(staff_user)
    db.session.flush()  # Obtain staff_user.id

    # Create associated StaffProfile
    profile = StaffProfile(
        user_id=staff_user.id,
        experience_years=int(experience_years),
        bio=bio,
        emergency_contact=emergency_contact,
        status='Active'
    )
    db.session.add(profile)
    db.session.commit()

    response_data = staff_user.to_dict()
    response_data['profile'] = profile.to_dict()

    return jsonify({
        'success': True,
        'message': f'Staff member "{full_name}" created successfully.',
        'staff': response_data
    }), 201


@admin_bp.route('/staff', methods=['GET'])
@token_required
@role_required(['admin'])
def list_staff(current_user):
    """
    List all staff members and their assigned trek counts.
    """
    staff_users = User.query.filter_by(role='staff').all()
    results = []

    for s in staff_users:
        s_dict = s.to_dict()
        s_dict['profile'] = s.staff_profile.to_dict() if s.staff_profile else None
        s_dict['assigned_treks_count'] = len(s.assigned_treks)
        results.append(s_dict)

    return jsonify({
        'success': True,
        'count': len(results),
        'staff': results
    }), 200


@admin_bp.route('/treks/<int:trek_id>/assign-staff', methods=['PUT'])
@token_required
@role_required(['admin'])
def assign_staff_to_trek(current_user, trek_id):
    """
    Assign a designated staff member to a trek.
    """
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found.'}), 404

    data = request.get_json() or {}
    staff_id = data.get('staff_id')

    if staff_id is not None:
        staff_user = User.query.filter_by(id=staff_id, role='staff').first()
        if not staff_user:
            return jsonify({'success': False, 'message': 'Selected staff member does not exist.'}), 404
        if not staff_user.is_active:
            return jsonify({'success': False, 'message': 'Cannot assign an inactive or blacklisted staff member.'}), 400

    trek.assigned_staff_id = staff_id
    db.session.commit()
    clear_cache("treks:*")

    assigned_name = trek.assigned_staff.full_name if trek.assigned_staff else 'Unassigned'
    return jsonify({
        'success': True,
        'message': f'Trek "{trek.name}" assigned to staff: {assigned_name}.',
        'trek': trek.to_dict()
    }), 200


@admin_bp.route('/bookings', methods=['GET'])
@token_required
@role_required(['admin'])
def view_all_bookings(current_user):
    """
    Admin views all historical bookings across the system with filtering.
    """
    status = request.args.get('status', '').strip()
    query = Booking.query

    if status:
        query = query.filter_by(status=status)

    bookings = query.order_by(Booking.booking_date.desc()).all()
    return jsonify({
        'success': True,
        'count': len(bookings),
        'bookings': [b.to_dict() for b in bookings]
    }), 200


@admin_bp.route('/reports', methods=['GET'])
@token_required
@role_required(['admin'])
def view_reports(current_user):
    """
    Aggregated trekking statistics and analytics for Admin.
    """
    # 1. Popular treks (by number of bookings)
    treks = Trek.query.all()
    popular_treks = []
    for t in treks:
        booking_count = len([b for b in t.bookings if b.status != 'Cancelled'])
        slots_booked = sum(b.slots_booked for b in t.bookings if b.status != 'Cancelled')
        popular_treks.append({
            'trek_id': t.id,
            'name': t.name,
            'location': t.location,
            'difficulty': t.difficulty,
            'total_slots': t.total_slots,
            'slots_booked': slots_booked,
            'booking_count': booking_count
        })

    popular_treks.sort(key=lambda x: x['slots_booked'], reverse=True)

    # 2. Treks by status count
    status_summary = {
        'Open': Trek.query.filter_by(status='Open').count(),
        'Closed': Trek.query.filter_by(status='Closed').count(),
        'Completed': Trek.query.filter_by(status='Completed').count(),
        'Pending': Trek.query.filter_by(status='Pending').count()
    }

    # 3. Overall participant metrics
    total_participants = sum(
        b.slots_booked for b in Booking.query.filter(Booking.status != 'Cancelled').all()
    )

    return jsonify({
        'success': True,
        'status_summary': status_summary,
        'total_participants': total_participants,
        'popular_treks': popular_treks[:5]
    }), 200
