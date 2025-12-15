# IntelliTrack - Secure Student and Class Data System

A simple, beginner-friendly Flask-based student and class management system with secure authentication, full CRUD operations, and analytics dashboard.

## Features

- **Admin Authentication**: Secure login with bcrypt password hashing and session management
- **Student Management**: Complete CRUD operations (Create, Read, Update, Delete)
- **Class Management**: Complete CRUD operations for classes with student enrollment tracking
- **Analytics Dashboard**: Performance insights, statistics, and data visualization
- **Clean UI**: Minimalist Scandinavian design with TailwindCSS
- **Data Validation**: Form validation for all inputs
- **Visual Feedback**: Color-coded badges for marks and attendance percentages

## Technology Stack

- **Backend**: Python Flask 3.0.0
- **Database**: SQLite
- **Frontend**: HTML, Jinja2 Templates, TailwindCSS
- **Authentication**: Werkzeug password hashing with session management

## Installation

1. Install dependencies:
```bash
pip3 install -r requirements.txt
```

2. Run the application:
```bash
python3 app.py
```

3. Access the application at: `http://localhost:5000`

## Default Credentials

- **Username**: admin
- **Password**: admin123

## Database Schema

### Admin Table
- `id` - Primary key
- `username` - Admin username
- `password_hash` - Hashed password

### Classes Table
- `id` - Primary key
- `name` - Class name (unique)
- `description` - Class description
- `created_at` - Timestamp

### Students Table
- `id` - Primary key
- `name` - Student name
- `roll_no` - Unique roll number
- `class_id` - Foreign key to classes table
- `subjects` - Subjects enrolled
- `marks` - Marks (0-100)
- `attendance` - Attendance percentage (0-100)

## Routes

- `/` - Redirects to login
- `/login` - Admin login page
- `/logout` - Logout and clear session
- `/dashboard` - Admin dashboard (protected)
- `/add-student` - Add new student form (protected)
- `/view-students` - View all students table (protected)
- `/edit-student/<id>` - Edit student form (protected)
- `/delete-student/<id>` - Delete student (protected)
- `/classes` - View all classes table (protected)
- `/add-class` - Add new class form (protected)
- `/edit-class/<id>` - Edit class form (protected)
- `/delete-class/<id>` - Delete class (protected)
- `/analytics` - Analytics dashboard with statistics (protected)

## Features Implemented

✅ Secure password hashing with Werkzeug
✅ Session-based authentication
✅ Protected routes with login_required decorator
✅ Form validation for student and class data
✅ Flash messages for user feedback
✅ Responsive design with TailwindCSS
✅ Color-coded performance indicators
✅ Scandinavian minimalist UI design
✅ Class management with CRUD operations
✅ Student enrollment tracking per class
✅ Analytics dashboard with performance statistics
✅ Data visualization for marks and attendance distribution

## Design Style

The application features a **Scandinavian minimalist aesthetic** with:
- Pale cool gray backgrounds
- Bold black typography for headings
- Thin, delicate subtitles
- Abstract geometric shapes in soft pastel blue and blush pink
- Generous negative space for clean, uncluttered interface

## Security Features

- Password hashing using Werkzeug's `generate_password_hash`
- Session-based authentication
- Protected routes requiring login
- CSRF protection through Flask sessions
- Input validation on all forms

## Code Level

The code is written at a **beginner to intermediate level** with:
- Clear, readable variable names
- Simple function structures
- Basic error handling
- Minimal complexity
- Easy-to-understand logic flow

## Notes

- The database is automatically initialized on first run
- Default admin account is created if none exists
- Default classes are added if none exist (Grade 10-A, Grade 10-B, etc.)
- SQLite database file (`database.db`) is created in the application directory
- All student and class data is stored locally in the SQLite database
