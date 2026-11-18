from flask import Blueprint, request, jsonify
from backend.models import db, Trek, Booking
from backend.routes.auth_routes import token_required, role_required
from backend.cache import clear_cache

staff_bp = Blueprint('staff', __name__, url_prefix='/api/staff')


@staff_bp.route('/dashboard', methods=['GET'])
@token_required
@role_required(['staff'])
def staff_dashboard(current_user):
    # Get treks assigned to this staff member
    treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.start_date.asc()).all()

    treks_data = []
    total_participants = 0

    for trek in treks:
        active_bookings = [b for b in trek.bookings if b.status != 'Cancelled']
        participant_count = sum(b.slots_booked for b in active_bookings)
        total_participants += participant_count

        item = trek.to_dict()
        item['total_registered_participants'] = participant_count
        item['booking_count'] = len(active_bookings)
        treks_data.append(item)

    return jsonify({
        'success': True,
        'metrics': {
            'assigned_treks_count': len(treks),
            'total_participants': total_participants
        },
        'treks': treks_data
    }), 200


@staff_bp.route('/treks/<int:trek_id>/participants', methods=['GET'])
@token_required
@role_required(['staff', 'admin'])
def get_trek_participants(current_user, trek_id):
    # View participants for an assigned trek
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found'}), 404

    # Staff can only view their own treks
    if current_user.role == 'staff' and trek.assigned_staff_id != current_user.id:
        return jsonify({'success': False, 'message': 'You are not assigned to this trek'}), 403

    bookings = Booking.query.filter_by(trek_id=trek.id).filter(Booking.status != 'Cancelled').all()

    participants = []
    for b in bookings:
        participants.append({
            'booking_id': b.id,
            'user_id': b.user.id if b.user else None,
            'user_name': b.user.full_name if b.user else 'Unknown',
            'user_email': b.user.email if b.user else 'N/A',
            'user_phone': b.user.phone if b.user else 'N/A',
            'slots_booked': b.slots_booked,
            'booking_date': b.booking_date.strftime('%Y-%m-%d %H:%M:%S') if b.booking_date else 'N/A',
            'booking_status': b.status,
            'payment_status': b.payment_status,
            'emergency_contact_name': b.user.emergency_contact_name if b.user else None,
            'emergency_contact_phone': b.user.emergency_contact_phone if b.user else None,
            'blood_group': b.user.blood_group if b.user else None,
            'medical_notes': b.user.medical_notes if b.user else None,
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
    # Update status: Open, Closed, Started, Completed
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found'}), 404

    if current_user.role == 'staff' and trek.assigned_staff_id != current_user.id:
        return jsonify({'success': False, 'message': 'You are not assigned to this trek'}), 403

    data = request.get_json() or {}
    new_status = data.get('status', '').strip()

    allowed = ['Open', 'Closed', 'Started', 'Completed']
    if new_status not in allowed:
        return jsonify({'success': False, 'message': f'Status must be one of: {allowed}'}), 400

    trek.status = new_status
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({'success': True, 'message': 'Status updated', 'trek': trek.to_dict()}), 200


@staff_bp.route('/treks/<int:trek_id>/slots', methods=['PUT'])
@token_required
@role_required(['staff', 'admin'])
def update_trek_slots(current_user, trek_id):
    # Adjust available slots
    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found'}), 404

    if current_user.role == 'staff' and trek.assigned_staff_id != current_user.id:
        return jsonify({'success': False, 'message': 'You are not assigned to this trek'}), 403

    data = request.get_json() or {}
    slots = data.get('available_slots')

    if slots is None:
        return jsonify({'success': False, 'message': 'available_slots is required'}), 400

    try:
        slots = int(slots)
        if slots < 0 or slots > trek.total_slots:
            return jsonify({'success': False, 'message': f'Slots must be between 0 and {trek.total_slots}'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid slots number'}), 400

    trek.available_slots = slots
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({'success': True, 'message': 'Slots updated', 'trek': trek.to_dict()}), 200


@staff_bp.route('/bookings/<int:booking_id>/check-in', methods=['PUT'])
@token_required
@role_required(['staff', 'admin'])
def update_participant_checkin(current_user, booking_id):
    # Update participant check-in attendance and medical status
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found'}), 404

    if current_user.role == 'staff' and booking.trek and booking.trek.assigned_staff_id != current_user.id:
        return jsonify({'success': False, 'message': 'You are not assigned to this trek'}), 403

    data = request.get_json() or {}
    check_in_status = data.get('check_in_status')
    medical_cleared = data.get('medical_cleared')

    if check_in_status:
        if check_in_status not in ['Pending', 'Checked In', 'No Show']:
            return jsonify({'success': False, 'message': 'Invalid check-in status'}), 400
        booking.check_in_status = check_in_status

    if medical_cleared is not None:
        booking.medical_cleared = bool(medical_cleared)

    db.session.commit()

    user_name = booking.user.full_name if booking.user else 'Participant'
    return jsonify({
        'success': True,
        'message': f"Status updated for {user_name}",
        'booking': booking.to_dict()
    }), 200
