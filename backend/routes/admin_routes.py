import os
from flask import Blueprint, request, jsonify, send_from_directory
from backend.models import db, User, StaffProfile, Trek, Booking
from backend.routes.auth_routes import token_required, role_required
from backend.cache import clear_cache

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')


@admin_bp.route('/dashboard', methods=['GET'])
@token_required
@role_required(['admin'])
def admin_dashboard(_current_user):
    # Summary metrics for the Admin Dashboard
    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_bookings = Booking.query.count()
    active_bookings = Booking.query.filter_by(status='Booked').count()

    all_valid_bookings = Booking.query.filter(Booking.status != 'Cancelled').all()
    total_revenue = sum(b.total_price for b in all_valid_bookings)

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
def list_users(_current_user):
    # List and search users with optional filters
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
    # Activate or deactivate a user
    if current_user.id == user_id:
        return jsonify({'success': False, 'message': 'Cannot deactivate your own account'}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404

    data = request.get_json() or {}
    if 'is_active' in data:
        user.is_active = bool(data['is_active'])
    else:
        user.is_active = not user.is_active

    db.session.commit()
    status_str = "activated" if user.is_active else "deactivated"
    return jsonify({
        'success': True,
        'message': f'User {user.username} {status_str}',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/staff', methods=['POST'])
@token_required
@role_required(['admin'])
def create_staff(_current_user):
    # Admin provisions a new staff member
    data = request.get_json() or {}

    username = data.get('username', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    exp_years = data.get('experience_years', 0)
    bio = data.get('bio', '').strip()
    emergency_contact = data.get('emergency_contact', '').strip()

    if not username or not email or not password or not full_name:
        return jsonify({'success': False, 'message': 'All required fields must be filled'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Username already taken'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Email already registered'}), 409

    try:
        exp_years_num = int(exp_years) if exp_years else 0
    except (ValueError, TypeError):
        exp_years_num = 0

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
    db.session.flush()

    profile = StaffProfile(
        user_id=staff_user.id,
        experience_years=exp_years_num,
        bio=bio,
        emergency_contact=emergency_contact,
        status='Active'
    )
    db.session.add(profile)
    db.session.commit()

    resp = staff_user.to_dict()
    resp['profile'] = profile.to_dict()

    return jsonify({
        'success': True,
        'message': f'Staff {full_name} created successfully',
        'staff': resp
    }), 201


@admin_bp.route('/staff', methods=['GET'])
@token_required
@role_required(['admin'])
def list_staff(_current_user):
    # List all staff and their assigned treks
    staff_users = User.query.filter_by(role='staff').all()
    results = []

    for s in staff_users:
        item = s.to_dict()
        item['profile'] = s.staff_profile.to_dict() if s.staff_profile else None
        item['assigned_treks_count'] = len(s.assigned_treks)
        results.append(item)

    return jsonify({
        'success': True,
        'count': len(results),
        'staff': results
    }), 200


@admin_bp.route('/treks/<int:trek_id>/assign-staff', methods=['PUT'])
@token_required
@role_required(['admin'])
def assign_staff_to_trek(_current_user, trek_id):
    # Assign a staff member to a trek
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found'}), 404

    data = request.get_json() or {}
    staff_id = data.get('staff_id')

    if staff_id:
        try:
            staff_id = int(staff_id)
            staff_user = User.query.filter_by(id=staff_id, role='staff').first()
            if not staff_user or not staff_user.is_active:
                return jsonify({'success': False, 'message': 'Staff member not found or inactive'}), 400
        except (ValueError, TypeError):
            staff_id = None
    else:
        staff_id = None

    trek.assigned_staff_id = staff_id
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': f'Trek {trek.name} staff assignment updated',
        'trek': trek.to_dict()
    }), 200


@admin_bp.route('/bookings', methods=['GET'])
@token_required
@role_required(['admin'])
def view_all_bookings(_current_user):
    # View all bookings in the system
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
def view_reports(_current_user):
    # View high level stats and popular treks
    treks = Trek.query.all()
    popular_treks = []

    for t in treks:
        valid_bookings = [b for b in t.bookings if b.status != 'Cancelled']
        booked_slots = sum(b.slots_booked for b in valid_bookings)
        popular_treks.append({
            'trek_id': t.id,
            'name': t.name,
            'location': t.location,
            'difficulty': t.difficulty,
            'total_slots': t.total_slots,
            'slots_booked': booked_slots,
            'booking_count': len(valid_bookings)
        })

    popular_treks.sort(key=lambda x: x['slots_booked'], reverse=True)

    status_summary = {
        'Open': Trek.query.filter_by(status='Open').count(),
        'Closed': Trek.query.filter_by(status='Closed').count(),
        'Completed': Trek.query.filter_by(status='Completed').count(),
        'Pending': Trek.query.filter_by(status='Pending').count()
    }

    all_valid = Booking.query.filter(Booking.status != 'Cancelled').all()
    total_participants = sum(b.slots_booked for b in all_valid)

    return jsonify({
        'success': True,
        'status_summary': status_summary,
        'total_participants': total_participants,
        'popular_treks': popular_treks[:5]
    }), 200


@admin_bp.route('/trigger-monthly-report', methods=['POST'])
@token_required
@role_required(['admin'])
def trigger_monthly_report(_current_user):
    # Trigger monthly report generation
    from backend.cache import get_redis_client
    from backend.tasks import generate_monthly_activity_report

    if get_redis_client():
        try:
            task = generate_monthly_activity_report.apply_async(retry=False)
            return jsonify({
                'success': True,
                'mode': 'async',
                'task_id': task.id,
                'message': 'Monthly report job started'
            }), 202
        except Exception:
            pass

    result = generate_monthly_activity_report()
    return jsonify({
        'success': True,
        'mode': 'sync',
        'message': 'Monthly report generated',
        'report': result
    }), 200


@admin_bp.route('/trigger-daily-reminders', methods=['POST'])
@token_required
@role_required(['admin'])
def trigger_daily_reminders(_current_user):
    # Trigger daily reminders job
    from backend.cache import get_redis_client
    from backend.tasks import send_daily_reminders

    if get_redis_client():
        try:
            task = send_daily_reminders.apply_async(retry=False)
            return jsonify({
                'success': True,
                'mode': 'async',
                'task_id': task.id,
                'message': 'Daily reminders job dispatched'
            }), 202
        except Exception:
            pass

    result = send_daily_reminders()
    return jsonify({
        'success': True,
        'mode': 'sync',
        'message': 'Daily reminders executed',
        'summary': result
    }), 200


@admin_bp.route('/reports/monthly', methods=['GET'])
@token_required
@role_required(['admin'])
def list_monthly_reports(_current_user):
    # List generated monthly reports
    os.makedirs(REPORTS_DIR, exist_ok=True)
    files = [f for f in os.listdir(REPORTS_DIR) if f.endswith('.html')]
    return jsonify({'success': True, 'reports': files}), 200


@admin_bp.route('/reports/monthly/<filename>', methods=['GET'])
@token_required
@role_required(['admin'])
def view_monthly_report_file(_current_user, filename):
    # View a generated monthly report HTML file
    if not os.path.exists(os.path.join(REPORTS_DIR, filename)):
        return jsonify({'success': False, 'message': 'Report not found'}), 404
    return send_from_directory(REPORTS_DIR, filename)
