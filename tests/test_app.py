import unittest
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from models import Booking, Trek, User, db


class TrekkingAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-key",
                "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            }
        )
        self.client = self.app.test_client()
        self.context = self.app.app_context()
        self.context.push()

        self.user1 = User(
            name="User One",
            email="user1@example.com",
            password_hash=generate_password_hash("user123"),
            role="user",
            approved=True,
        )
        self.user2 = User(
            name="User Two",
            email="user2@example.com",
            password_hash=generate_password_hash("user123"),
            role="user",
            approved=True,
        )
        self.staff = User(
            name="Guide One",
            email="staff@example.com",
            password_hash=generate_password_hash("staff123"),
            role="staff",
            approved=True,
        )
        db.session.add_all([self.user1, self.user2, self.staff])
        db.session.flush()

        self.trek = Trek(
            name="Test Trek",
            location="Test Hills",
            difficulty="Easy",
            duration_days=1,
            total_slots=1,
            available_slots=1,
            status="Open",
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=10),
            assigned_staff_id=self.staff.id,
        )
        db.session.add(self.trek)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def login(self, email, password):
        return self.client.post(
            "/login",
            data={"email": email, "password": password},
            follow_redirects=True,
        )

    def logout(self):
        return self.client.get("/logout", follow_redirects=True)

    def test_admin_is_created_programmatically(self):
        admin = User.query.filter_by(role="admin").first()
        self.assertIsNotNone(admin)
        self.assertEqual(admin.email, "admin@trek.com")

    def test_user_can_book_open_trek(self):
        self.login("user1@example.com", "user123")
        response = self.client.post(f"/treks/{self.trek.id}/book", follow_redirects=True)
        self.assertIn(b"Trek booked successfully", response.data)
        self.assertEqual(Booking.query.filter_by(user_id=self.user1.id, status="Booked").count(), 1)
        self.assertEqual(db.session.get(Trek, self.trek.id).available_slots, 0)

    def test_overbooking_is_prevented(self):
        self.login("user1@example.com", "user123")
        self.client.post(f"/treks/{self.trek.id}/book", follow_redirects=True)
        self.logout()
        self.login("user2@example.com", "user123")
        response = self.client.post(f"/treks/{self.trek.id}/book", follow_redirects=True)
        self.assertIn(b"this trek is full", response.data.lower())
        self.assertEqual(Booking.query.filter_by(trek_id=self.trek.id, status="Booked").count(), 1)

    def test_cancel_restores_slot_and_keeps_history(self):
        booking = Booking(user_id=self.user1.id, trek_id=self.trek.id, status="Booked")
        self.trek.available_slots = 0
        db.session.add(booking)
        db.session.commit()
        self.login("user1@example.com", "user123")
        self.client.post(f"/bookings/{booking.id}/cancel", follow_redirects=True)
        self.assertEqual(db.session.get(Booking, booking.id).status, "Cancelled")
        self.assertEqual(db.session.get(Trek, self.trek.id).available_slots, 1)

    def test_only_assigned_staff_can_edit_trek(self):
        other_staff = User(
            name="Guide Two",
            email="staff2@example.com",
            password_hash=generate_password_hash("staff123"),
            role="staff",
            approved=True,
        )
        db.session.add(other_staff)
        db.session.commit()
        self.login("staff2@example.com", "staff123")
        response = self.client.get(f"/staff/treks/{self.trek.id}/edit")
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
