"""
Celery Task Definitions for Trekking Management Application (TMA).
Implements background jobs:
1. Scheduled Daily Reminders: Reminds users about upcoming treks starting in 3 days.
2. Scheduled Monthly Report: Generates HTML activity report for the Admin.
3. User-Triggered CSV Export: Exports user's complete booking history.
"""

import os
import csv
from datetime import datetime, date, timedelta, timezone
from backend.celery_app import celery
from backend.models import db, User, Trek, Booking

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
NOTIFICATIONS_LOG = os.path.join(BASE_DIR, 'notifications.log')

os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def log_notification(message):
    #Log an outgoing notification or reminder to console and file.
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
    entry = f"[{timestamp}] {message}\n"
    with open(NOTIFICATIONS_LOG, 'a', encoding='utf-8') as file:
        file.write(entry)
    print(f"{message}")


@celery.task(name='backend.tasks.export_booking_history_csv')
def export_booking_history_csv(user_id):
    
    #Exports a user's complete trekking and booking history as a CSV file.
    from backend.app import app

    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': f'User {user_id} not found.'}

        bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_date.desc()).all()

        timestamp_str = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(EXPORTS_DIR, f"booking_history_user_{user_id}_{timestamp_str}.csv")
        filename = f"booking_history_user_{user_id}_{timestamp_str}.csv"

        # Write data to CSV file
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header row
            header = [
                'Booking ID',
                'User ID',
                'User Name',
                'Trek Name',
                'Location',
                'Difficulty',
                'Booking Status',
                'Booking Date',
                'Trek Start Date',
                'Trek End Date',
                'Slots Booked',
                'Total Price (INR)',
                'Payment Status'
            ]
            writer.writerow(header)

            # Write booking records
            for booking in bookings:
                trek = booking.trek

                trek_name = 'N/A'
                trek_location = 'N/A'
                trek_difficulty = 'N/A'
                trek_start_str = 'N/A'
                trek_end_str = 'N/A'

                if trek:
                    trek_name = trek.name
                    trek_location = trek.location
                    trek_difficulty = trek.difficulty
                    if trek.start_date:
                        trek_start_str = trek.start_date.strftime('%Y-%m-%d')
                    if trek.end_date:
                        trek_end_str = trek.end_date.strftime('%Y-%m-%d')

                booking_date_str = 'N/A'
                if booking.booking_date:
                    booking_date_str = booking.booking_date.strftime('%Y-%m-%d %H:%M:%S')

                row = [
                    booking.id,
                    user.id,
                    user.full_name,
                    trek_name,
                    trek_location,
                    trek_difficulty,
                    booking.status,
                    booking_date_str,
                    trek_start_str,
                    trek_end_str,
                    booking.slots_booked,
                    booking.total_price,
                    booking.payment_status
                ]
                writer.writerow(row)

        log_notification(
            f"Export Complete: Booking history for User '{user.username}' (ID: {user_id}) exported to {filename}."
        )

        return {
            'success': True,
            'user_id': user_id,
            'filename': filename,
            'records_exported': len(bookings),
            'download_url': f'/api/bookings/export/{filename}'
        }


@celery.task(name='backend.tasks.send_daily_reminders')
def send_daily_reminders():
    
    #Sends preparation reminders to users whose treks depart in the next 3 days.
    
    from backend.app import app

    with app.app_context():
        today = date.today()
        upcoming_window = today + timedelta(days=3)

        # Query treks departing in the 3-day window
        upcoming_treks = Trek.query.filter(
            Trek.start_date >= today,
            Trek.start_date <= upcoming_window,
            Trek.status.in_(['Open', 'Approved', 'Started'])
        ).all()

        reminders_sent = 0
        details = []

        for trek in upcoming_treks:
            active_bookings = Booking.query.filter_by(trek_id=trek.id, status='Booked').all()

            for booking in active_bookings:
                recipient = booking.user
                days_left = (trek.start_date - today).days

                start_date_str = trek.start_date.strftime('%Y-%m-%d')
                reminder_msg = (
                    f"Reminder to {recipient.full_name} ({recipient.email}): "
                    f"Your trek '{trek.name}' at {trek.location} starts in {days_left} day(s) on {start_date_str}. "
                    f"Slots booked: {booking.slots_booked}. Please bring appropriate trekking gear!"
                )

                log_notification(reminder_msg)
                details.append({
                    'user_id': recipient.id,
                    'user_email': recipient.email,
                    'trek_name': trek.name,
                    'start_date': start_date_str
                })
                reminders_sent += 1

        summary = f"Daily Reminders Job executed: {reminders_sent} reminder(s) dispatched."
        log_notification(summary)

        return {
            'success': True,
            'reminders_sent': reminders_sent,
            'details': details
        }


