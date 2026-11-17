"""
Database Seeder Script for Trekking Management Application (TMA).
Populates SQLite with realistic demo data:
- Pre-seeded Admin
- Certified Trek Staff members with profiles
- Popular Himalayan Treks across difficulties (Easy, Moderate, Hard)
- Sample Trekker users and active bookings for analytics
"""

import os
import sys
from datetime import date, timedelta, datetime

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app import create_app
from backend.models import db, User, StaffProfile, Trek, Booking
from backend.cache import clear_cache


def seed_database():
    app = create_app()

    with app.app_context():
        print("🌱 Seeding database with realistic demo data...")

        # 1. Admin (Pre-seeded Superuser)
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@trekking.com',
                role='admin',
                full_name='System Administrator',
                phone='9876543210',
                is_active=True
            )
            admin.set_password('Admin@123')
            db.session.add(admin)
            db.session.commit()
            print("  ✅ Admin: admin@trekking.com / Admin@123")
        else:
            print("  ℹ️ Admin already exists.")

        # 2. Staff Members
        staff_data = [
            {
                'username': 'staff_arjun',
                'email': 'arjun.mehta@trekking.com',
                'password': 'StaffPassword123',
                'full_name': 'Arjun Mehta',
                'phone': '9876543220',
                'experience_years': 6,
                'bio': 'Certified Nehru Institute of Mountaineering (NIM) guide with 6 years experience across Garhwal.',
                'emergency_contact': '9876543229'
            },
            {
                'username': 'staff_priya',
                'email': 'priya.nair@trekking.com',
                'password': 'StaffPassword123',
                'full_name': 'Priya Nair',
                'phone': '9876543221',
                'experience_years': 4,
                'bio': 'Wilderness first-responder and high-altitude flora specialist.',
                'emergency_contact': '9876543228'
            },
            {
                'username': 'staff_vikram',
                'email': 'vikram.singh@trekking.com',
                'password': 'StaffPassword123',
                'full_name': 'Vikram Singh',
                'phone': '9876543222',
                'experience_years': 8,
                'bio': 'Senior expedition leader for Chadar and winter passes in Ladakh.',
                'emergency_contact': '9876543227'
            }
        ]

        staff_users = {}
        for s in staff_data:
            user = User.query.filter_by(username=s['username']).first()
            if not user:
                user = User(
                    username=s['username'],
                    email=s['email'],
                    full_name=s['full_name'],
                    phone=s['phone'],
                    role='staff',
                    is_active=True
                )
                user.set_password(s['password'])
                db.session.add(user)
                db.session.flush()

                profile = StaffProfile(
                    user_id=user.id,
                    experience_years=s['experience_years'],
                    bio=s['bio'],
                    emergency_contact=s['emergency_contact'],
                    status='Active'
                )
                db.session.add(profile)
                db.session.commit()
                print(f"  ✅ Staff created: {s['username']}")
            staff_users[s['username']] = user

        # 3. Sample Trekkers (Regular Users)
        trekkers_data = [
            {'username': 'trekker_rahul', 'email': 'rahul@example.com', 'full_name': 'Rahul Sharma', 'phone': '9123456701'},
            {'username': 'trekker_sneha', 'email': 'sneha@example.com', 'full_name': 'Sneha Rao', 'phone': '9123456702'},
            {'username': 'trekker_aarav', 'email': 'aarav@example.com', 'full_name': 'Aarav Kapoor', 'phone': '9123456703'},
            {'username': 'trekker_ananya', 'email': 'ananya@example.com', 'full_name': 'Ananya Sen', 'phone': '9123456704'}
        ]

        trekkers = {}
        for t in trekkers_data:
            user = User.query.filter_by(username=t['username']).first()
            if not user:
                user = User(
                    username=t['username'],
                    email=t['email'],
                    full_name=t['full_name'],
                    phone=t['phone'],
                    role='user',
                    is_active=True
                )
                user.set_password('Password123')
                db.session.add(user)
                db.session.commit()
                print(f"  ✅ Trekker created: {t['username']}")
            trekkers[t['username']] = user

        # 4. Realistic Treks
        today = date.today()
        treks_data = [
            {
                'name': 'Kedarkantha Winter Summit',
                'location': 'Uttarakhand',
                'description': 'Famous winter snow trek offering 360-degree views of Himalayan peaks.',
                'difficulty': 'Easy',
                'duration_days': 5,
                'total_slots': 20,
                'available_slots': 16,
                'price': 9500.0,
                'staff': staff_users['staff_arjun'],
                'start_date': today + timedelta(days=10),
                'end_date': today + timedelta(days=15),
                'status': 'Open'
            },
            {
                'name': 'Hampta Pass & Chandratal Lake',
                'location': 'Himachal Pradesh',
                'description': 'Dramatic crossover trek from lush green Kullu valley to arid desert of Spiti.',
                'difficulty': 'Moderate',
                'duration_days': 5,
                'total_slots': 15,
                'available_slots': 12,
                'price': 11000.0,
                'staff': staff_users['staff_priya'],
                'start_date': today + timedelta(days=18),
                'end_date': today + timedelta(days=23),
                'status': 'Open'
            },
            {
                'name': 'Roopkund Mystery Lake Expedition',
                'location': 'Uttarakhand',
                'description': 'High altitude trail leading to skeleton lake surrounded by Trishul and Nanda Ghunti peaks.',
                'difficulty': 'Hard',
                'duration_days': 7,
                'total_slots': 12,
                'available_slots': 9,
                'price': 14500.0,
                'staff': staff_users['staff_arjun'],
                'start_date': today + timedelta(days=25),
                'end_date': today + timedelta(days=32),
                'status': 'Open'
            },
            {
                'name': 'Valley of Flowers & Hemkund Sahib',
                'location': 'Uttarakhand',
                'description': 'UNESCO World Heritage botanical valley home to rare flora and alpine meadows.',
                'difficulty': 'Moderate',
                'duration_days': 6,
                'total_slots': 18,
                'available_slots': 15,
                'price': 8500.0,
                'staff': staff_users['staff_priya'],
                'start_date': today + timedelta(days=3),
                'end_date': today + timedelta(days=9),
                'status': 'Open'
            },
            {
                'name': 'Chadar Frozen River Trek',
                'location': 'Ladakh',
                'description': 'Extreme winter trek walking on the frozen Zanskar river in sub-zero temperatures.',
                'difficulty': 'Hard',
                'duration_days': 8,
                'total_slots': 10,
                'available_slots': 7,
                'price': 22500.0,
                'staff': staff_users['staff_vikram'],
                'start_date': today + timedelta(days=40),
                'end_date': today + timedelta(days=48),
                'status': 'Open'
            },
            {
                'name': 'Kuari Pass Pangarchulla Peak',
                'location': 'Uttarakhand',
                'description': 'Lord Curzon trail providing mesmerizing vistas of Mt. Nanda Devi.',
                'difficulty': 'Moderate',
                'duration_days': 6,
                'total_slots': 16,
                'available_slots': 16,
                'price': 10200.0,
                'staff': staff_users['staff_arjun'],
                'start_date': today + timedelta(days=30),
                'end_date': today + timedelta(days=36),
                'status': 'Open'
            }
        ]

        created_treks = []
        for td in treks_data:
            trek = Trek.query.filter_by(name=td['name']).first()
            if not trek:
                trek = Trek(
                    name=td['name'],
                    location=td['location'],
                    description=td['description'],
                    difficulty=td['difficulty'],
                    duration_days=td['duration_days'],
                    total_slots=td['total_slots'],
                    available_slots=td['available_slots'],
                    price=td['price'],
                    assigned_staff_id=td['staff'].id,
                    start_date=td['start_date'],
                    end_date=td['end_date'],
                    status=td['status']
                )
                db.session.add(trek)
                db.session.commit()
                print(f"  ✅ Trek seeded: {td['name']}")
            created_treks.append(trek)

        # 5. Seed Initial Bookings
        sample_bookings = [
            {'user': trekkers['trekker_rahul'], 'trek': created_treks[0], 'slots': 2},
            {'user': trekkers['trekker_sneha'], 'trek': created_treks[0], 'slots': 2},
            {'user': trekkers['trekker_aarav'], 'trek': created_treks[1], 'slots': 3},
            {'user': trekkers['trekker_ananya'], 'trek': created_treks[2], 'slots': 3},
            {'user': trekkers['trekker_rahul'], 'trek': created_treks[3], 'slots': 3},
            {'user': trekkers['trekker_sneha'], 'trek': created_treks[4], 'slots': 3}
        ]

        for sb in sample_bookings:
            existing = Booking.query.filter_by(user_id=sb['user'].id, trek_id=sb['trek'].id).first()
            if not existing:
                b = Booking(
                    user_id=sb['user'].id,
                    trek_id=sb['trek'].id,
                    slots_booked=sb['slots'],
                    total_price=sb['slots'] * sb['trek'].price,
                    booking_date=datetime.utcnow() - timedelta(days=2),
                    status='Booked',
                    payment_status='Paid'
                )
                db.session.add(b)
                db.session.commit()

        clear_cache("treks:*")
        print("🎉 Database seeded successfully with realistic demonstration data!\n")


if __name__ == '__main__':
    seed_database()
