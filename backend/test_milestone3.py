"""
Milestone 3 Automated Verification Script for Trekking Management Application.
Tests:
1. Celery application & Celery Beat periodic schedules
2. User-triggered Async CSV Export task & CSV schema validation
3. CSV download endpoint with role/ownership security checks
4. Daily Reminders background job execution & notification logging
5. Monthly Activity HTML Report generation & statistics verification
6. Admin trigger endpoints for batch jobs
"""

import sys
import os
import csv
from datetime import date, timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app
from backend.models import db, User, Trek, Booking
from backend.celery_app import celery
from backend.tasks import (
    export_booking_history_csv,
    send_daily_reminders,
    generate_monthly_activity_report,
    EXPORTS_DIR,
    REPORTS_DIR,
    NOTIFICATIONS_LOG
)


def run_tests():
    app = create_app()
    client = app.test_client()

    print("\n" + "="*65)
    print("🧪 RUNNING MILESTONE 3 (CELERY & BATCH JOBS) VERIFICATION TESTS")
    print("="*65)

    # 1. Verify Celery App & Beat Schedule Configuration
    assert celery is not None, "❌ Celery instance not created!"
    schedule = celery.conf.beat_schedule
    assert 'daily-reminders-job' in schedule, "❌ 'daily-reminders-job' missing in beat_schedule!"
    assert 'monthly-activity-report-job' in schedule, "❌ 'monthly-activity-report-job' missing in beat_schedule!"
    print("✅ Test 1 Passed: Celery app initialized with Beat periodic schedules.")

    # 2. Setup Test Data (User & Booking)
    with app.app_context():
        # Ensure test trekker exists
        user = User.query.filter_by(username='trekker_m3_test').first()
        if not user:
            user = User(
                username='trekker_m3_test',
                email='trekker_m3@test.com',
                full_name='Aarav Kapoor',
                role='user',
                phone='9811223344',
                is_active=True
            )
            user.set_password('Password123')
            db.session.add(user)
            db.session.commit()

        # Ensure an upcoming trek exists starting in 2 days
        start_date = date.today() + timedelta(days=2)
        end_date = date.today() + timedelta(days=7)
        trek = Trek.query.filter_by(name='Valley of Flowers Expedition').first()
        if not trek:
            trek = Trek(
                name='Valley of Flowers Expedition',
                location='Uttarakhand',
                difficulty='Moderate',
                duration_days=5,
                total_slots=15,
                available_slots=12,
                price=8500.0,
                status='Open',
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(trek)
            db.session.commit()

        # Ensure an active booking exists
        booking = Booking.query.filter_by(user_id=user.id, trek_id=trek.id).first()
        if not booking:
            booking = Booking(
                user_id=user.id,
                trek_id=trek.id,
                slots_booked=2,
                total_price=17000.0,
                status='Booked',
                payment_status='Paid'
            )
            db.session.add(booking)
            db.session.commit()

        user_id = user.id
        trek_id = trek.id

    # 3. Test Job C: Export Booking History as CSV
    result = export_booking_history_csv(user_id)
    assert result['success'] is True, f"❌ CSV Export task failed: {result}"
    filename = result['filename']
    filepath = os.path.join(EXPORTS_DIR, filename)
    assert os.path.exists(filepath), f"❌ Generated CSV file not found on disk at {filepath}"

    # Verify CSV content and mandatory attributes
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        expected_fields = ['User ID', 'Trek Name', 'Location', 'Booking Status']
        for field in expected_fields:
            assert any(field in col for col in header), f"❌ Mandatory field '{field}' missing in CSV header: {header}"

        row = next(reader, None)
        assert row is not None, "❌ Exported CSV contains no data rows!"
        print(f"✅ Test 2 Passed: Export CSV generated successfully ({result['records_exported']} records).")

    # 4. Authenticate User & Test CSV Export API & Download Endpoints
    login_res = client.post('/api/auth/login', json={'username': 'trekker_m3_test', 'password': 'Password123'})
    token = login_res.get_json()['token']
    user_headers = {'Authorization': f'Bearer {token}'}

    # Trigger via API
    res = client.post('/api/bookings/export-csv', headers=user_headers)
    assert res.status_code in [200, 202], f"❌ Export CSV API returned {res.status_code}"
    print("✅ Test 3 Passed: User-triggered async CSV export API functional.")

    # Download file via API
    res = client.get(f'/api/bookings/export/{filename}', headers=user_headers)
    assert res.status_code == 200, f"❌ Download failed: {res.status_code}"
    assert 'text/csv' in res.content_type, "❌ Expected text/csv response!"
    print("✅ Test 4 Passed: CSV file download endpoint verified.")

    # Security check: another user cannot download this user's CSV
    other_user_res = client.post('/api/auth/login', json={'username': 'trekker_rahul', 'password': 'Password123'})
    if other_user_res.status_code == 200:
        other_token = other_user_res.get_json()['token']
        res = client.get(f'/api/bookings/export/{filename}', headers={'Authorization': f'Bearer {other_token}'})
        assert res.status_code == 403, f"❌ Unauthorized user was allowed to download CSV: {res.status_code}"
        print("✅ Test 5 Passed: Unauthorized user download blocked with 403 Forbidden.")

    # 5. Test Job A: Scheduled Daily Reminders
    reminder_result = send_daily_reminders()
    assert reminder_result['success'] is True, f"❌ Daily reminders failed: {reminder_result}"
    assert reminder_result['reminders_sent'] >= 1, "❌ Expected at least 1 upcoming trek reminder!"
    assert os.path.exists(NOTIFICATIONS_LOG), "❌ Notifications log file not found!"
    with open(NOTIFICATIONS_LOG, 'r', encoding='utf-8') as f:
        log_content = f.read()
        assert 'Reminder to Aarav Kapoor' in log_content or 'Valley of Flowers Expedition' in log_content
    print(f"✅ Test 6 Passed: Daily reminders dispatched ({reminder_result['reminders_sent']} sent, logged to notifications.log).")

    # 6. Test Job B: Scheduled Monthly Activity Report
    report_result = generate_monthly_activity_report()
    assert report_result['success'] is True, f"❌ Monthly report failed: {report_result}"
    report_name = report_result['report_name']
    report_file_path = os.path.join(REPORTS_DIR, report_name)
    assert os.path.exists(report_file_path), f"❌ Monthly report HTML file missing at {report_file_path}"

    with open(report_file_path, 'r', encoding='utf-8') as f:
        html = f.read()
        assert 'Monthly Trekking Activity Report' in html
        assert 'Total Treks' in html
        assert 'Participants' in html
    print(f"✅ Test 7 Passed: Monthly HTML Activity Report generated successfully ({report_name}).")

    # 7. Admin Batch Job Endpoints
    admin_login = client.post('/api/auth/login', json={'email': 'admin@trekking.com', 'password': 'Admin@123'})
    admin_token = admin_login.get_json()['token']
    admin_headers = {'Authorization': f'Bearer {admin_token}'}

    # Admin trigger monthly report
    res = client.post('/api/admin/trigger-monthly-report', headers=admin_headers)
    assert res.status_code in [200, 202]
    print("✅ Test 8 Passed: Admin trigger monthly report endpoint functional.")

    # Admin list reports
    res = client.get('/api/admin/reports/monthly', headers=admin_headers)
    assert res.status_code == 200
    assert report_name in res.get_json()['reports']
    print("✅ Test 9 Passed: Admin list monthly reports endpoint functional.")

    # Admin view/download report file
    res = client.get(f'/api/admin/reports/monthly/{report_name}', headers=admin_headers)
    assert res.status_code == 200
    assert 'text/html' in res.content_type
    print("✅ Test 10 Passed: Admin view monthly HTML report endpoint functional.")

    print("\n" + "="*65)
    print("🎉 ALL 10 MILESTONE 3 TESTS PASSED PERFECTLY!")
    print("="*65 + "\n")


if __name__ == '__main__':
    run_tests()
