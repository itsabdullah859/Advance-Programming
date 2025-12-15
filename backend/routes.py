import sqlite3

from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from backend.auth import login_required
from backend.db import get_db_connection


def register_routes(app):
    @app.route('/')
    def index():
        """
        Redirects to the login page.
        """
        return redirect(url_for('login'))

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')

            conn = get_db_connection()
            admin = conn.execute('SELECT * FROM admin WHERE username = ?', (username,)).fetchone()
            conn.close()

            if admin and check_password_hash(admin['password_hash'], password):
                session['logged_in'] = True
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')

        return render_template('login.html')

    @app.route('/logout')
    def logout():
        session.clear()
        flash('You have been logged out', 'success')
        return redirect(url_for('login'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        conn = get_db_connection()
        students = conn.execute('''
            SELECT s.*, c.name as class_name
            FROM students s
            JOIN classes c ON s.class_id = c.id
        ''').fetchall()
        classes = conn.execute('SELECT * FROM classes').fetchall()
        conn.close()
        return render_template('dashboard.html', students=students, classes=classes)

    @app.route('/add-student', methods=['GET', 'POST'])
    @login_required
    def add_student():
        conn = get_db_connection()
        classes = conn.execute('SELECT * FROM classes ORDER BY name').fetchall()

        if request.method == 'POST':
            name = request.form.get('name')
            roll_no = request.form.get('roll_no')
            class_id = request.form.get('class_id')
            subjects = request.form.get('subjects')
            marks = request.form.get('marks')
            attendance = request.form.get('attendance')

            # Basic validation
            if not all([name, roll_no, class_id, subjects, marks, attendance]):
                flash('All fields are required', 'error')
                return render_template('add_student.html', classes=classes)

            try:
                marks = int(marks)
                attendance = int(attendance)
                class_id = int(class_id)

                if marks < 0 or marks > 100:
                    flash('Marks must be between 0 and 100', 'error')
                    return render_template('add_student.html', classes=classes)

                if attendance < 0 or attendance > 100:
                    flash('Attendance must be between 0 and 100', 'error')
                    return render_template('add_student.html', classes=classes)

                conn.execute('INSERT INTO students (name, roll_no, class_id, subjects, marks, attendance) VALUES (?, ?, ?, ?, ?, ?)',
                            (name, roll_no, class_id, subjects, marks, attendance))
                conn.commit()
                conn.close()

                flash('Student added successfully!', 'success')
                return redirect(url_for('view_students'))
            except ValueError:
                flash('Marks and attendance must be numbers', 'error')
            except sqlite3.IntegrityError:
                flash('Roll number already exists', 'error')

        conn.close()
        return render_template('add_student.html', classes=classes)

    @app.route('/view-students')
    @login_required
    def view_students():
        conn = get_db_connection()
        students = conn.execute('''
            SELECT s.*, c.name as class_name
            FROM students s
            JOIN classes c ON s.class_id = c.id
            ORDER BY s.roll_no
        ''').fetchall()
        classes = conn.execute('SELECT * FROM classes ORDER BY name').fetchall()
        conn.close()
        return render_template('view_students.html', students=students, classes=classes)

    @app.route('/edit-student/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_student(id):
        conn = get_db_connection()
        classes = conn.execute('SELECT * FROM classes ORDER BY name').fetchall()

        if request.method == 'POST':
            name = request.form.get('name')
            roll_no = request.form.get('roll_no')
            class_id = request.form.get('class_id')
            subjects = request.form.get('subjects')
            marks = request.form.get('marks')
            attendance = request.form.get('attendance')

            if not all([name, roll_no, class_id, subjects, marks, attendance]):
                flash('All fields are required', 'error')
                return redirect(url_for('edit_student', id=id))

            try:
                marks = int(marks)
                attendance = int(attendance)
                class_id = int(class_id)

                if marks < 0 or marks > 100:
                    flash('Marks must be between 0 and 100', 'error')
                    return redirect(url_for('edit_student', id=id))

                if attendance < 0 or attendance > 100:
                    flash('Attendance must be between 0 and 100', 'error')
                    return redirect(url_for('edit_student', id=id))

                conn.execute('UPDATE students SET name = ?, roll_no = ?, class_id = ?, subjects = ?, marks = ?, attendance = ? WHERE id = ?',
                            (name, roll_no, class_id, subjects, marks, attendance, id))
                conn.commit()
                conn.close()

                flash('Student updated successfully!', 'success')
                return redirect(url_for('view_students'))
            except ValueError:
                flash('Marks and attendance must be numbers', 'error')
            except sqlite3.IntegrityError:
                flash('Roll number already exists', 'error')

        student = conn.execute('SELECT * FROM students WHERE id = ?', (id,)).fetchone()
        conn.close()

        if not student:
            flash('Student not found', 'error')
            return redirect(url_for('view_students'))

        return render_template('edit_student.html', student=student, classes=classes)

    @app.route('/delete-student/<int:id>')
    @login_required
    def delete_student(id):
        conn = get_db_connection()
        conn.execute('DELETE FROM students WHERE id = ?', (id,))
        conn.commit()
        conn.close()

        flash('Student deleted successfully!', 'success')
        return redirect(url_for('view_students'))

    # Class Management Routes
    @app.route('/classes')
    @login_required
    def view_classes():
        conn = get_db_connection()
        classes = conn.execute('''
            SELECT c.*, COUNT(s.id) as student_count
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id
            GROUP BY c.id
            ORDER BY c.name
        ''').fetchall()
        conn.close()
        return render_template('view_classes.html', classes=classes)

    @app.route('/add-class', methods=['GET', 'POST'])
    @login_required
    def add_class():
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description', '')

            if not name:
                flash('Class name is required', 'error')
                return render_template('add_class.html')

            try:
                conn = get_db_connection()
                conn.execute('INSERT INTO classes (name, description) VALUES (?, ?)',
                            (name, description))
                conn.commit()
                conn.close()

                flash('Class added successfully!', 'success')
                return redirect(url_for('view_classes'))
            except sqlite3.IntegrityError:
                flash('Class name already exists', 'error')

        return render_template('add_class.html')

    @app.route('/edit-class/<int:id>', methods=['GET', 'POST'])
    @login_required
    def edit_class(id):
        conn = get_db_connection()

        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description', '')

            if not name:
                flash('Class name is required', 'error')
                return redirect(url_for('edit_class', id=id))

            try:
                conn.execute('UPDATE classes SET name = ?, description = ? WHERE id = ?',
                            (name, description, id))
                conn.commit()
                conn.close()

                flash('Class updated successfully!', 'success')
                return redirect(url_for('view_classes'))
            except sqlite3.IntegrityError:
                flash('Class name already exists', 'error')

        class_info = conn.execute('SELECT * FROM classes WHERE id = ?', (id,)).fetchone()
        conn.close()

        if not class_info:
            flash('Class not found', 'error')
            return redirect(url_for('view_classes'))

        return render_template('edit_class.html', class_info=class_info)

    @app.route('/delete-class/<int:id>')
    @login_required
    def delete_class(id):
        conn = get_db_connection()

        # Check if class has students
        student_count = conn.execute('SELECT COUNT(*) FROM students WHERE class_id = ?', (id,)).fetchone()[0]

        if student_count > 0:
            conn.close()
            flash(f'Cannot delete class. It has {student_count} student(s) enrolled.', 'error')
            return redirect(url_for('view_classes'))

        conn.execute('DELETE FROM classes WHERE id = ?', (id,))
        conn.commit()
        conn.close()

        flash('Class deleted successfully!', 'success')
        return redirect(url_for('view_classes'))

    @app.route('/analytics')
    @login_required
    def analytics():
        conn = get_db_connection()

        # Get all students with class information
        students = conn.execute('''
            SELECT s.*, c.name as class_name
            FROM students s
            JOIN classes c ON s.class_id = c.id
            ORDER BY s.marks DESC
        ''').fetchall()

        # Get class statistics
        classes_stats = conn.execute('''
            SELECT
                c.name,
                COUNT(s.id) as student_count,
                AVG(s.marks) as avg_marks,
                AVG(s.attendance) as avg_attendance,
                MIN(s.marks) as min_marks,
                MAX(s.marks) as max_marks
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id
            GROUP BY c.id, c.name
            ORDER BY c.name
        ''').fetchall()

        # Performance distribution
        performance_ranges = {
            '90-100': len([s for s in students if s['marks'] >= 90]),
            '80-89': len([s for s in students if 80 <= s['marks'] < 90]),
            '70-79': len([s for s in students if 70 <= s['marks'] < 80]),
            '60-69': len([s for s in students if 60 <= s['marks'] < 70]),
            '50-59': len([s for s in students if 50 <= s['marks'] < 60]),
            'Below 50': len([s for s in students if s['marks'] < 50])
        }

        # Attendance distribution
        attendance_ranges = {
            '90-100': len([s for s in students if s['attendance'] >= 90]),
            '80-89': len([s for s in students if 80 <= s['attendance'] < 90]),
            '70-79': len([s for s in students if 70 <= s['attendance'] < 80]),
            '60-69': len([s for s in students if 60 <= s['attendance'] < 70]),
            'Below 60': len([s for s in students if s['attendance'] < 60])
        }

        # Top performers (top 5)
        top_performers = students[:5] if len(students) >= 5 else students

        # Students needing attention (marks < 50 or attendance < 60)
        students_attention = [s for s in students if s['marks'] < 50 or s['attendance'] < 60]

        conn.close()

        return render_template('analytics.html',
                             students=students,
                             classes_stats=classes_stats,
                             performance_ranges=performance_ranges,
                             attendance_ranges=attendance_ranges,
                             top_performers=top_performers,
                             students_attention=students_attention)
