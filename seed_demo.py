"""Reset the database and create simple demonstration records.

Run: python seed_demo.py
"""
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from models import Booking, Trek, User, db


app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    admin = User(
        name="System Admin",
        email="admin@trek.com",
        phone="9999999999",
        password_hash=generate_password_hash("admin123"),
        role="admin",
        approved=True,
    )
    staff = User(
        name="Aarav Guide",
        email="staff@trek.com",
        phone="9876543210",
        password_hash=generate_password_hash("staff123"),
        role="staff",
        approved=True,
    )
    pending_staff = User(
        name="Meera Guide",
        email="pending@trek.com",
        phone="9876500000",
        password_hash=generate_password_hash("staff123"),
        role="staff",
        approved=False,
    )
    trekker = User(
        name="Demo Trekker",
        email="user@trek.com",
        phone="9123456780",
        password_hash=generate_password_hash("user123"),
        role="user",
        approved=True,
    )
    db.session.add_all([admin, staff, pending_staff, trekker])
    db.session.flush()

    today = date.today()
    treks = [
        Trek(
            name="Munnar Tea Trail",
            location="Munnar, Kerala",
            difficulty="Easy",
            duration_days=2,
            total_slots=15,
            available_slots=14,
            assigned_staff_id=staff.id,
            status="Open",
            start_date=today + timedelta(days=15),
            end_date=today + timedelta(days=16),
            description="A beginner-friendly trek through tea estates and viewpoints.",
        ),
        Trek(
            name="Kodaikanal Forest Trek",
            location="Kodaikanal, Tamil Nadu",
            difficulty="Moderate",
            duration_days=3,
            total_slots=12,
            available_slots=12,
            assigned_staff_id=staff.id,
            status="Open",
            start_date=today + timedelta(days=30),
            end_date=today + timedelta(days=32),
            description="A moderate forest trail with camping and guided nature walks.",
        ),
        Trek(
            name="Himalayan Ridge Challenge",
            location="Manali, Himachal Pradesh",
            difficulty="Hard",
            duration_days=5,
            total_slots=10,
            available_slots=10,
            status="Approved",
            start_date=today + timedelta(days=60),
            end_date=today + timedelta(days=64),
            description="A demanding high-altitude trek for experienced participants.",
        ),
    ]
    db.session.add_all(treks)
    db.session.flush()

    booking = Booking(user_id=trekker.id, trek_id=treks[0].id, status="Booked")
    db.session.add(booking)
    db.session.commit()

    print("Demo database created successfully.")
    print("Admin: admin@trek.com / admin123")
    print("Staff: staff@trek.com / staff123")
    print("User: user@trek.com / user123")
