import os
import sqlite3
import tempfile
import unittest

from backend.app import app, init_db, set_database_path


class TestIntegrationRoutes(unittest.TestCase):
    """Integration tests for Flask routes and authentication"""
    
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test_database.db")
        set_database_path(self.db_path)
        init_db()

        app.config.update(TESTING=True)
        self.client = app.test_client()

        conn = sqlite3.connect(self.db_path)
        self.class_id = conn.execute("SELECT id FROM classes ORDER BY id LIMIT 1").fetchone()[0]
        conn.close()

    def tearDown(self):
        try:
            self._tmpdir.cleanup()
        except Exception:
            # Windows sometimes locks the database file, ignore cleanup errors
            pass

    def login(self, username="admin", password="admin123"):
        """Helper method to log in"""
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    # ===== Authentication Tests =====
    def test_index_redirects_to_login(self):
        """Test that index redirects to login page"""
        resp = self.client.get("/", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_protected_route_redirects_when_not_logged_in(self):
        """Test that protected routes redirect to login when not authenticated"""
        resp = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_login_success_redirects_to_dashboard(self):
        """Test successful login redirects to dashboard"""
        resp = self.login()
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/dashboard", resp.headers.get("Location", ""))

    def test_login_failure_stays_on_login_page(self):
        """Test failed login stays on login page"""
        resp = self.login(password="wrong")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Login", resp.data)

    def test_login_invalid_username(self):
        """Test login with invalid username"""
        resp = self.login(username="nonexistent", password="admin123")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Invalid", resp.data)

    def test_logout(self):
        """Test logout functionality"""
        self.login()
        resp = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    # ===== Dashboard Tests =====
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        resp = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)

    def test_dashboard_shows_after_login(self):
        """Test dashboard is accessible after login"""
        self.login()
        resp = self.client.get("/dashboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Dashboard", resp.data)

    # ===== Student CRUD Tests =====
    def test_add_student_happy_path(self):
        """Test successfully adding a student"""
        self.login()

        resp = self.client.post(
            "/add-student",
            data={
                "name": "Test Student",
                "roll_no": "T-001",
                "class_id": str(self.class_id),
                "subjects": "Math",
                "marks": "88",
                "attendance": "95",
            },
            follow_redirects=False,
        )

        self.assertEqual(resp.status_code, 302)
        self.assertIn("/view-students", resp.headers.get("Location", ""))

        conn = sqlite3.connect(self.db_path)
        row = conn.execute("SELECT name, roll_no FROM students WHERE roll_no = ?", ("T-001",)).fetchone()
        conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row[0], "Test Student")

    def test_add_student_duplicate_roll_no(self):
        """Test adding student with duplicate roll number"""
        self.login()

        # Add first student
        self.client.post(
            "/add-student",
            data={
                "name": "Student 1",
                "roll_no": "DUP-001",
                "class_id": str(self.class_id),
                "subjects": "Math",
                "marks": "85",
                "attendance": "90",
            },
        )

        # Try to add student with same roll number
        resp = self.client.post(
            "/add-student",
            data={
                "name": "Student 2",
                "roll_no": "DUP-001",
                "class_id": str(self.class_id),
                "subjects": "Math",
                "marks": "80",
                "attendance": "85",
            },
        )

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Roll number already exists", resp.data)

    def test_add_student_invalid_marks(self):
        """Test adding student with invalid marks (>100)"""
        self.login()

        resp = self.client.post(
            "/add-student",
            data={
                "name": "Invalid Marks",
                "roll_no": "IM-001",
                "class_id": str(self.class_id),
                "subjects": "Math",
                "marks": "150",
                "attendance": "90",
            },
        )

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"between 0 and 100", resp.data)

    def test_add_student_invalid_attendance(self):
        """Test adding student with invalid attendance"""
        self.login()

        resp = self.client.post(
            "/add-student",
            data={
                "name": "Invalid Attendance",
                "roll_no": "IA-001",
                "class_id": str(self.class_id),
                "subjects": "Math",
                "marks": "85",
                "attendance": "105",
            },
        )

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"between 0 and 100", resp.data)

    def test_add_student_missing_fields(self):
        """Test adding student with missing fields"""
        self.login()

        resp = self.client.post(
            "/add-student",
            data={
                "name": "Incomplete",
                "roll_no": "INC-001",
                # Missing other required fields
            },
        )

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"required", resp.data)

    def test_view_students(self):
        """Test viewing students list"""
        self.login()

        # Add a student first
        self.client.post(
            "/add-student",
            data={
                "name": "View Test",
                "roll_no": "VT-001",
                "class_id": str(self.class_id),
                "subjects": "Math",
                "marks": "88",
                "attendance": "95",
            },
        )

        resp = self.client.get("/view-students")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"View Test", resp.data)

    def test_view_students_with_sorting(self):
        """Test view students with sort parameters"""
        self.login()

        # Add students
        for i in range(3):
            self.client.post(
                "/add-student",
                data={
                    "name": f"Student {i}",
                    "roll_no": f"SORT-{i:03d}",
                    "class_id": str(self.class_id),
                    "subjects": "Math",
                    "marks": str(80 + i*5),
                    "attendance": str(90 - i*5),
                },
            )

        resp = self.client.get("/view-students?sort_by=marks&sort_order=desc")
        self.assertEqual(resp.status_code, 200)

    def test_view_students_with_search(self):
        """Test view students with search"""
        self.login()

        # Add a student
        self.client.post(
            "/add-student",
            data={
                "name": "SearchMe",
                "roll_no": "SEARCH-001",
                "class_id": str(self.class_id),
                "subjects": "Math",
                "marks": "88",
                "attendance": "95",
            },
        )

        resp = self.client.get("/view-students?search=SearchMe")
        self.assertEqual(resp.status_code, 200)

    def test_edit_student(self):
        """Test editing a student"""
        self.login()

        # Add a student
        self.client.post(
            "/add-student",
            data={
                "name": "Original Name",
                "roll_no": "EDIT-001",
                "class_id": str(self.class_id),
                "subjects": "Math",
                "marks": "80",
                "attendance": "90",
            },
        )

        # Get student ID
        conn = sqlite3.connect(self.db_path)
        student_id = conn.execute("SELECT id FROM students WHERE roll_no = ?", ("EDIT-001",)).fetchone()[0]
        conn.close()

        # Edit the student
        resp = self.client.post(
            f"/edit-student/{student_id}",
            data={
                "name": "Updated Name",
                "roll_no": "EDIT-001",
                "class_id": str(self.class_id),
                "subjects": "Math, Science",
                "marks": "95",
                "attendance": "98",
            },
            follow_redirects=False,
        )

        self.assertEqual(resp.status_code, 302)

        # Verify update
        conn = sqlite3.connect(self.db_path)
        updated = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        conn.close()

        self.assertEqual(updated[1], "Updated Name")  # name is at index 1
        self.assertEqual(updated[5], 95)  # marks

    def test_delete_student(self):
        """Test deleting a student"""
        self.login()

        # Add a student
        self.client.post(
            "/add-student",
            data={
                "name": "Delete Me",
                "roll_no": "DEL-001",
                "class_id": str(self.class_id),
                "subjects": "Math",
                "marks": "85",
                "attendance": "92",
            },
        )

        # Get student ID
        conn = sqlite3.connect(self.db_path)
        student_id = conn.execute("SELECT id FROM students WHERE roll_no = ?", ("DEL-001",)).fetchone()[0]
        conn.close()

        # Delete the student
        resp = self.client.get(f"/delete-student/{student_id}", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)

        # Verify deletion
        conn = sqlite3.connect(self.db_path)
        deleted = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        conn.close()

        self.assertIsNone(deleted)

    # ===== Class CRUD Tests =====
    def test_view_classes(self):
        """Test viewing classes list"""
        self.login()
        resp = self.client.get("/classes")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Class", resp.data)

    def test_add_class(self):
        """Test adding a class"""
        self.login()

        resp = self.client.post(
            "/add-class",
            data={
                "name": "Test Class A",
                "description": "A test class",
            },
            follow_redirects=False,
        )

        self.assertEqual(resp.status_code, 302)

        # Verify creation
        conn = sqlite3.connect(self.db_path)
        class_record = conn.execute("SELECT * FROM classes WHERE name = ?", ("Test Class A",)).fetchone()
        conn.close()

        self.assertIsNotNone(class_record)

    def test_add_class_duplicate_name(self):
        """Test adding class with duplicate name"""
        self.login()

        # Add first class
        self.client.post(
            "/add-class",
            data={
                "name": "Duplicate Class",
                "description": "First",
            },
        )

        # Try to add with same name
        resp = self.client.post(
            "/add-class",
            data={
                "name": "Duplicate Class",
                "description": "Second",
            },
        )

        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"already exists", resp.data)

    def test_delete_class_with_students_fails(self):
        """Test that deleting class with students fails"""
        self.login()

        # Add a student
        self.client.post(
            "/add-student",
            data={
                "name": "Student",
                "roll_no": "SAFE-001",
                "class_id": str(self.class_id),
                "subjects": "Math",
                "marks": "85",
                "attendance": "90",
            },
        )

        # Try to delete class with student
        resp = self.client.get(f"/delete-class/{self.class_id}", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)

        # Verify class still exists
        conn = sqlite3.connect(self.db_path)
        class_record = conn.execute("SELECT * FROM classes WHERE id = ?", (self.class_id,)).fetchone()
        conn.close()

        self.assertIsNotNone(class_record)

    # ===== Analytics Tests =====
    def test_analytics_page_loads(self):
        """Test analytics page loads"""
        self.login()
        resp = self.client.get("/analytics")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Analytics", resp.data)

    def test_analytics_with_data(self):
        """Test analytics displays correctly with student data"""
        self.login()

        # Add students with different marks
        for i in range(5):
            self.client.post(
                "/add-student",
                data={
                    "name": f"Analytics Student {i}",
                    "roll_no": f"ANALYTICS-{i:03d}",
                    "class_id": str(self.class_id),
                    "subjects": "Math",
                    "marks": str(60 + i*10),
                    "attendance": str(70 + i*5),
                },
            )

        resp = self.client.get("/analytics")
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
