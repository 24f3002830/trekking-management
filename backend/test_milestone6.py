"""
Milestone 6 Automated Verification Test Suite.
Tests:
1. Basic payment simulation with transaction ID reference generation
2. In-app booking confirmation notifications
3. In-app cancellation notifications
4. Notification retrieval & read status management
5. Chart.js integration & Analytics rendering verification
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app
from backend.models import db, User, Trek, Booking, Notification


def run_tests():
    app = create_app()
    client = app.test_client()

    print("\n" + "="*65)
    print("🧪 RUNNING MILESTONE 6 (NOTIFICATIONS & PAYMENT SIMULATION) TESTS")
    print("="*65)

    # 1. Authenticate Trekker
    login_res = client.post('/api/auth/login', json={'username': 'trekker_ananya', 'password': 'Password123'})
    if login_res.status_code != 200:
        # Fallback to trekker_rahul
        login_res = client.post('/api/auth/login', json={'username': 'trekker_rahul', 'password': 'Password123'})
    assert login_res.status_code == 200
    token = login_res.get_json()['token']
    user_id = login_res.get_json()['user']['id']
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Test 1 Passed: Trekker authenticated.")

    # 2. Find an Open Trek to Book
    with app.app_context():
        # Find a trek not currently booked by this user
        booked_trek_ids = [b.trek_id for b in Booking.query.filter_by(user_id=user_id, status='Booked').all()]
        available_trek = Trek.query.filter(Trek.id.notin_(booked_trek_ids), Trek.status == 'Open', Trek.available_slots >= 2).first()
        assert available_trek is not None, "No open trek found for booking test"
        trek_id = available_trek.id
        trek_name = available_trek.name

    # 3. Book Trek with Simulated Payment
    booking_payload = {
        'trek_id': trek_id,
        'slots_booked': 2,
        'payment_method': 'Simulated UPI (GooglePay / PhonePe)'
    }
    res = client.post('/api/bookings', headers=headers, json=booking_payload)
    assert res.status_code == 201, f"Booking failed: {res.get_json()}"
    booking_res = res.get_json()
    assert 'transaction_id' in booking_res, "❌ Transaction ID missing in payment simulation!"
    assert booking_res['transaction_id'].startswith("TXN_"), "❌ Invalid transaction reference format!"
    booking_id = booking_res['booking']['id']
    print(f"✅ Test 2 Passed: Payment simulated successfully. Ref: {booking_res['transaction_id']}.")

    # 4. Check In-App Notification Generation
    res = client.get('/api/notifications', headers=headers)
    assert res.status_code == 200, f"Notification fetch failed: {res.get_json()}"
    notifs_data = res.get_json()
    assert notifs_data['unread_count'] >= 1, "❌ Unread notifications count should be at least 1!"
    notifs = notifs_data['notifications']
    assert any(n['notification_type'] == 'booking' for n in notifs), "❌ Booking confirmation notification missing!"
    first_notif = notifs[0]
    print(f"✅ Test 3 Passed: Booking confirmation notification generated ('{first_notif['title']}').")

    # 5. Mark Single Notification as Read
    res = client.put(f'/api/notifications/{first_notif["id"]}/read', headers=headers)
    assert res.status_code == 200
    print("✅ Test 4 Passed: Notification marked as read.")

    # 6. Mark All Notifications as Read
    res = client.put('/api/notifications/read-all', headers=headers)
    assert res.status_code == 200
    res = client.get('/api/notifications', headers=headers)
    assert res.get_json()['unread_count'] == 0, "❌ Unread count should be 0 after read-all!"
    print("✅ Test 5 Passed: Mark all notifications read functional.")

    # 7. Booking Cancellation & Cancellation Alert
    res = client.put(f'/api/bookings/{booking_id}/cancel', headers=headers)
    assert res.status_code == 200
    res = client.get('/api/notifications', headers=headers)
    notifs = res.get_json()['notifications']
    assert any(n['notification_type'] == 'cancellation' for n in notifs), "❌ Cancellation notification missing!"
    print("✅ Test 6 Passed: Cancellation notification dispatched successfully.")

    # 8. Chart.js & Component Analytics Verification
    res = client.get('/frontend/src/components/AdminDashboard.vue')
    assert res.status_code == 200
    vue_code = res.get_data(as_text=True)
    assert 'analyticsChart' in vue_code, "❌ analyticsChart canvas missing in AdminDashboard.vue!"
    assert 'renderChart' in vue_code, "❌ renderChart method missing in AdminDashboard.vue!"
    print("✅ Test 7 Passed: Chart.js interactive analytics integrated in Admin Dashboard.")

    print("\n" + "="*65)
    print("🎉 ALL MILESTONE 6 VERIFICATION TESTS PASSED PERFECTLY!")
    print("="*65 + "\n")


if __name__ == '__main__':
    run_tests()
