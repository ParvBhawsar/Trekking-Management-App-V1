import os
import secrets
from datetime import date, datetime, timedelta
from functools import wraps

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from models import Booking, Trek, User, db


login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "warning"


DIFFICULTIES = ["Easy", "Moderate", "Hard"]
TREK_STATUSES = ["Pending", "Approved", "Open", "Started", "Closed", "Completed"]
STAFF_TREK_STATUSES = ["Approved", "Open", "Started", "Closed", "Completed"]


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    if os.getenv("VERCEL"):
        runtime_dir = "/tmp/trekmate"
        os.makedirs(runtime_dir, exist_ok=True)
        default_db_path = os.path.join(runtime_dir, "trekking.db")
    else:
        os.makedirs(app.instance_path, exist_ok=True)
        default_db_path = os.path.join(app.instance_path, "trekking.db")

    app.config.from_mapping(
        SECRET_KEY=os.getenv("SECRET_KEY", "simple-trekking-project-key"),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{default_db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()
        create_default_admin()
        if os.getenv("VERCEL"):
            create_demo_data_if_empty()

    register_routes(app)
    register_error_handlers(app)
    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def create_default_admin():
    admin = User.query.filter_by(role="admin").first()
    if admin is None:
        admin = User(
            name="System Admin",
            email="admin@trek.com",
            phone="9999999999",
            password_hash=generate_password_hash(
                os.getenv("TREKMATE_ADMIN_PASSWORD") or secrets.token_urlsafe(24)
            ),
            role="admin",
            approved=True,
            blacklisted=False,
        )
        db.session.add(admin)
        db.session.commit()


def create_demo_data_if_empty():
    """Seed a small demo dataset for ephemeral Vercel serverless instances."""
    if Trek.query.first() is not None:
        return

    staff = User.query.filter_by(email="staff@trek.com").first()
    if staff is None:
        staff = User(
            name="Aarav Guide",
            email="staff@trek.com",
            phone="9876543210",
            password_hash=generate_password_hash("staff123"),
            role="staff",
            approved=True,
            blacklisted=False,
        )
        db.session.add(staff)

    pending_staff = User.query.filter_by(email="pending@trek.com").first()
    if pending_staff is None:
        pending_staff = User(
            name="Meera Guide",
            email="pending@trek.com",
            phone="9876500000",
            password_hash=generate_password_hash("staff123"),
            role="staff",
            approved=False,
            blacklisted=False,
        )
        db.session.add(pending_staff)

    trekker = User.query.filter_by(email="user@trek.com").first()
    if trekker is None:
        trekker = User(
            name="Demo Trekker",
            email="user@trek.com",
            phone="9123456780",
            password_hash=generate_password_hash("user123"),
            role="user",
            approved=True,
            blacklisted=False,
        )
        db.session.add(trekker)

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
    db.session.add(Booking(user_id=trekker.id, trek_id=treks[0].id, status="Booked"))
    db.session.commit()


def role_required(*roles):
    def decorator(view_function):
        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):
            if current_user.role not in roles:
                abort(403)
            if current_user.blacklisted:
                logout_user()
                flash("Your account has been deactivated.", "danger")
                return redirect(url_for("login"))
            return view_function(*args, **kwargs)

        return wrapped_view

    return decorator


def parse_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def parse_positive_int(value, default=None):
    try:
        number = int(value)
        if number < 0:
            return default
        return number
    except (TypeError, ValueError):
        return default


def redirect_to_dashboard():
    if current_user.role == "admin":
        return redirect(url_for("admin_dashboard"))
    if current_user.role == "staff":
        return redirect(url_for("staff_dashboard"))
    return redirect(url_for("user_dashboard"))


def register_routes(app):
    @app.route("/")
    def home():
        open_treks = Trek.query.filter_by(status="Open").order_by(Trek.start_date).limit(3).all()
        return render_template("home.html", open_treks=open_treks)

    @app.route("/register/<role>", methods=["GET", "POST"])
    def register(role):
        if role not in {"user", "staff"}:
            abort(404)

        if current_user.is_authenticated:
            return redirect_to_dashboard()

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip()
            password = request.form.get("password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not name or not email or not password:
                flash("Name, email and password are required.", "danger")
            elif "@" not in email:
                flash("Please enter a valid email address.", "danger")
            elif len(password) < 6:
                flash("Password must contain at least 6 characters.", "danger")
            elif password != confirm_password:
                flash("Passwords do not match.", "danger")
            elif User.query.filter_by(email=email).first():
                flash("An account with this email already exists.", "danger")
            else:
                account = User(
                    name=name,
                    email=email,
                    phone=phone,
                    password_hash=generate_password_hash(password),
                    role=role,
                    approved=(role == "user"),
                )
                db.session.add(account)
                db.session.commit()
                if role == "staff":
                    flash("Registration successful. Wait for admin approval before logging in.", "success")
                else:
                    flash("Registration successful. You may now log in.", "success")
                return redirect(url_for("login"))

        return render_template("register.html", role=role)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect_to_dashboard()

        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            user = User.query.filter_by(email=email).first()

            if not user or not check_password_hash(user.password_hash, password):
                flash("Invalid email or password.", "danger")
            elif user.blacklisted:
                flash("This account has been deactivated by the admin.", "danger")
            elif user.role == "staff" and not user.approved:
                flash("Your staff account is waiting for admin approval.", "warning")
            else:
                login_user(user)
                flash(f"Welcome, {user.name}!", "success")
                return redirect_to_dashboard()

        return render_template("login.html")

    @app.route("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You have been logged out.", "info")
        return redirect(url_for("home"))

    # ---------------------------- Admin routes ----------------------------

    @app.route("/admin/dashboard")
    @role_required("admin")
    def admin_dashboard():
        query = request.args.get("q", "").strip()
        trek_results = []
        user_results = []
        staff_results = []

        if query:
            id_value = parse_positive_int(query)
            trek_filter = or_(
                Trek.name.ilike(f"%{query}%"),
                Trek.location.ilike(f"%{query}%"),
            )
            user_filter = User.name.ilike(f"%{query}%")
            if id_value is not None:
                trek_filter = or_(trek_filter, Trek.id == id_value)
                user_filter = or_(user_filter, User.id == id_value)

            trek_results = Trek.query.filter(trek_filter).all()
            user_results = User.query.filter(user_filter, User.role == "user").all()
            staff_results = User.query.filter(user_filter, User.role == "staff").all()

        counts = {
            "treks": Trek.query.count(),
            "users": User.query.filter_by(role="user").count(),
            "staff": User.query.filter_by(role="staff").count(),
            "bookings": Booking.query.count(),
            "pending_staff": User.query.filter_by(role="staff", approved=False, blacklisted=False).count(),
        }
        recent_bookings = Booking.query.order_by(Booking.booking_date.desc()).limit(5).all()
        return render_template(
            "admin_dashboard.html",
            counts=counts,
            recent_bookings=recent_bookings,
            query=query,
            trek_results=trek_results,
            user_results=user_results,
            staff_results=staff_results,
        )

    @app.route("/admin/treks")
    @role_required("admin")
    def admin_treks():
        query = request.args.get("q", "").strip()
        trek_query = Trek.query
        if query:
            id_value = parse_positive_int(query)
            criteria = or_(
                Trek.name.ilike(f"%{query}%"),
                Trek.location.ilike(f"%{query}%"),
            )
            if id_value is not None:
                criteria = or_(criteria, Trek.id == id_value)
            trek_query = trek_query.filter(criteria)
        treks = trek_query.order_by(Trek.start_date.desc()).all()
        return render_template("admin_treks.html", treks=treks, query=query)

    @app.route("/admin/treks/create", methods=["GET", "POST"])
    @role_required("admin")
    def admin_create_trek():
        approved_staff = User.query.filter_by(role="staff", approved=True, blacklisted=False).order_by(User.name).all()
        if request.method == "POST":
            trek, error = build_trek_from_form()
            if error:
                flash(error, "danger")
            else:
                db.session.add(trek)
                db.session.commit()
                flash("Trek created successfully.", "success")
                return redirect(url_for("admin_treks"))
        return render_template(
            "admin_trek_form.html",
            trek=None,
            approved_staff=approved_staff,
            difficulties=DIFFICULTIES,
            statuses=TREK_STATUSES,
        )

    @app.route("/admin/treks/<int:trek_id>/edit", methods=["GET", "POST"])
    @role_required("admin")
    def admin_edit_trek(trek_id):
        trek = Trek.query.get_or_404(trek_id)
        approved_staff = User.query.filter_by(role="staff", approved=True, blacklisted=False).order_by(User.name).all()

        if request.method == "POST":
            updated_trek, error = build_trek_from_form(existing=trek)
            if error:
                flash(error, "danger")
            else:
                if updated_trek.status == "Completed":
                    mark_bookings_completed(updated_trek)
                    updated_trek.available_slots = 0
                db.session.commit()
                flash("Trek updated successfully.", "success")
                return redirect(url_for("admin_treks"))

        return render_template(
            "admin_trek_form.html",
            trek=trek,
            approved_staff=approved_staff,
            difficulties=DIFFICULTIES,
            statuses=TREK_STATUSES,
        )

    @app.route("/admin/treks/<int:trek_id>/delete", methods=["POST"])
    @role_required("admin")
    def admin_delete_trek(trek_id):
        trek = Trek.query.get_or_404(trek_id)
        if trek.bookings:
            flash("This trek has booking history and cannot be deleted. Close it instead.", "warning")
        else:
            db.session.delete(trek)
            db.session.commit()
            flash("Trek removed successfully.", "success")
        return redirect(url_for("admin_treks"))

    @app.route("/admin/staff")
    @role_required("admin")
    def admin_staff():
        query = request.args.get("q", "").strip()
        staff_query = User.query.filter_by(role="staff")
        if query:
            id_value = parse_positive_int(query)
            criteria = or_(User.name.ilike(f"%{query}%"), User.email.ilike(f"%{query}%"))
            if id_value is not None:
                criteria = or_(criteria, User.id == id_value)
            staff_query = staff_query.filter(criteria)
        staff_members = staff_query.order_by(User.created_at.desc()).all()
        return render_template("admin_staff.html", staff_members=staff_members, query=query)

    @app.route("/admin/staff/<int:staff_id>/approve", methods=["POST"])
    @role_required("admin")
    def admin_approve_staff(staff_id):
        staff = User.query.filter_by(id=staff_id, role="staff").first_or_404()
        staff.approved = True
        staff.blacklisted = False
        db.session.commit()
        flash(f"{staff.name}'s staff account has been approved.", "success")
        return redirect(url_for("admin_staff"))

    @app.route("/admin/account/<int:user_id>/toggle-blacklist", methods=["POST"])
    @role_required("admin")
    def admin_toggle_blacklist(user_id):
        account = User.query.get_or_404(user_id)
        if account.role == "admin":
            flash("The admin account cannot be blacklisted.", "danger")
        else:
            account.blacklisted = not account.blacklisted
            if account.blacklisted and account.role == "staff":
                for trek in account.assigned_treks:
                    trek.assigned_staff_id = None
            db.session.commit()
            state = "blacklisted" if account.blacklisted else "reactivated"
            flash(f"{account.name} has been {state}.", "success")
        return redirect(request.referrer or url_for("admin_dashboard"))

    @app.route("/admin/users")
    @role_required("admin")
    def admin_users():
        query = request.args.get("q", "").strip()
        user_query = User.query.filter_by(role="user")
        if query:
            id_value = parse_positive_int(query)
            criteria = or_(User.name.ilike(f"%{query}%"), User.email.ilike(f"%{query}%"))
            if id_value is not None:
                criteria = or_(criteria, User.id == id_value)
            user_query = user_query.filter(criteria)
        users = user_query.order_by(User.created_at.desc()).all()
        return render_template("admin_users.html", users=users, query=query)

    @app.route("/admin/bookings")
    @role_required("admin")
    def admin_bookings():
        bookings = Booking.query.order_by(Booking.booking_date.desc()).all()
        return render_template("admin_bookings.html", bookings=bookings)

    # ---------------------------- Staff routes ----------------------------

    @app.route("/staff/dashboard")
    @role_required("staff")
    def staff_dashboard():
        treks = Trek.query.filter_by(assigned_staff_id=current_user.id).order_by(Trek.start_date).all()
        return render_template("staff_dashboard.html", treks=treks)

    @app.route("/staff/treks/<int:trek_id>/edit", methods=["GET", "POST"])
    @role_required("staff")
    def staff_edit_trek(trek_id):
        trek = Trek.query.get_or_404(trek_id)
        ensure_assigned_staff(trek)

        if request.method == "POST":
            available_slots = parse_positive_int(request.form.get("available_slots"))
            status = request.form.get("status", "")

            if available_slots is None:
                flash("Available slots must be a non-negative whole number.", "danger")
            elif available_slots > (trek.total_slots - trek.booked_count):
                flash("Available slots cannot exceed the unbooked capacity.", "danger")
            elif status not in STAFF_TREK_STATUSES:
                flash("Please select a valid trek status.", "danger")
            else:
                trek.available_slots = available_slots
                trek.status = status
                if status == "Completed":
                    mark_bookings_completed(trek)
                    trek.available_slots = 0
                db.session.commit()
                flash("Trek details updated successfully.", "success")
                return redirect(url_for("staff_dashboard"))

        return render_template(
            "staff_trek_edit.html",
            trek=trek,
            statuses=STAFF_TREK_STATUSES,
        )

    @app.route("/staff/treks/<int:trek_id>/participants")
    @role_required("staff")
    def staff_participants(trek_id):
        trek = Trek.query.get_or_404(trek_id)
        ensure_assigned_staff(trek)
        bookings = Booking.query.filter_by(trek_id=trek.id).order_by(Booking.booking_date.desc()).all()
        return render_template("staff_participants.html", trek=trek, bookings=bookings)

    @app.route("/staff/bookings/<int:booking_id>/status", methods=["POST"])
    @role_required("staff")
    def staff_update_booking_status(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        ensure_assigned_staff(booking.trek)
        new_status = request.form.get("status", "")

        if booking.status != "Booked":
            flash("Only active bookings can be updated by staff.", "warning")
        elif new_status not in {"Cancelled", "Completed"}:
            flash("Please select a valid participant status.", "danger")
        else:
            booking.status = new_status
            if new_status == "Cancelled" and booking.trek.status != "Completed":
                booking.trek.available_slots = min(
                    booking.trek.total_slots,
                    booking.trek.available_slots + 1,
                )
            db.session.commit()
            flash("Participant booking status updated.", "success")
        return redirect(url_for("staff_participants", trek_id=booking.trek_id))

    # ----------------------------- User routes ----------------------------

    @app.route("/user/dashboard")
    @role_required("user")
    def user_dashboard():
        open_treks = Trek.query.filter_by(status="Open").order_by(Trek.start_date).limit(6).all()
        recent_bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).limit(5).all()
        return render_template(
            "user_dashboard.html",
            open_treks=open_treks,
            recent_bookings=recent_bookings,
        )

    @app.route("/treks")
    @role_required("user")
    def browse_treks():
        query = request.args.get("q", "").strip()
        difficulty = request.args.get("difficulty", "").strip()
        location = request.args.get("location", "").strip()

        trek_query = Trek.query.filter_by(status="Open")
        if query:
            trek_query = trek_query.filter(
                or_(Trek.name.ilike(f"%{query}%"), Trek.location.ilike(f"%{query}%"))
            )
        if difficulty in DIFFICULTIES:
            trek_query = trek_query.filter_by(difficulty=difficulty)
        if location:
            trek_query = trek_query.filter(Trek.location.ilike(f"%{location}%"))

        treks = trek_query.order_by(Trek.start_date).all()
        booked_trek_ids = {
            booking.trek_id
            for booking in Booking.query.filter_by(user_id=current_user.id, status="Booked").all()
        }
        return render_template(
            "browse_treks.html",
            treks=treks,
            booked_trek_ids=booked_trek_ids,
            difficulties=DIFFICULTIES,
            query=query,
            selected_difficulty=difficulty,
            selected_location=location,
        )

    @app.route("/treks/<int:trek_id>/book", methods=["POST"])
    @role_required("user")
    def book_trek(trek_id):
        trek = Trek.query.get_or_404(trek_id)
        existing = Booking.query.filter_by(
            user_id=current_user.id,
            trek_id=trek.id,
            status="Booked",
        ).first()

        if trek.status != "Open":
            flash("Only open treks can be booked.", "danger")
        elif trek.available_slots <= 0:
            flash("Sorry, this trek is full.", "warning")
        elif existing:
            flash("You have already booked this trek.", "info")
        else:
            booking = Booking(user_id=current_user.id, trek_id=trek.id, status="Booked")
            trek.available_slots -= 1
            db.session.add(booking)
            db.session.commit()
            flash("Trek booked successfully.", "success")
        return redirect(request.referrer or url_for("browse_treks"))

    @app.route("/bookings")
    @role_required("user")
    def user_bookings():
        bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booking_date.desc()).all()
        return render_template("user_bookings.html", bookings=bookings)

    @app.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
    @role_required("user")
    def cancel_booking(booking_id):
        booking = Booking.query.get_or_404(booking_id)
        if booking.user_id != current_user.id:
            abort(403)
        if booking.status != "Booked":
            flash("Only active bookings can be cancelled.", "warning")
        elif booking.trek.status == "Completed":
            flash("A completed trek booking cannot be cancelled.", "warning")
        else:
            booking.status = "Cancelled"
            booking.trek.available_slots = min(
                booking.trek.total_slots,
                booking.trek.available_slots + 1,
            )
            db.session.commit()
            flash("Booking cancelled successfully.", "success")
        return redirect(url_for("user_bookings"))

    @app.route("/profile", methods=["GET", "POST"])
    @role_required("user")
    def user_profile():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            phone = request.form.get("phone", "").strip()
            if not name:
                flash("Name cannot be empty.", "danger")
            else:
                current_user.name = name
                current_user.phone = phone
                db.session.commit()
                flash("Profile updated successfully.", "success")
                return redirect(url_for("user_profile"))
        return render_template("user_profile.html")

    # -------------------------- Shared helper routes ----------------------

    @app.route("/trek/<int:trek_id>")
    @login_required
    def trek_detail(trek_id):
        trek = Trek.query.get_or_404(trek_id)
        return render_template("trek_detail.html", trek=trek)

    def build_trek_from_form(existing=None):
        name = request.form.get("name", "").strip()
        location = request.form.get("location", "").strip()
        difficulty = request.form.get("difficulty", "")
        duration_days = parse_positive_int(request.form.get("duration_days"))
        total_slots = parse_positive_int(request.form.get("total_slots"))
        available_slots = parse_positive_int(request.form.get("available_slots"))
        status = request.form.get("status", "")
        start_date = parse_date(request.form.get("start_date"))
        end_date = parse_date(request.form.get("end_date"))
        description = request.form.get("description", "").strip()
        assigned_staff_id = parse_positive_int(request.form.get("assigned_staff_id"))

        if not name or not location:
            return existing, "Trek name and location are required."
        if difficulty not in DIFFICULTIES:
            return existing, "Please select a valid difficulty."
        if duration_days is None or duration_days < 1:
            return existing, "Duration must be at least 1 day."
        if total_slots is None or total_slots < 1:
            return existing, "Total slots must be at least 1."
        if available_slots is None or available_slots > total_slots:
            return existing, "Available slots must be between 0 and total slots."
        if status not in TREK_STATUSES:
            return existing, "Please select a valid status."
        if not start_date or not end_date or end_date < start_date:
            return existing, "Please enter valid start and end dates."

        assigned_staff = None
        if assigned_staff_id:
            assigned_staff = User.query.filter_by(
                id=assigned_staff_id,
                role="staff",
                approved=True,
                blacklisted=False,
            ).first()
            if not assigned_staff:
                return existing, "Selected staff member is not available."

        trek = existing or Trek()
        active_booking_count = Booking.query.filter_by(trek_id=trek.id, status="Booked").count() if existing else 0
        if total_slots < active_booking_count:
            return existing, "Total slots cannot be less than current active bookings."
        if available_slots > (total_slots - active_booking_count):
            return existing, "Available slots cannot exceed the unbooked capacity."

        trek.name = name
        trek.location = location
        trek.difficulty = difficulty
        trek.duration_days = duration_days
        trek.total_slots = total_slots
        trek.available_slots = available_slots
        trek.status = status
        trek.start_date = start_date
        trek.end_date = end_date
        trek.description = description
        trek.assigned_staff_id = assigned_staff.id if assigned_staff else None
        return trek, None

    def ensure_assigned_staff(trek):
        if trek.assigned_staff_id != current_user.id:
            abort(403)

    def mark_bookings_completed(trek):
        for booking in trek.bookings:
            if booking.status == "Booked":
                booking.status = "Completed"


def register_error_handlers(app):
    @app.errorhandler(403)
    def forbidden(error):
        return render_template("error.html", code=403, message="You do not have permission to access this page."), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("error.html", code=404, message="The requested page was not found."), 404


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
