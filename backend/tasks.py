"""
Celery Task Definitions for Trekking Management Application (TMA).
Implements:
1. Scheduled Job: Daily reminders sent to users for upcoming treks.
2. Scheduled Job: Monthly HTML activity report generated for Admin.
3. User-Triggered Async Job: Export booking & trekking history as CSV.
"""

import os
import csv
from datetime import datetime, date, timedelta
from backend.celery_app import celery
from backend.models import db, User, Trek, Booking

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
NOTIFICATIONS_LOG = os.path.join(BASE_DIR, 'notifications.log')

os.makedirs(EXPORTS_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)


def log_notification(message):
    """Log an outgoing notification, reminder, or system alert."""
    timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    entry = f"[{timestamp}] {message}\n"
    with open(NOTIFICATIONS_LOG, 'a', encoding='utf-8') as f:
        f.write(entry)
    print(f"📢 {message}")


@celery.task(name='backend.tasks.export_booking_history_csv')
def export_booking_history_csv(user_id):
    """
    User Triggered Async Job:
    Exports complete trekking and booking history of a user to CSV format.
    Fields included per specification:
      - User ID, Trek Name, Location, Booking Status, Dates (Booking, Start, End),
        Slots Booked, Total Price, Payment Status.
    """
    from backend.app import app

    with app.app_context():
        user = User.query.get(user_id)
        if not user:
            return {'success': False, 'message': f'User {user_id} not found.'}

        bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.booking_date.desc()).all()

        timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"booking_history_user_{user_id}_{timestamp_str}.csv"
        file_path = os.path.join(EXPORTS_DIR, filename)

        # Write CSV
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # Write Header
            writer.writerow([
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
            ])

            # Write Records
            for b in bookings:
                trek = b.trek
                writer.writerow([
                    b.id,
                    user.id,
                    user.full_name,
                    trek.name if trek else 'N/A',
                    trek.location if trek else 'N/A',
                    trek.difficulty if trek else 'N/A',
                    b.status,
                    b.booking_date.strftime('%Y-%m-%d %H:%M:%S') if b.booking_date else 'N/A',
                    trek.start_date.strftime('%Y-%m-%d') if trek and trek.start_date else 'N/A',
                    trek.end_date.strftime('%Y-%m-%d') if trek and trek.end_date else 'N/A',
                    b.slots_booked,
                    b.total_price,
                    b.payment_status
                ])

        log_notification(
            f"Export Complete: Booking history for User '{user.username}' (ID: {user_id}) exported to {filename}. ({len(bookings)} records)"
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
    """
    Scheduled Job (Daily):
    Finds all bookings for treks starting in the next 3 days and sends
    preparation reminders and guidelines to the registered users via email/webhook simulation.
    """
    from backend.app import app

    with app.app_context():
        today = date.today()
        upcoming_window = today + timedelta(days=3)

        # Treks starting within next 3 days
        upcoming_treks = Trek.query.filter(
            Trek.start_date >= today,
            Trek.start_date <= upcoming_window,
            Trek.status.in_(['Open', 'Approved', 'Started'])
        ).all()

        reminders_sent = 0
        details = []

        for trek in upcoming_treks:
            # Active bookings for this trek
            active_bookings = Booking.query.filter_by(trek_id=trek.id, status='Booked').all()

            for b in active_bookings:
                recipient = b.user
                days_left = (trek.start_date - today).days

                reminder_msg = (
                    f"Reminder to {recipient.full_name} ({recipient.email}): "
                    f"Your trek '{trek.name}' at {trek.location} starts in {days_left} day(s) on {trek.start_date}. "
                    f"Slots booked: {b.slots_booked}. Please bring appropriate trekking gear, sturdy shoes, and warm layers!"
                )

                log_notification(reminder_msg)
                details.append({
                    'user_id': recipient.id,
                    'user_email': recipient.email,
                    'trek_name': trek.name,
                    'start_date': trek.start_date.strftime('%Y-%m-%d')
                })
                reminders_sent += 1

        summary = f"Daily Reminders Job executed: {reminders_sent} reminder(s) dispatched for upcoming treks."
        log_notification(summary)

        return {
            'success': True,
            'reminders_sent': reminders_sent,
            'details': details
        }


@celery.task(name='backend.tasks.generate_monthly_activity_report')
def generate_monthly_activity_report():
    """
    Scheduled Job (Monthly):
    Generates a monthly activity and trekking statistics report for the Admin.
    Formats the report in clean HTML and saves it for Admin download and email simulation.
    """
    from backend.app import app

    with app.app_context():
        now = datetime.utcnow()
        month_name = now.strftime('%B %Y')
        month_tag = now.strftime('%Y_%m')

        total_treks = Trek.query.count()
        all_bookings = Booking.query.filter(Booking.status != 'Cancelled').all()
        total_participants = sum(b.slots_booked for b in all_bookings)
        total_revenue = sum(b.total_price for b in all_bookings)

        # Popular Treks Breakdown
        treks = Trek.query.all()
        trek_stats = []
        for t in treks:
            valid_bookings = [b for b in t.bookings if b.status != 'Cancelled']
            slots_booked = sum(b.slots_booked for b in valid_bookings)
            trek_stats.append({
                'name': t.name,
                'location': t.location,
                'difficulty': t.difficulty,
                'total_slots': t.total_slots,
                'slots_booked': slots_booked,
                'status': t.status
            })

        trek_stats.sort(key=lambda x: x['slots_booked'], reverse=True)

        # Generate HTML report
        rows_html = "".join([
            f"""<tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{t['name']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{t['location']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{t['difficulty']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">{t['slots_booked']} / {t['total_slots']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;"><strong>{t['status']}</strong></td>
            </tr>""" for t in trek_stats
        ])

        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Monthly Trekking Activity Report - {month_name}</title>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }}
        .container {{ max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        .metric-cards {{ display: flex; gap: 15px; margin: 25px 0; }}
        .card {{ flex: 1; background: #ecf0f1; padding: 15px; border-radius: 6px; text-align: center; }}
        .card h3 {{ margin: 0; font-size: 14px; color: #7f8c8d; text-transform: uppercase; }}
        .card p {{ margin: 10px 0 0; font-size: 24px; font-weight: bold; color: #2c3e50; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background-color: #3498db; color: white; padding: 12px; text-align: left; }}
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
                {rows_html if rows_html else '<tr><td colspan="5" style="text-align:center; padding:15px;">No treks conducted this period.</td></tr>'}
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
            f"Monthly Report Generated: Sent to Admin (admin@trekking.com). Saved at {filename}."
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
