"""
Booking Routes for Trekking Management Application.
Handles slot reservation, overbooking prevention, duplicate booking checks, cancellation,
payment simulation, in-app notifications, and User Triggered Async CSV Export.
"""

import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_from_directory
from backend.models import db, Booking, Trek, Notification
from backend.routes.auth_routes import token_required
from backend.cache import clear_cache

booking_bp = Blueprint('bookings', __name__, url_prefix='/api')

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')


@booking_bp.route('/bookings', methods=['POST'])
@token_required
def create_booking(current_user):
    """
    Trekker books a trek with slot validation, simulated payment processing,
    and automatic in-app confirmation notification.
    """
    if current_user.role != 'user':
        return jsonify({
            'success': False,
            'message': 'Only registered trekkers can book treks.'
        }), 403

    data = request.get_json() or {}
    trek_id = data.get('trek_id')
    slots_booked = data.get('slots_booked', 1)
    payment_method = data.get('payment_method', 'Simulated UPI')

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

    # Basic payment simulation: Generate unique transaction ID
    timestamp_num = int(datetime.utcnow().timestamp())
    transaction_id = f"TXN_{timestamp_num}_{current_user.id}{trek.id}"

    new_booking = Booking(
        user_id=current_user.id,
        trek_id=trek.id,
        slots_booked=slots_booked,
        total_price=total_price,
        booking_date=datetime.utcnow(),
        status='Booked',
        payment_status='Paid',
        transaction_id=transaction_id,
        payment_method=payment_method
    )

    db.session.add(new_booking)

    # Generate in-app booking confirmation notification
    confirmation_notif = Notification(
        user_id=current_user.id,
        title=f"Booking Confirmed: {trek.name}",
        message=f"Your booking for {slots_booked} slot(s) is confirmed. Total paid: ₹{total_price:,.2f} via {payment_method}. Ref: {transaction_id}.",
        notification_type='booking',
        is_read=False
    )
    db.session.add(confirmation_notif)
    db.session.commit()

    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': f'Successfully booked {slots_booked} slot(s) for "{trek.name}". Payment simulated ({transaction_id}).',
        'booking': new_booking.to_dict(),
        'transaction_id': transaction_id
    }), 201


@booking_bp.route('/bookings/my-bookings', methods=['GET'])
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


@booking_bp.route('/bookings/<int:booking_id>', methods=['GET'])
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


@booking_bp.route('/bookings/<int:booking_id>/cancel', methods=['PUT'])
@token_required
def cancel_booking(current_user, booking_id):
    """
    Cancel an active booking, restore slots to the trek, and dispatch a cancellation alert.
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

    # In-app cancellation notification
    cancel_notif = Notification(
        user_id=booking.user_id,
        title=f"Booking Cancelled: #{booking.id}",
        message=f"Booking for {trek.name} ({booking.slots_booked} slots) was cancelled. {booking.slots_booked} slot(s) returned.",
        notification_type='cancellation',
        is_read=False
    )
    db.session.add(cancel_notif)
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': f'Booking #{booking.id} for "{trek.name}" was successfully cancelled. {booking.slots_booked} slot(s) returned.',
        'booking': booking.to_dict()
    }), 200


@booking_bp.route('/bookings/export-csv', methods=['POST'])
@token_required
def trigger_export_csv(current_user):
    """
    User Triggered Async Job:
    Triggers CSV export of the user's trekking and booking history.
    """
    from backend.cache import get_redis_client
    from backend.tasks import export_booking_history_csv

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

    result = export_booking_history_csv(current_user.id)
    return jsonify({
        'success': True,
        'mode': 'sync-fallback',
        'message': 'Booking history exported successfully.',
        'export': result
    }), 200


@booking_bp.route('/bookings/export/<filename>', methods=['GET'])
@token_required
def download_export_file(current_user, filename):
    """
    Download a previously exported booking history CSV.
    """
    if current_user.role != 'admin':
        expected_prefix = f"booking_history_user_{current_user.id}_"
        if not filename.startswith(expected_prefix):
            return jsonify({'success': False, 'message': 'Access forbidden: unauthorized export file.'}), 403

    file_path = os.path.join(EXPORTS_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'message': 'Export file not found.'}), 404

    return send_from_directory(EXPORTS_DIR, filename, as_attachment=True, mimetype='text/csv')


# ==========================================
# IN-APP NOTIFICATIONS ENDPOINTS
# ==========================================

@booking_bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    """
    Get in-app notifications for the authenticated user.
    """
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(20).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return jsonify({
        'success': True,
        'unread_count': unread_count,
        'notifications': [n.to_dict() for n in notifications]
    }), 200


@booking_bp.route('/notifications/<int:notif_id>/read', methods=['PUT'])
@token_required
def mark_notification_read(current_user, notif_id):
    """
    Mark a specific notification as read.
    """
    notif = Notification.query.get(notif_id)
    if not notif or notif.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Notification not found.'}), 404

    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True, 'message': 'Notification marked as read.'}), 200


@booking_bp.route('/notifications/read-all', methods=['PUT'])
@token_required
def mark_all_notifications_read(current_user):
    """
    Mark all unread notifications as read for current user.
    """
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True, 'message': 'All notifications marked as read.'}), 200
