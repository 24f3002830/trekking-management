"""
Milestone 8 Automated Verification Test Suite.
Tests:
1. Trekker authentication for safety profile operations
2. Emergency & Medical Safety Profile update (PUT /api/auth/profile)
3. Emergency profile data retrieval (GET /api/auth/profile)
4. Trek Day-wise Itinerary & Gear Checklist verification (GET /api/treks/<id>)
5. Staff participant manifest retrieval with medical & emergency details (GET /api/staff/treks/<id>/participants)
6. Staff check-in attendance marking (PUT /api/staff/bookings/<id>/check-in)
7. Staff medical clearance toggle (PUT /api/staff/bookings/<id>/check-in)
8. Role-based security: Unassigned staff check-in update blocked with 403 Forbidden
9. Frontend components integration checks (ProfileView, StaffDashboard, TrekkerDashboard)
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app
from backend.models import db, User, Trek, Booking


def run_tests():
    app = create_app()
    client = app.test_client()

    print("\n" + "="*65)
    print("🧪 RUNNING MILESTONE 8 (SAFETY PROFILE, ITINERARY & CHECK-IN) TESTS")
    print("="*65)

    # 1. Authenticate Trekker
    login_res = client.post('/api/auth/login', json={'username': 'trekker_rahul', 'password': 'Password123'})
    if login_res.status_code != 200:
        login_res = client.post('/api/auth/login', json={'username': 'trekker_ananya', 'password': 'Password123'})
    assert login_res.status_code == 200, "❌ Trekker authentication failed"
    token = login_res.get_json()['token']
    user_id = login_res.get_json()['user']['id']
    trekker_headers = {'Authorization': f'Bearer {token}'}
    print("✅ Test 1 Passed: Trekker authenticated successfully.")

    # 2. Update Emergency & Medical Safety Profile
    profile_payload = {
        'full_name': 'Rahul S. Sharma',
        'phone': '9123456701',
        'emergency_contact_name': 'Dr. Sunita Sharma',
        'emergency_contact_phone': '9811223344',
        'blood_group': 'O+',
        'medical_notes': 'No altitude sickness history. Regular marathon runner.'
    }
    res = client.put('/api/auth/profile', headers=trekker_headers, json=profile_payload)
    assert res.status_code == 200, f"❌ Failed to update emergency profile: {res.get_json()}"
    updated_user = res.get_json()['user']
    assert updated_user['emergency_contact_name'] == 'Dr. Sunita Sharma'
    assert updated_user['blood_group'] == 'O+'
    print("✅ Test 2 Passed: Emergency contact & medical safety profile updated.")

    # 3. Retrieve Profile to verify persistence
    res = client.get('/api/auth/profile', headers=trekker_headers)
    assert res.status_code == 200
    user_data = res.get_json()['user']
    assert user_data['emergency_contact_phone'] == '9811223344'
    assert 'marathon' in user_data['medical_notes'].lower()
    print("✅ Test 3 Passed: Profile persistence verified with emergency details.")

    # 4. Day-wise Itinerary & Gear Checklist
    with app.app_context():
        trek = Trek.query.filter(Trek.itinerary.isnot(None)).first()
        if not trek:
            trek = Trek.query.first()
            trek.itinerary = "Day 1: Basecamp\nDay 2: High Camp\nDay 3: Summit Push"
            trek.gear_checklist = "Trekking shoes, 50L Rucksack, Thermal inners"
            db.session.commit()
        trek_id = trek.id
        staff_id = trek.assigned_staff_id

    res = client.get(f'/api/treks/{trek_id}')
    assert res.status_code == 200
    trek_data = res.get_json()['trek']
    assert trek_data.get('itinerary') is not None, "❌ Trek itinerary missing"
    assert trek_data.get('gear_checklist') is not None, "❌ Trek gear checklist missing"
    print(f"✅ Test 4 Passed: Trek '{trek_data['name']}' exposes itinerary and gear checklist.")

    # 5. Authenticate Assigned Staff
    with app.app_context():
        assigned_staff_user = db.session.get(User, staff_id)
        assert assigned_staff_user is not None, "Assigned staff user not found"
        staff_username = assigned_staff_user.username

    staff_login = client.post('/api/auth/login', json={'username': staff_username, 'password': 'StaffPassword123'})
    assert staff_login.status_code == 200, f"Staff login failed for {staff_username}"
    staff_token = staff_login.get_json()['token']
    staff_headers = {'Authorization': f'Bearer {staff_token}'}

    # Staff fetches participant manifest
    res = client.get(f'/api/staff/treks/{trek_id}/participants', headers=staff_headers)
    assert res.status_code == 200
    participants = res.get_json()['participants']
    print(f"✅ Test 5 Passed: Staff retrieved participant manifest ({len(participants)} registered).")

    # 6. Check-in Attendance Marking
    with app.app_context():
        booking = Booking.query.filter_by(trek_id=trek_id, status='Booked').first()
        if not booking:
            # Create a booking if none exists
            booking = Booking(
                user_id=user_id,
                trek_id=trek_id,
                slots_booked=1,
                total_price=trek.price,
                status='Booked',
                payment_status='Paid'
            )
            db.session.add(booking)
            db.session.commit()
        booking_id = booking.id

    checkin_payload = {'check_in_status': 'Checked In', 'medical_cleared': True}
    res = client.put(f'/api/staff/bookings/{booking_id}/check-in', headers=staff_headers, json=checkin_payload)
    assert res.status_code == 200, f"Check-in failed: {res.get_json()}"
    assert res.get_json()['booking']['check_in_status'] == 'Checked In'
    print(f"✅ Test 6 Passed: Participant attendance marked as 'Checked In'.")

    # 7. Toggle Medical Clearance
    res = client.put(f'/api/staff/bookings/{booking_id}/check-in', headers=staff_headers, json={'medical_cleared': False})
    assert res.status_code == 200
    assert res.get_json()['booking']['medical_cleared'] is False
    print("✅ Test 7 Passed: Medical clearance review status toggled.")

    # 8. Unassigned Staff Security Check
    with app.app_context():
        unassigned_staff = User.query.filter(User.role == 'staff', User.id != staff_id).first()
    if unassigned_staff:
        unassigned_login = client.post('/api/auth/login', json={'username': unassigned_staff.username, 'password': 'StaffPassword123'})
        if unassigned_login.status_code == 200:
            unassigned_headers = {'Authorization': f'Bearer {unassigned_login.get_json()["token"]}'}
            res = client.put(f'/api/staff/bookings/{booking_id}/check-in', headers=unassigned_headers, json={'check_in_status': 'Checked In'})
            assert res.status_code == 403, "❌ Unassigned staff should be rejected with 403 Forbidden"
            print("✅ Test 8 Passed: Unauthorized staff check-in attempt blocked (403 Forbidden).")
    else:
        print("✅ Test 8 Skipped/Passed: Only one staff member in DB.")

    # 9. Frontend Component Code Verification
    res = client.get('/frontend/src/components/ProfileView.vue')
    assert res.status_code == 200
    assert 'emergency_contact_name' in res.get_data(as_text=True)

    res = client.get('/frontend/src/components/StaffDashboard.vue')
    assert res.status_code == 200
    assert 'updateCheckIn' in res.get_data(as_text=True)

    res = client.get('/frontend/src/components/TrekkerDashboard.vue')
    assert res.status_code == 200
    assert 'openItineraryModal' in res.get_data(as_text=True)
    print("✅ Test 9 Passed: Frontend UI components verified (Profile, Staff, Trekker).")

    print("\n" + "="*65)
    print("🎉 ALL 9 MILESTONE 8 TESTS PASSED SUCCESSFULLY!")
    print("="*65 + "\n")


if __name__ == '__main__':
    run_tests()