@celery.task(name='backend.tasks.generate_monthly_activity_report')
def generate_monthly_activity_report():
    
    #Generates a monthly activity report with metrics and HTML summary for Admin.
    
    from backend.app import app

    with app.app_context():
        now = datetime.now(timezone.utc)
        month_name = now.strftime('%B %Y')
        month_tag = now.strftime('%Y_%m')

        total_treks = Trek.query.count()
        all_bookings = Booking.query.filter(Booking.status != 'Cancelled').all()

        total_participants = 0
        total_revenue = 0.0
        for b in all_bookings:
            total_participants += b.slots_booked
            total_revenue += b.total_price

        # Sort treks by slots booked
        treks = Trek.query.all()
        trek_stats = []
        for t in treks:
            valid_bookings = [b for b in t.bookings if b.status != 'Cancelled']
            booked_count = sum(b.slots_booked for b in valid_bookings)
            trek_stats.append({
                'name': t.name,
                'location': t.location,
                'difficulty': t.difficulty,
                'total_slots': t.total_slots,
                'slots_booked': booked_count,
                'status': t.status
            })

        trek_stats.sort(key=lambda x: x['slots_booked'], reverse=True)

        # Generate HTML table rows cleanly
        table_rows = []
        for t in trek_stats:
            row_html = f"""<tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{t['name']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{t['location']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{t['difficulty']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{t['slots_booked']} / {t['total_slots']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;"><strong>{t['status']}</strong></td>
            </tr>"""
            table_rows.append(row_html)

        if table_rows:
            rows_html = "".join(table_rows)
        else:
            rows_html = '<tr><td colspan="5" style="text-align:center; padding:15px;">No treks conducted this period.</td></tr>'

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Monthly Trekking Activity Report - {month_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #1F6F5C; padding-bottom: 10px; }}
        .metric-cards {{ display: flex; gap: 15px; margin: 25px 0; }}
        .card {{ flex: 1; background: #ecf0f1; padding: 15px; border-radius: 6px; text-align: center; }}
        .card h3 {{ margin: 0; font-size: 14px; color: #7f8c8d; text-transform: uppercase; }}
        .card p {{ margin: 10px 0 0; font-size: 24px; font-weight: bold; color: #1F6F5C; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background-color: #1F6F5C; color: white; padding: 12px; text-align: left; }}
        .footer {{ margin-top: 30px; font-size: 12px; color: #95a5a6; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Monthly Trekking Activity Report</h1>
        <p><strong>Reporting Period:</strong> {month_name}</p>
        <p><strong>Recipient:</strong> System Administrator (admin@trekking.com)</p>

        <div class="metric-cards">
            <div class="card">
                <h3>Total Treks</h3>
                <p>{total_treks}</p>
            </div>
            <div class="card">
                <h3>Participants</h3>
                <p>{total_participants}</p>
            </div>
            <div class="card">
                <h3>Total Revenue</h3>
                <p>₹{total_revenue:,.2f}</p>
            </div>
        </div>

        <h2>Trek Performance & Slot Utilization</h2>
        <table>
            <thead>
                <tr>
                    <th>Trek Name</th>
                    <th>Location</th>
                    <th>Difficulty</th>
                    <th style="text-align: center;">Slots Booked</th>
                    <th style="text-align: center;">Status</th>
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>

        <div class="footer">
            <p>Generated automatically by Trekking Management Application (TMA) - Celery Batch Service.</p>
        </div>
    </div>
</body>
</html>"""

        filename = f"monthly_report_{month_tag}.html"
        report_path = os.path.join(REPORTS_DIR, filename)

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)

        log_notification(
            f"Monthly Report Generated: Saved at {filename}."
        )

        return {
            'success': True,
            'report_name': filename,
            'period': month_name,
            'total_treks': total_treks,
            'total_participants': total_participants,
            'total_revenue': total_revenue,
            'report_url': f'/api/admin/reports/monthly/{filename}'
        }
