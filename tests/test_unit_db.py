import os
import sqlite3
import tempfile
import unittest

from backend.app import init_db, set_database_path
from backend.db import get_db_connection


class TestDatabaseInitialization(unittest.TestCase):
    """Tests for database initialization and setup"""
    
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test_database.db")
        set_database_path(self.db_path)
        init_db()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_init_db_creates_admin(self):
        """Test that admin user is created during initialization"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        admin = conn.execute("SELECT * FROM admin WHERE username = ?", ("admin",)).fetchone()
        conn.close()

        self.assertIsNotNone(admin)
        self.assertEqual(admin["username"], "admin")
        password_hash = admin["password_hash"]
        self.assertIn(":", password_hash)
        self.assertTrue(password_hash.startswith("pbkdf2") or password_hash.startswith("scrypt"))

    def test_init_db_seeds_default_classes(self):
        """Test that default classes are seeded in database"""
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
        conn.close()

        self.assertGreater(count, 0)
        self.assertGreaterEqual(count, 6)  # We seed at least 6 default classes


class TestDatabaseOperations(unittest.TestCase):
    """Tests for CRUD operations on database"""
    
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test_database.db")
        set_database_path(self.db_path)
        init_db()
        
        # Get first class ID for student insertion
        conn = get_db_connection()
        self.class_id = conn.execute("SELECT id FROM classes ORDER BY id LIMIT 1").fetchone()[0]
        conn.close()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_insert_student(self):
        """Test inserting a new student"""
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO students (name, roll_no, class_id, subjects, marks, attendance) VALUES (?, ?, ?, ?, ?, ?)',
            ('John Doe', 'J-001', self.class_id, 'Math, English', 85, 90)
        )
        conn.commit()
        
        student = conn.execute('SELECT * FROM students WHERE roll_no = ?', ('J-001',)).fetchone()
        conn.close()
        
        self.assertIsNotNone(student)
        self.assertEqual(student['name'], 'John Doe')
        self.assertEqual(student['marks'], 85)
        self.assertEqual(student['attendance'], 90)

    def test_update_student(self):
        """Test updating a student record"""
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO students (name, roll_no, class_id, subjects, marks, attendance) VALUES (?, ?, ?, ?, ?, ?)',
            ('Jane Doe', 'J-002', self.class_id, 'Math', 75, 85)
        )
        conn.commit()
        
        student_id = conn.execute('SELECT id FROM students WHERE roll_no = ?', ('J-002',)).fetchone()[0]
        
        # Update the student
        conn.execute(
            'UPDATE students SET marks = ?, attendance = ? WHERE id = ?',
            (95, 98, student_id)
        )
        conn.commit()
        
        updated = conn.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
        conn.close()
        
        self.assertEqual(updated['marks'], 95)
        self.assertEqual(updated['attendance'], 98)

    def test_delete_student(self):
        """Test deleting a student"""
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO students (name, roll_no, class_id, subjects, marks, attendance) VALUES (?, ?, ?, ?, ?, ?)',
            ('Delete Me', 'D-001', self.class_id, 'Math', 50, 60)
        )
        conn.commit()
        
        student_id = conn.execute('SELECT id FROM students WHERE roll_no = ?', ('D-001',)).fetchone()[0]
        
        # Delete the student
        conn.execute('DELETE FROM students WHERE id = ?', (student_id,))
        conn.commit()
        
        deleted = conn.execute('SELECT * FROM students WHERE id = ?', (student_id,)).fetchone()
        conn.close()
        
        self.assertIsNone(deleted)

    def test_query_all_students(self):
        """Test retrieving all students with class info"""
        conn = get_db_connection()
        
        # Insert multiple students
        for i in range(3):
            conn.execute(
                'INSERT INTO students (name, roll_no, class_id, subjects, marks, attendance) VALUES (?, ?, ?, ?, ?, ?)',
                (f'Student {i}', f'S-{i:03d}', self.class_id, 'Math', 70 + i*5, 80 + i*2)
            )
        conn.commit()
        
        students = conn.execute('''
            SELECT s.*, c.name as class_name
            FROM students s
            JOIN classes c ON s.class_id = c.id
        ''').fetchall()
        conn.close()
        
        self.assertEqual(len(students), 3)
        self.assertIsNotNone(students[0]['class_name'])

    def test_student_roll_no_uniqueness(self):
        """Test that roll number must be unique"""
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO students (name, roll_no, class_id, subjects, marks, attendance) VALUES (?, ?, ?, ?, ?, ?)',
            ('Student 1', 'UNIQUE-001', self.class_id, 'Math', 80, 90)
        )
        conn.commit()
        
        # Try to insert duplicate roll number
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                'INSERT INTO students (name, roll_no, class_id, subjects, marks, attendance) VALUES (?, ?, ?, ?, ?, ?)',
                ('Student 2', 'UNIQUE-001', self.class_id, 'Math', 75, 85)
            )
            conn.commit()
        
        conn.close()


class TestClassOperations(unittest.TestCase):
    """Tests for class CRUD operations"""
    
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test_database.db")
        set_database_path(self.db_path)
        init_db()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_insert_class(self):
        """Test inserting a new class"""
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO classes (name, description) VALUES (?, ?)',
            ('Test Class', 'A test class')
        )
        conn.commit()
        
        class_record = conn.execute('SELECT * FROM classes WHERE name = ?', ('Test Class',)).fetchone()
        conn.close()
        
        self.assertIsNotNone(class_record)
        self.assertEqual(class_record['name'], 'Test Class')
        self.assertEqual(class_record['description'], 'A test class')

    def test_class_name_uniqueness(self):
        """Test that class names must be unique"""
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO classes (name, description) VALUES (?, ?)',
            ('Unique Class', 'First insert')
        )
        conn.commit()
        
        # Try to insert duplicate name
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                'INSERT INTO classes (name, description) VALUES (?, ?)',
                ('Unique Class', 'Second insert')
            )
            conn.commit()
        
        conn.close()

    def test_class_student_count(self):
        """Test counting students in a class"""
        conn = get_db_connection()
        class_id = conn.execute("SELECT id FROM classes ORDER BY id LIMIT 1").fetchone()[0]
        
        # Insert students
        for i in range(3):
            conn.execute(
                'INSERT INTO students (name, roll_no, class_id, subjects, marks, attendance) VALUES (?, ?, ?, ?, ?, ?)',
                (f'Student {i}', f'SC-{i:03d}', class_id, 'Math', 80, 90)
            )
        conn.commit()
        
        # Count students in class
        result = conn.execute('''
            SELECT c.*, COUNT(s.id) as student_count
            FROM classes c
            LEFT JOIN students s ON c.id = s.class_id
            WHERE c.id = ?
            GROUP BY c.id
        ''', (class_id,)).fetchone()
        conn.close()
        
        self.assertEqual(result['student_count'], 3)


class TestDataValidation(unittest.TestCase):
    """Tests for data validation constraints"""
    
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test_database.db")
        set_database_path(self.db_path)
        init_db()
        
        conn = get_db_connection()
        self.class_id = conn.execute("SELECT id FROM classes ORDER BY id LIMIT 1").fetchone()[0]
        conn.close()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_student_foreign_key_constraint(self):
        """Test that student must have valid class_id"""
        conn = get_db_connection()
        # Enable foreign key constraints in SQLite
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Try to insert with non-existent class_id
        with self.assertRaises(sqlite3.IntegrityError):
            conn.execute(
                'INSERT INTO students (name, roll_no, class_id, subjects, marks, attendance) VALUES (?, ?, ?, ?, ?, ?)',
                ('Invalid', 'I-001', 99999, 'Math', 80, 90)
            )
            conn.commit()
        
        conn.close()

    def test_admin_table_structure(self):
        """Test that admin table has correct structure"""
        conn = get_db_connection()
        admin_cols = [row[1] for row in conn.execute("PRAGMA table_info(admin)").fetchall()]
        conn.close()
        
        self.assertIn('id', admin_cols)
        self.assertIn('username', admin_cols)
        self.assertIn('password_hash', admin_cols)

    def test_students_table_structure(self):
        """Test that students table has correct structure"""
        conn = get_db_connection()
        student_cols = [row[1] for row in conn.execute("PRAGMA table_info(students)").fetchall()]
        conn.close()
        
        expected_cols = ['id', 'name', 'roll_no', 'class_id', 'subjects', 'marks', 'attendance']
        for col in expected_cols:
            self.assertIn(col, student_cols)


if __name__ == "__main__":
    unittest.main()
