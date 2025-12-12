# Vehicle Parking Management System

A complete web-based Vehicle Parking Management System built using Python (Flask).
The application supports user and admin roles, allowing users to book parking spots effortlessly while admins manage parking lots, monitor bookings, and view analytical dashboards.

# Introduction

The Vehicle Parking Management System simplifies the process of locating, booking, and managing parking spaces.
Users can register, log in, search for nearby parking locations, book or release spots, and track their parking history.

Administrators can manage parking lots, parking spaces, users, and view usage analytics through charts.

The goal is to make parking management simple, efficient, and accessible for all.

# Technologies Used

Python 3 — Core programming language

Flask — Lightweight web framework

Flask-SQLAlchemy — ORM for database operations

SQLite — Simple and efficient database

Jinja2 — Templating engine for HTML

Bootstrap — Responsive UI components

Matplotlib — Used for generating analytic charts

# Features
# User Features

# User Registration & Login

Search Parking Locations (by name, address, or area)

Book & Release Spots

View Booking History (time, date, cost, location)

# Admin Features

Manage Parking Lots (add, edit, delete)

Manage Parking Spots

View All Users & Bookings

Admin Dashboard with statistics

Analytics & Charts showing usage trends

# Additional Features

Role-Based Access Control

Responsive UI (Bootstrap)

Clean Project Structure

 # Project Structure
project-folder/
│
├── app.py                 # Main Flask application
├── models.py              # Database models
│
├── /templates             # Jinja2 HTML templates
│   ├── user_dashboard.html
│   ├── admin_dashboard.html
│   └── ...
│
├── /static                # CSS, JS, Images
│
└── README.md              # Documentation

# How to Run the Project
1️ Clone the repository
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name

2️  Install dependencies
pip install flask flask_sqlalchemy matplotlib

3️ Run the application
python app.py

4️ Open in browser
http://127.0.0.1:5000/
