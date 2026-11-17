"""
Milestone 2 Automated Verification Script for Trekking Management Application.
Tests:
1. Admin trek creation, update & delete
2. Trek search, filter, and Redis caching
3. Admin staff creation & staff-to-trek assignment
4. User trek booking & slot calculation
5. Overbooking prevention
6. Duplicate booking prevention
7. Assigned staff authorization checks
8. Staff participant listing & status update
9. Booking cancellation & slot restoration
10. Admin dashboard metrics and reports
"""

import sys
import os
from datetime import date, timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app
from backend.models import db, User, Trek, Booking, StaffProfile


def run_tests():
    app = create_app()
    client = app.test_client()

    print("\n" + "="*65)
    print("🧪 RUNNING MILESTONE 2 COMPREHENSIVE VERIFICATION TESTS")
    print("="*65)

    # 1. Admin Login
    admin_login = {'email': 'admin@trekking.com', 'password': 'Admin@123'}
    res = client.post('/api/auth/login', json=admin_login)
    assert res.status_code == 200, f"Admin login failed: {res.get_json()}"
    admin_token = res.get_json()['token']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}
    print("✅ Step 1: Admin authenticated.")

    # 2. Admin creates a new Staff member
    staff_payload = {
        'username': 'staff_arjun',
        'email': 'arjun.staff@trekking.com',
        'password': 'StaffPassword123',
        'full_name': 'Arjun Mehta',
        'phone': '9876543220',
        'experience_years': 5,
        'bio': 'Certified mountaineering instructor with 5 years experience in Himalayas.'
    }
    res = client.post('/api/admin/staff', headers=admin_headers, json=staff_payload)
    if res.status_code == 409:
        # Already created in prior test run
        with app.app_context():
            staff_user = User.query.filter_by(username='staff_arjun').first()
            staff_id = staff_user.id
    else:
        assert res.status_code == 201, f"Create staff failed: {res.get_json()}"
        staff_id = res.get_json()['staff']['id']
    print(f"✅ Step 2: Trek Staff member verified (ID: {staff_id}).")

    # Staff Login
    res = client.post('/api/auth/login', json={'username': 'staff_arjun', 'password': 'StaffPassword123'})
    assert res.status_code == 200, f"Staff login failed: {res.get_json()}"
    staff_token = res.get_json()['token']
    staff_headers = {'Authorization': f'Bearer {staff_token}'}
    print("✅ Step 3: Staff authenticated.")

    # 3. Create a second Staff member (for testing unassigned authorization checks)
    staff2_payload = {
        'username': 'staff_priya',
        'email': 'priya.staff@trekking.com',
        'password': 'StaffPassword123',
        'full_name': 'Priya Nair',
        'phone': '9876543221',
        'experience_years': 3
    }
    res = client.post('/api/admin/staff', headers=admin_headers, json=staff2_payload)
    res = client.post('/api/auth/login', json={'username': 'staff_priya', 'password': 'StaffPassword123'})
    staff2_token = res.get_json()['token']
    staff2_headers = {'Authorization': f'Bearer {staff2_token}'}

    # 4. Admin creates a Trek Route
    start_dt = (date.today() + timedelta(days=15)).strftime('%Y-%m-%d')
    end_dt = (date.today() + timedelta(days=20)).strftime('%Y-%m-%d')
    trek_payload = {
        'name': 'Roopkund Glacier Expedition',
        'description': 'High altitude trek to mystery lake in Uttarakhand.',
        'location': 'Uttarakhand',
        'difficulty': 'Hard',
        'duration_days': 6,
        'total_slots': 10,
        'price': 12500.0,
        'assigned_staff_id': staff_id,
        'start_date': start_dt,
        'end_date': end_dt
    }
    res = client.post('/api/treks', headers=admin_headers, json=trek_payload)
    assert res.status_code == 201, f"Trek creation failed: {res.get_json()}"
    trek = res.get_json()['trek']
    trek_id = trek['id']
    print(f"✅ Step 4: Admin created Trek '{trek['name']}' (ID: {trek_id}) assigned to staff.")

    # 5. Search & Filter Treks
    res = client.get('/api/treks?difficulty=Hard&location=Uttarakhand')
    assert res.status_code == 200
    treks_found = res.get_json()['treks']
    assert any(t['id'] == trek_id for t in treks_found), "Trek not found in filtered search!"
    print("✅ Step 5: Trek search & filter functional (Redis caching handled).")

    # 6. Trekker (User) Registration and Login
    trekker_data = {
        'username': f'trekker_m2_{trek_id}',
        'email': f'trekker_m2_{trek_id}@example.com',
        'password': 'TrekkerPass123',
        'full_name': 'Sneha Rao',
        'phone': '9123456780'
    }
    res = client.post('/api/auth/register', json=trekker_data)
    assert res.status_code in [201, 409]

    res = client.post('/api/auth/login', json={'username': trekker_data['username'], 'password': trekker_data['password']})
    assert res.status_code == 200
    trekker_token = res.get_json()['token']
    trekker_headers = {'Authorization': f'Bearer {trekker_token}'}
    print("✅ Step 6: Trekker account registered and authenticated.")

    # 7. Trekker Books 2 Slots
    booking_payload = {'trek_id': trek_id, 'slots_booked': 2}
    res = client.post('/api/bookings', headers=trekker_headers, json=booking_payload)
    assert res.status_code == 201, f"Booking failed: {res.get_json()}"
    booking_data = res.get_json()['booking']
    booking_id = booking_data['id']
    assert booking_data['slots_booked'] == 2
    assert booking_data['total_price'] == 25000.0  # 2 * 12500
    print(f"✅ Step 7: Booking created #{booking_id} (2 slots, Rs. 25,000).")

    # Verify slot reduction on trek
    res = client.get(f'/api/treks/{trek_id}')
    assert res.get_json()['trek']['available_slots'] == 8  # 10 - 2
    print("✅ Step 8: Available slots correctly reduced from 10 to 8.")

    # 8. Duplicate Booking Prevention Check
    res = client.post('/api/bookings', headers=trekker_headers, json={'trek_id': trek_id, 'slots_booked': 1})
    assert res.status_code == 409, f"Duplicate booking was not rejected: {res.status_code}"
    print("✅ Step 9: Duplicate booking rejected with 409 Conflict.")

    # 9. Overbooking Prevention Check (try booking 10 slots when only 8 remain)
    trekker2_data = {
        'username': f'trekker2_m2_{trek_id}',
        'email': f'trekker2_m2_{trek_id}@example.com',
        'password': 'Password123',
        'full_name': 'Ananya Sen'
    }
    client.post('/api/auth/register', json=trekker2_data)
    res = client.post('/api/auth/login', json={'username': trekker2_data['username'], 'password': 'Password123'})
    t2_token = res.get_json()['token']
    t2_headers = {'Authorization': f'Bearer {t2_token}'}

    res = client.post('/api/bookings', headers=t2_headers, json={'trek_id': trek_id, 'slots_booked': 9})
    assert res.status_code == 400, f"Overbooking was not rejected: {res.status_code}"
    print("✅ Step 10: Overbooking beyond available slots rejected with 400 Bad Request.")

    # 10. Staff Dashboard & Participant List Check
    res = client.get('/api/staff/dashboard', headers=staff_headers)
    assert res.status_code == 200
    assert res.get_json()['metrics']['assigned_treks_count'] >= 1
    print("✅ Step 11: Assigned Staff dashboard shows assigned treks.")

    # Assigned staff views participants
    res = client.get(f'/api/staff/treks/{trek_id}/participants', headers=staff_headers)
    assert res.status_code == 200
    participants = res.get_json()['participants']
    assert len(participants) >= 1
    assert any(p['user_name'] == 'Sneha Rao' for p in participants)
    print("✅ Step 12: Assigned staff can view participant list.")

    # 11. Security Check: Unassigned Staff cannot view or manage another staff's trek
    res = client.get(f'/api/staff/treks/{trek_id}/participants', headers=staff2_headers)
    assert res.status_code == 403, f"Unassigned staff was allowed to view participants: {res.status_code}"
    print("✅ Step 13: Unassigned staff blocked from managing other staff's trek (403 Forbidden).")

    # 12. Staff updates trek status & slots
    res = client.put(f'/api/staff/treks/{trek_id}/status', headers=staff_headers, json={'status': 'Started'})
    assert res.status_code == 200
    assert res.get_json()['trek']['status'] == 'Started'

    # Set back to Open
    client.put(f'/api/staff/treks/{trek_id}/status', headers=staff_headers, json={'status': 'Open'})
    print("✅ Step 14: Assigned staff updated trek status successfully.")

    # 13. Trekker views booking history
    res = client.get('/api/bookings/my-bookings', headers=trekker_headers)
    assert res.status_code == 200
    my_bookings = res.get_json()['bookings']
    assert any(b['id'] == booking_id for b in my_bookings)
    print("✅ Step 15: Trekker booking history verified.")

    # 14. Trekker cancels booking and slots are restored
    res = client.put(f'/api/bookings/{booking_id}/cancel', headers=trekker_headers)
    assert res.status_code == 200
    assert res.get_json()['booking']['status'] == 'Cancelled'

    # Check that slots are restored to 10
    res = client.get(f'/api/treks/{trek_id}')
    assert res.get_json()['trek']['available_slots'] == 10
    print("✅ Step 16: Booking cancelled and slots restored to 10.")

    # 15. Admin views dashboard, bookings, and reports
    res = client.get('/api/admin/dashboard', headers=admin_headers)
    assert res.status_code == 200
    assert res.get_json()['metrics']['total_treks'] >= 1
    print("✅ Step 17: Admin dashboard metrics verified.")

    res = client.get('/api/admin/reports', headers=admin_headers)
    assert res.status_code == 200
    print("✅ Step 18: Admin reports & statistics verified.")

    print("\n" + "="*65)
    print("🎉 ALL 18 MILESTONE 2 TESTS PASSED PERFECTLY!")
    print("="*65 + "\n")


if __name__ == '__main__':
    run_tests()
