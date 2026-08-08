# TrekMate - Trekking Management Application V1

A beginner-friendly Flask web application for managing treks, staff approvals, assignments and user bookings.

## Main technologies

- Flask back-end
- Jinja2, HTML, CSS and Bootstrap front-end
- SQLite database through Flask-SQLAlchemy
- Flask-Login for sessions and role-based access
- No JavaScript is used for any core requirement

## Project structure

```text
Trekking_Management_App_V1/
├── app.py                 # Routes, validation and application logic
├── models.py              # User, Trek and Booking database models
├── seed_demo.py           # Optional demo database generator
├── requirements.txt
├── run.bat
├── instance/              # SQLite database is created here automatically
├── static/style.css
├── templates/             # All Jinja2 pages
├── tests/test_app.py
├── docs/er_diagram.png
└── VIVA_GUIDE.md
```

## Setup and run

1. Open Command Prompt inside the project folder.
2. Create a virtual environment:

```bash
python -m venv venv
```

3. Activate it on Windows:

```bash
venv\Scripts\activate
```

4. Install packages:

```bash
pip install -r requirements.txt
```

5. Create useful demo records:

```bash
python seed_demo.py
```

6. Start the application:

```bash
python app.py
```

7. Open `http://127.0.0.1:5000` in a browser.

The database is created programmatically. Do not manually create or edit the SQLite database.

## Demo credentials

| Role | Email | Password |
|---|---|---|
| Admin | admin@trek.com | admin123 |
| Approved staff | staff@trek.com | staff123 |
| Trekker | user@trek.com | user123 |
| Pending staff | pending@trek.com | staff123 |

## Core feature checklist

### Admin
- Dashboard counts for treks, users, staff and bookings
- Create, edit and remove treks without booking history
- Approve staff registrations
- Assign approved staff to treks
- Search treks, users and staff by name, email, location or ID
- Blacklist and reactivate users/staff
- View all booking history

### Trek staff
- Self-register and wait for approval
- View assigned treks only
- Update available slots and status
- View participant and booking history
- Mark a trek completed, which completes active bookings

### Trekker
- Register, log in and edit profile
- Browse, search and filter open treks
- Book an open trek
- Cancel an active booking
- View active, cancelled and completed booking history

### Business rules
- Booking is allowed only when a trek is Open
- Available slots cannot go below zero
- Duplicate active bookings are prevented
- Only assigned staff can manage a trek
- Cancelled records remain in booking history

## Run automated tests

From the project folder:

```bash
python -m unittest discover -s tests -v
```

## Important before submission

- Change the project name, sample trek content and UI details in your own words.
- Practise explaining every model, route and validation rule.
- Record your own video and place its public Drive link in the report.
- Keep the repository private until the final project grade is released.
- Declare any AI/LLM assistance truthfully in the report.
