import os
from datetime import datetime, timezone
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
    # Only trekkers can book
    if current_user.role != 'user':
        return jsonify({'success': False, 'message': 'Only registered trekkers can book treks'}), 403

    data = request.get_json() or {}
    trek_id = data.get('trek_id')
    slots_booked = data.get('slots_booked', 1)
    payment_method = data.get('payment_method', 'Simulated UPI')

    if not trek_id:
        return jsonify({'success': False, 'message': 'trek_id is required'}), 400

    try:
        trek_id = int(trek_id)
        slots_booked = int(slots_booked)
        if slots_booked <= 0:
            return jsonify({'success': False, 'message': 'Slots must be at least 1'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid slots count or trek ID'}), 400

    trek = Trek.query.get(trek_id)
    if not trek:
        return jsonify({'success': False, 'message': 'Trek not found'}), 404

    if trek.status != 'Open':
        return jsonify({'success': False, 'message': f'Trek is currently {trek.status}'}), 400

    # Prevent duplicate active bookings
    existing = Booking.query.filter_by(user_id=current_user.id, trek_id=trek.id, status='Booked').first()
    if existing:
        return jsonify({'success': False, 'message': 'You already have an active booking for this trek'}), 409

    if trek.available_slots < slots_booked:
        return jsonify({'success': False, 'message': f'Only {trek.available_slots} slots remaining'}), 400

    # Deduct slots and save booking
    trek.available_slots -= slots_booked
    price = trek.price if trek.price is not None else 0.0
    total_price = round(slots_booked * price, 2)
    txn_id = f"TXN_{int(datetime.now(timezone.utc).timestamp())}_{current_user.id}{trek.id}"

    booking = Booking(
        user_id=current_user.id,
        trek_id=trek.id,
        slots_booked=slots_booked,
        total_price=total_price,
        booking_date=datetime.now(timezone.utc),
        status='Booked',
        payment_status='Paid',
        transaction_id=txn_id,
        payment_method=payment_method
    )
    db.session.add(booking)

    # In-app confirmation notification
    notif = Notification(
        user_id=current_user.id,
        title=f"Booking Confirmed: {trek.name}",
        message=f"Booked {slots_booked} slot(s) for ₹{total_price:,.2f}. Txn: {txn_id}.",
        notification_type='booking',
        is_read=False
    )
    db.session.add(notif)
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': f'Booked {slots_booked} slot(s) successfully',
        'booking': booking.to_dict(),
        'transaction_id': txn_id
    }), 201


@booking_bp.route('/bookings/my-bookings', methods=['GET'])
@token_required
def get_my_bookings(current_user):
    # Get all bookings for the logged-in user
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
    return jsonify({
        'success': True,
        'count': len(bookings),
        'bookings': [b.to_dict() for b in bookings]
    }), 200


@booking_bp.route('/bookings/<int:booking_id>', methods=['GET'])
@token_required
def get_booking(current_user, booking_id):
    # Get details of one booking
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found'}), 404

    # Check permission
    is_owner = (booking.user_id == current_user.id)
    is_admin = (current_user.role == 'admin')
    is_staff = (booking.trek and booking.trek.assigned_staff_id == current_user.id)
    if not (is_owner or is_admin or is_staff):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    return jsonify({'success': True, 'booking': booking.to_dict()}), 200


@booking_bp.route('/bookings/<int:booking_id>/cancel', methods=['PUT'])
@token_required
def cancel_booking(current_user, booking_id):
    # Cancel booking and return slots
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({'success': False, 'message': 'Booking not found'}), 404

    if current_user.role != 'admin' and booking.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'You can only cancel your own bookings'}), 403

    if booking.status == 'Cancelled':
        return jsonify({'success': False, 'message': 'Booking is already cancelled'}), 400

    if booking.status == 'Completed':
        return jsonify({'success': False, 'message': 'Completed bookings cannot be cancelled'}), 400

    # Restore slots to trek
    trek = booking.trek
    trek_name = trek.name if trek else "Trek"
    if trek:
        trek.available_slots = min(trek.total_slots, trek.available_slots + booking.slots_booked)
    booking.status = 'Cancelled'

    # Send cancellation notification
    notif = Notification(
        user_id=booking.user_id,
        title=f"Booking Cancelled: #{booking.id}",
        message=f"Booking for {trek_name} was cancelled. {booking.slots_booked} slots returned.",
        notification_type='cancellation',
        is_read=False
    )
    db.session.add(notif)
    db.session.commit()
    clear_cache("treks:*")

    return jsonify({
        'success': True,
        'message': f'Booking #{booking.id} cancelled successfully',
        'booking': booking.to_dict()
    }), 200


@booking_bp.route('/bookings/export-csv', methods=['POST'])
@token_required
def trigger_export_csv(current_user):
    # Trigger CSV export (async via Celery or sync fallback)
    from backend.cache import get_redis_client
    from backend.tasks import export_booking_history_csv

    if get_redis_client():
        try:
            task = export_booking_history_csv.apply_async(args=[current_user.id], retry=False)
            return jsonify({
                'success': True,
                'mode': 'async (Celery)',
                'task_id': task.id,
                'message': 'Export started'
            }), 202
        except Exception:
            pass

    # Direct fallback if Celery/Redis is not running
    result = export_booking_history_csv(current_user.id)
    return jsonify({
        'success': True,
        'mode': 'sync-fallback',
        'message': 'Booking history exported successfully',
        'export': result
    }), 200


@booking_bp.route('/bookings/export/<filename>', methods=['GET'])
@token_required
def download_export_file(current_user, filename):
    # Download exported CSV file
    if current_user.role != 'admin':
        prefix = f"booking_history_user_{current_user.id}_"
        if not filename.startswith(prefix):
            return jsonify({'success': False, 'message': 'Permission denied'}), 403

    path = os.path.join(EXPORTS_DIR, filename)
    if not os.path.exists(path):
        return jsonify({'success': False, 'message': 'File not found'}), 404

    return send_from_directory(EXPORTS_DIR, filename, as_attachment=True, mimetype='text/csv')


@booking_bp.route('/notifications', methods=['GET'])
@token_required
def get_notifications(current_user):
    # Get recent notifications and unread count
    notifs = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).limit(20).all()
    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({
        'success': True,
        'unread_count': unread,
        'notifications': [n.to_dict() for n in notifs]
    }), 200


@booking_bp.route('/notifications/<int:notif_id>/read', methods=['PUT'])
@token_required
def mark_notification_read(current_user, notif_id):
    # Mark a notification as read
    notif = Notification.query.get(notif_id)
    if not notif or notif.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Notification not found'}), 404

    notif.is_read = True
    db.session.commit()
    return jsonify({'success': True, 'message': 'Marked as read'}), 200


@booking_bp.route('/notifications/read-all', methods=['PUT'])
@token_required
def mark_all_notifications_read(current_user):
    # Mark all notifications as read
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True, 'message': 'All notifications marked as read'}), 200
