"""
Booking Routes for Trekking Management Application.
Handles slot reservation, overbooking prevention, duplicate booking checks, cancellation,
and User Triggered Async CSV Export of trekking history.
"""

import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory
from backend.models import db, Booking, Trek
from backend.routes.auth_routes import token_required
from backend.cache import clear_cache

booking_bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')


@booking_bp.route('', methods=['POST'])
@token_required
def create_booking(current_user):
    """
    Trekker books a trek with slot validation and concurrency/overbooking safeguards.
    """
    if current_user.role != 'user':
        return jsonify({
            'success': False,
            'message': 'Only registered trekkers can book treks.'
        }), 403

    data = request.get_json() or {}
    trek_id = data.get('trek_id')
    slots_booked = data.get('slots_booked', 1)

    if not trek_id:
        return jsonify({'success': False, 'message': 'trek_id is required.'}), 400

    try:
        slots_booked = int(slots_booked)
        if slots_booked <= 0:
            return jsonify({'success': False, 'message': 'You must book at least 1 slot.'}), 400
    except ValueError:
        return jsonify({'success': False, 'message': 'slots_booked must be a positive integer.'}), 400

    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found.'}), 404

    # 1. Check if Trek status is Open
    if trek.status != 'Open':
        return jsonify({
            'success': False,
            'message': f'Bookings are currently unavailable for this trek (status: {trek.status}).'
        }), 400

    # 2. Prevent duplicate bookings for same trek
    existing_booking = Booking.query.filter_by(
        user_id=current_user.id,
        trek_id=trek.id,
        status='Booked'
    ).first()

    if existing_booking:
        return jsonify({
            'success': False,
            'message': 'You already have an active booking for this trek. Duplicate bookings are not allowed.'
        }), 409

    # 3. Check slot availability (Prevent overbooking)
    if trek.available_slots < slots_booked:
        return jsonify({
            'success': False,
            'message': f'Not enough slots available. Only {trek.available_slots} slot(s) remaining.'
        }), 400

    # Deduct slots and compute price
    trek.available_slots -= slots_booked
    total_price = round(slots_booked * trek.price, 2)

    new_booking = Booking(
        user_id=current_user.id,
        trek_id=trek.id,
        slots_booked=slots_booked,
        total_price=total_price,
        booking_date=datetime.utcnow(),
        status='Booked',
        payment_status='Paid'
    )

    db.session.add(new_booking)
    db.session.commit()

    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': f'Successfully booked {slots_booked} slot(s) for "{trek.name}".',
        'booking': new_booking.to_dict()
    }), 201


@booking_bp.route('/my-bookings', methods=['GET'])
@token_required
def get_my_bookings(current_user):
    """
    Get all bookings made by the logged-in user (trekker history).
    """
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return jsonify({
        'success': True,
        'count': len(bookings),
        'bookings': [b.to_dict() for b in bookings]
    }), 200


@booking_bp.route('/<int:booking_id>', methods=['GET'])
@token_required
def get_booking(current_user, booking_id):
    """
    Get details of a specific booking.
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found.'}), 404

    is_owner = (booking.user_id == current_user.id)
    is_admin = (current_user.role == 'admin')
    is_assigned_staff = (booking.trek.assigned_staff_id == current_user.id)

    if not (is_owner or is_admin or is_assigned_staff):
        return jsonify({'success': False, 'message': 'Access forbidden.'}), 403

    return jsonify({
        'success': True,
        'booking': booking.to_dict()
    }), 200


@booking_bp.route('/<int:booking_id>/cancel', methods=['PUT'])
@token_required
def cancel_booking(current_user, booking_id):
    """
    Cancel an active booking and restore slots to the trek.
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found.'}), 404

    if current_user.role != 'admin' and booking.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'You can only cancel your own bookings.'}), 403

    if booking.status == 'Cancelled':
        return jsonify({'success': False, 'message': 'This booking has already been cancelled.'}), 400

    if booking.status == 'Completed':
        return jsonify({'success': False, 'message': 'Completed treks cannot be cancelled.'}), 400

    # Restore slots to trek
    trek = booking.trek
    trek.available_slots = min(trek.total_slots, trek.available_slots + booking.slots_booked)
    booking.status = 'Cancelled'

    db.session.commit()
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': f'Booking #{booking.id} for "{trek.name}" was successfully cancelled. {booking.slots_booked} slot(s) returned.',
        'booking': booking.to_dict()
    }), 200


@booking_bp.route('/export-csv', methods=['POST'])
@token_required
def trigger_export_csv(current_user):
    """
    User Triggered Async Job:
    Triggers CSV export of the user's trekking and booking history.
    Uses Celery background task with immediate execution fallback.
    """
    from backend.cache import get_redis_client
    from backend.tasks import export_booking_history_csv

    # If Redis is active, dispatch via Celery background worker
    if get_redis_client():
        try:
            task = export_booking_history_csv.apply_async(args=[current_user.id], retry=False)
            return jsonify({
                'success': True,
                'mode': 'async (Celery)',
                'task_id': task.id,
                'message': 'Export job initiated. You will receive an alert once generated.'
            }), 202
        except Exception as e:
            print(f"⚠️ Celery dispatch failed: {e}. Executing directly.")

    # Synchronous direct execution fallback
    result = export_booking_history_csv(current_user.id)
    return jsonify({
        'success': True,
        'mode': 'sync-fallback',
        'message': 'Booking history exported successfully.',
        'export': result
    }), 200


@booking_bp.route('/export/<filename>', methods=['GET'])
@token_required
def download_export_file(current_user, filename):
    """
    Download a previously exported booking history CSV.
    Ensures user can only download their own export file (or Admin can download any).
    """
    # Filename format: booking_history_user_<user_id>_<timestamp>.csv
    if current_user.role != 'admin':
        expected_prefix = f"booking_history_user_{current_user.id}_"
        if not filename.startswith(expected_prefix):
            return jsonify({'success': False, 'message': 'Access forbidden: unauthorized export file.'}), 403

    file_path = os.path.join(EXPORTS_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'Export file not found.'}), 404

    return send_from_directory(EXPORTS_DIR, filename, as_attachment=True, mimetype='text/csv')
