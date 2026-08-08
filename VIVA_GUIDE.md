# TrekMate Viva Guide

## 1. Thirty-second introduction

"My project is TrekMate, a role-based Trekking Management Application developed using Flask, Jinja2, Bootstrap and SQLite. It has three roles: Admin, Trek Staff and Trekker. The main purpose is to replace manual coordination with a system for staff approval, trek assignment, slot management, booking and booking history."

## 2. Simple application flow

1. `app.py` creates the Flask application and SQLite tables.
2. A default admin is inserted automatically if it does not exist.
3. Users and staff register through the same User table with different role values.
4. Staff accounts remain unapproved until the admin approves them.
5. The admin creates a trek and assigns an approved staff member.
6. The staff member updates slots and status for assigned treks only.
7. A trekker can book only an Open trek with an available slot.
8. Every booking remains stored as Booked, Cancelled or Completed.

## 3. Database tables

### User
Stores admin, staff and trekker accounts. Important fields are `role`, `approved` and `blacklisted`.

### Trek
Stores trek details, capacity, dates, status and the assigned staff ID.

### Booking
Connects one trekker to one trek. It stores booking date and status.

Relations:
- One staff member can be assigned to many treks.
- One trekker can have many bookings.
- One trek can have many bookings.

## 4. Code areas you must understand

### `create_app()`
Configures Flask, gives SQLite a location, initializes extensions, creates tables and creates the default admin.

### `role_required()`
A custom decorator. It first requires login and then checks whether the logged-in user's role is allowed for the route.

### `book_trek()`
Checks four things: role is user, trek is Open, slots are available and no active duplicate booking exists. It then creates a Booking and subtracts one available slot.

### `cancel_booking()`
Changes the booking status instead of deleting it, then restores one slot. This preserves history.

### `ensure_assigned_staff()`
Compares the trek's assigned staff ID with the current staff ID. A mismatch returns HTTP 403.

### `mark_bookings_completed()`
When a trek is marked Completed, active Booked records become Completed.

## 5. Common viva questions and answers

**Why SQLite?**  
It is mandatory for the project, lightweight and stored as a local file, so it is suitable for a local demonstration.

**Why use three tables instead of separate login tables?**  
All roles share common fields such as name, email and password. The `role` field controls access, which keeps authentication simple.

**How is the password protected?**  
The password is converted into a secure hash using Werkzeug. The original password is never stored in the database.

**How do you prevent overbooking?**  
Before booking, the route checks that `available_slots > 0`. A successful booking decreases it by one. A cancellation increases it by one, up to the total capacity.

**How do you preserve booking history?**  
Cancelled and completed bookings are not deleted. Only their status changes.

**How is staff approval handled?**  
A newly registered staff member has `approved=False`. Login is blocked until the admin changes it to true.

**How is authorization different from authentication?**  
Authentication verifies who the user is through login. Authorization checks what that logged-in role is allowed to access.

**What happens if a blacklisted staff member had assigned treks?**  
The blacklist route removes that staff assignment from those treks.

**Why did you avoid JavaScript?**  
All core functions use normal HTML forms and Flask routes, matching the requirement that JavaScript must not execute core functionality.

## 6. Easy live modifications to practise

Practise these before viva:

1. Add a new field such as trek meeting point.
2. Change the dashboard card title.
3. Add one more difficulty option.
4. Change the maximum number of homepage treks from 3 to 5.
5. Add a validation message for a past start date.
6. Change the admin default email.
7. Add a filter for trek status on the admin page.

## 7. Five-minute demo order

1. Login as pending staff and show that access is denied.
2. Login as admin and approve the staff member.
3. Create or edit a trek and assign staff.
4. Login as staff and update the trek to Open.
5. Login as trekker, search and book the trek.
6. Show the slot count decreasing.
7. Show the participant list from the staff dashboard.
8. Cancel the booking and show that history remains.
9. Show admin counts and complete booking history.

## 8. Files to remember

- `app.py`: routes and business logic
- `models.py`: database tables and relationships
- `templates/`: HTML pages
- `static/style.css`: visual design
- `instance/trekking.db`: automatically created SQLite database
- `seed_demo.py`: resets and fills the database for demonstration
