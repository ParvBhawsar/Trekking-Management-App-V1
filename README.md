# TrekMate - Trekking Management Application V1

TrekMate is a role-based web application developed for the Modern Application Development I (MAD1) project. It manages trekking events, staff approvals and assignments, trek bookings, slot availability, and booking history for three roles: Admin, Trek Staff, and Trekker.

## Features

### Admin
- View dashboard totals for treks, users, staff, and bookings
- Create, edit, and remove eligible treks
- Approve trek staff registrations
- Assign approved staff to treks
- Search treks, users, and staff by name or ID
- Blacklist or reactivate users and staff
- View complete booking history

### Trek Staff
- Register and log in after admin approval
- View only assigned treks
- Update available slots and trek status
- View participants registered for assigned treks
- Mark participant bookings or treks as completed

### Trekker
- Register and log in
- View and search open treks
- Filter treks by difficulty and location
- Book available treks
- Cancel active bookings
- View booking status and trekking history
- Edit profile details

## Business Rules

- Only treks with status `Open` can be booked
- Booking is blocked when no slots are available
- Duplicate active bookings for the same trek are prevented
- Only the assigned staff member can manage a trek
- Cancelled and completed bookings remain in the database as history
- Admin is created programmatically; there is no admin registration page

## Technology Stack

- **Backend:** Flask
- **Frontend:** Jinja2, HTML, CSS, Bootstrap
- **Database:** SQLite
- **Database ORM:** Flask-SQLAlchemy
- **Authentication:** Flask-Login
- **Password Hashing:** Werkzeug

No JavaScript is used for any core project requirement.

## Database

The application uses three main tables:

- `User` - stores Admin, Trek Staff, and Trekker accounts
- `Trek` - stores trek details, capacity, dates, status, and assigned staff
- `Booking` - connects trekkers with treks and stores booking history

The SQLite database and tables are created programmatically using `db.create_all()`.

## Project Structure

```text
Trekking_Management_App_V1/
├── app.py
├── models.py
├── seed_demo.py
├── requirements.txt
├── run.bat
├── instance/
├── static/
│   └── style.css
├── templates/
├── tests/
│   └── test_app.py
├── docs/
│   └── er_diagram.png
├── README.md
└── .gitignore
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv venv
```

### 2. Activate it on Windows

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create demo data

```bash
python seed_demo.py
```

### 5. Start the application

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## Demo Accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@trek.com` | `admin123` |
| Approved Staff | `staff@trek.com` | `staff123` |
| Trekker | `user@trek.com` | `user123` |
| Pending Staff | `pending@trek.com` | `staff123` |

Running `seed_demo.py` resets the local database and recreates the demonstration records.

## Tests

Run the included tests with:

```bash
python -m unittest discover -s tests -v
```

The tests cover admin creation, successful booking, overbooking prevention, cancellation with booking-history retention, and assigned-staff authorization.

## Student

**Parv Bhawsar**  
IIT Madras BS - Modern Application Development I  
May 2026 Term
