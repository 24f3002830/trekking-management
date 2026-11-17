"""
Staff Routes for Trekking Management Application.
Handles assigned trek management, participant viewing, slot adjustments, and trek status updates.
Strictly ensures only assigned staff can manage their specific treks.
"""

from flask import Blueprint, request, jsonify
from backend.models import db, Trek, Booking
from backend.routes.auth_routes import token_required, role_required
from backend.cache import clear_cache

staff_bp = Blueprint('staff', __name__, url_prefix='/api/staff')


@staff_bp.route('/dashboard', methods=['GET'])
@token_required
@role_required(['staff'])
def staff_dashboard(current_user):
    """
    Staff dashboard: displays all treks assigned to the logged-in staff member,
    along with registered participant counts for each trek.
    """
    assigned_treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.start_date.asc()).all()

    treks_summary = []
    total_participants = 0

    for trek in assigned_treks:
        active_bookings = [b for b in trek.bookings if b.status != 'Cancelled']
        participant_count = sum(b.slots_booked for b in active_bookings)
        total_participants += participant_count

        t_dict = trek.to_dict()
        t_dict['total_registered_participants'] = participant_count
        t_dict['booking_count'] = len(active_bookings)
        treks_summary.append(t_dict)

    return jsonify({
        'success': True,
        'metrics': {
            'assigned_treks_count': len(assigned_treks),
            'total_participants': total_participants
        },
        'treks': treks_summary
    }), 200


@staff_bp.route('/treks/<int:trek_id>/participants', methods=['GET'])
@token_required
@role_required(['staff', 'admin'])
def get_trek_participants(current_user, trek_id):
    """
    View registered participants for a trek.
    Strictly ensures only the assigned staff member (or Admin) can view.
    """
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found.'}), 404

    # Authorization: only assigned staff or admin
    if current_user.role == 'staff' and trek.assigned_staff_id != current_user.id:
        return jsonify({
            'success': False,
            'message': 'Access forbidden: you are not assigned to manage this trek.'
        }), 403

    bookings = Booking.query.filter_by(trek_id=trek.id).filter(Booking.status != 'Cancelled').all()

    participants = []
    for b in bookings:
        participants.append({
            'booking_id': b.id,
            'user_id': b.user.id,
            'user_name': b.user.full_name,
            'user_email': b.user.email,
            'user_phone': b.user.phone,
            'slots_booked': b.slots_booked,
            'booking_date': b.booking_date.strftime('%Y-%m-%d %H:%M:%S'),
            'booking_status': b.status,
            'payment_status': b.payment_status,
            'emergency_contact_name': b.user.emergency_contact_name,
            'emergency_contact_phone': b.user.emergency_contact_phone,
            'blood_group': b.user.blood_group,
            'medical_notes': b.user.medical_notes,
            'check_in_status': b.check_in_status or 'Pending',
            'medical_cleared': b.medical_cleared if b.medical_cleared is not None else True
        })

    return jsonify({
        'success': True,
        'trek_id': trek.id,
        'trek_name': trek.name,
        'total_participants': sum(p['slots_booked'] for p in participants),
        'participants': participants
    }), 200


@staff_bp.route('/treks/<int:trek_id>/status', methods=['PUT'])
@token_required
@role_required(['staff', 'admin'])
def update_trek_status(current_user, trek_id):
    """
    Update trek status (e.g. 'Open', 'Closed', 'Started', 'Completed').
    Strictly verifies only assigned staff (or Admin) can perform the action.
    """
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found.'}), 404

    if current_user.role == 'staff' and trek.assigned_staff_id != current_user.id:
        return jsonify({
            'success': False,
            'message': 'Access forbidden: you are not assigned to manage this trek.'
        }), 403

    data = request.get_json() or {}
    new_status = data.get('status', '').strip()

    valid_statuses = ['Open', 'Closed', 'Started', 'Completed']
    if new_status not in valid_statuses:
        return jsonify({
            'success': False,
            'message': f'Invalid status. Allowed values: {valid_statuses}'
        }), 400

    trek.status = new_status
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': f'Trek status updated to "{new_status}".',
        'trek': trek.to_dict()
    }), 200


@staff_bp.route('/treks/<int:trek_id>/slots', methods=['PUT'])
@token_required
@role_required(['staff', 'admin'])
def update_trek_slots(current_user, trek_id):
    """
    Manage available slots for an assigned trek.
    """
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found.'}), 404

    if current_user.role == 'staff' and trek.assigned_staff_id != current_user.id:
        return jsonify({
            'success': False,
            'message': 'Access forbidden: you are not assigned to manage this trek.'
        }), 403

    data = request.get_json() or {}
    available_slots = data.get('available_slots')

    if available_slots is None:
        return jsonify({'success': False, 'message': 'available_slots is required.'}), 400

    try:
        available_slots = int(available_slots)
        if available_slots < 0 or available_slots > trek.total_slots:
            return jsonify({
                'success': False,
                'message': f'available_slots must be between 0 and {trek.total_slots}.'
            }), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'available_slots must be a valid integer.'}), 400

    trek.available_slots = available_slots
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': f'Available slots updated to {available_slots}.',
        'trek': trek.to_dict()
    }), 200


@staff_bp.route('/bookings/<int:booking_id>/check-in', methods=['PUT'])
@token_required
@role_required(['staff', 'admin'])
def update_participant_checkin(current_user, booking_id):
    """
    Staff / Admin updates check-in attendance and medical clearance for a participant booking.
    Strictly verifies only assigned staff (or Admin) can update.
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found.'}), 404

    if current_user.role == 'staff' and booking.trek.assigned_staff_id != current_user.id:
        return jsonify({
            'success': False,
            'message': 'Access forbidden: you are not assigned to manage this trek.'
        }), 403

    data = request.get_json() or {}
    check_in_status = data.get('check_in_status')
    medical_cleared = data.get('medical_cleared')

    if check_in_status:
        valid_checkins = ['Pending', 'Checked In', 'No Show']
        if check_in_status not in valid_checkins:
            return jsonify({
                'success': False,
                'message': f'Invalid check_in_status. Allowed values: {valid_checkins}'
            }), 400
        booking.check_in_status = check_in_status

    if medical_cleared is not None:
        booking.medical_cleared = bool(medical_cleared)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f"Participant {booking.user.full_name} status updated to '{booking.check_in_status}'.",
        'booking': booking.to_dict()
    }), 200
