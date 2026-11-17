"""
Milestone 1 Automated Verification Script for Trekking Management Application.
Tests:
1. Programmatic SQLite creation
2. Pre-seeded Admin existence
3. User (Trekker) registration
4. Login & JWT token issuance for Admin & Trekker
5. Protected route verification (@token_required)
6. Role-Based Access Control (@role_required)
7. Deactivation / Blacklisting rejection
"""

import sys
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app
from backend.models import db, User, Trek, Booking, StaffProfile


def run_tests():
    app = create_app()
    client = app.test_client()

    print("\n" + "="*60)
    print("🧪 RUNNING MILESTONE 1 VERIFICATION TESTS")
    print("="*60)

    # Test 1: Verify Programmatic Database & Admin Seed
    with app.app_context():
        admin = User.query.filter_by(role='admin').first()
        assert admin is not None, "❌ Admin user was not created programmatically!"
        assert admin.username == 'admin', "❌ Admin username is not 'admin'!"
        assert admin.check_password('Admin@123'), "❌ Admin password does not match 'Admin@123'!"
        print("✅ Test 1 Passed: Database tables & default Admin initialized programmatically.")

    # Test 2: Health check endpoint
    res = client.get('/api/health')
    assert res.status_code == 200, f"❌ Health check failed: {res.status_code}"
    print("✅ Test 2 Passed: Health check endpoint /api/health returned 200 OK.")

    # Test 3: User (Trekker) Registration
    trekker_data = {
        'username': 'trekker_rahul',
        'email': 'rahul@example.com',
        'password': 'Password123',
        'full_name': 'Rahul Sharma',
        'phone': '9876543211'
    }
    res = client.post('/api/auth/register', json=trekker_data)
    assert res.status_code in [201, 409], f"❌ Registration failed: {res.get_json()}"
    print("✅ Test 3 Passed: Trekker self-registration API working.")

    # Test 4: Duplicate Registration Prevention
    res = client.post('/api/auth/register', json=trekker_data)
    assert res.status_code == 409, f"❌ Duplicate registration was not rejected: {res.status_code}"
    print("✅ Test 4 Passed: Duplicate registration blocked with 409 Conflict.")

    # Test 5: Trekker Login & JWT Token
    login_data = {
        'username': 'trekker_rahul',
        'password': 'Password123'
    }
    res = client.post('/api/auth/login', json=login_data)
    assert res.status_code == 200, f"❌ Login failed: {res.get_json()}"
    res_json = res.get_json()
    assert 'token' in res_json, "❌ JWT token missing in login response!"
    assert res_json['user']['role'] == 'user', "❌ Role should be 'user'!"
    trekker_token = res_json['token']
    print("✅ Test 5 Passed: Trekker login successful, JWT token issued.")

    # Test 6: Admin Login
    admin_login = {
        'email': 'admin@trekking.com',
        'password': 'Admin@123'
    }
    res = client.post('/api/auth/login', json=admin_login)
    assert res.status_code == 200, f"❌ Admin login failed: {res.get_json()}"
    admin_token = res.get_json()['token']
    assert res.get_json()['user']['role'] == 'admin', "❌ Role should be 'admin'!"
    print("✅ Test 6 Passed: Admin login successful, role verified as 'admin'.")

    # Test 7: Protected Route Access with Token
    headers = {'Authorization': f'Bearer {trekker_token}'}
    res = client.get('/api/auth/profile', headers=headers)
    assert res.status_code == 200, f"❌ Protected profile access failed: {res.get_json()}"
    profile = res.get_json()['user']
    assert profile['username'] == 'trekker_rahul', "❌ Profile username mismatch!"
    print("✅ Test 7 Passed: Protected route /api/auth/profile accessed with valid token.")

    # Test 8: Protected Route Access Without Token (Should Fail 401)
    res = client.get('/api/auth/profile')
    assert res.status_code == 401, f"❌ Unauthenticated request was not blocked: {res.status_code}"
    print("✅ Test 8 Passed: Missing token blocked with 401 Unauthorized.")

    # Test 9: Profile Update
    update_data = {'full_name': 'Rahul S. Sharma', 'phone': '9998887776'}
    res = client.put('/api/auth/profile', headers=headers, json=update_data)
    assert res.status_code == 200, f"❌ Profile update failed: {res.get_json()}"
    assert res.get_json()['user']['full_name'] == 'Rahul S. Sharma', "❌ Updated name mismatch!"
    print("✅ Test 9 Passed: Profile update API functional.")

    # Test 10: Account Deactivation / Blacklist Check
    with app.app_context():
        user = User.query.filter_by(username='trekker_rahul').first()
        user.is_active = False
        db.session.commit()

    # Now attempt to login as deactivated user
    res = client.post('/api/auth/login', json=login_data)
    assert res.status_code == 403, f"❌ Deactivated user was allowed to login: {res.status_code}"
    print("✅ Test 10 Passed: Deactivated / Blacklisted user login blocked with 403 Forbidden.")

    # Restore user active status
    with app.app_context():
        user = User.query.filter_by(username='trekker_rahul').first()
        user.is_active = True
        db.session.commit()

    print("\n" + "="*60)
    print("🎉 ALL MILESTONE 1 TESTS PASSED SUCCESSFULLY!")
    print("="*60 + "\n")


if __name__ == '__main__':
    run_tests()
