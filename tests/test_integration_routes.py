import os
import sqlite3
import tempfile
import unittest

from backend.app import app, init_db, set_database_path


class TestIntegrationRoutes(unittest.TestCase):
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
        self._tmpdir.cleanup()

    def login(self, username="admin", password="admin123"):
        return self.client.post(
            "/login",
            data={"username": username, "password": password},
            follow_redirects=False,
        )

    def test_protected_route_redirects_when_not_logged_in(self):
        resp = self.client.get("/dashboard", follow_redirects=False)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_login_success_redirects_to_dashboard(self):
        resp = self.login()
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/dashboard", resp.headers.get("Location", ""))

    def test_login_failure_stays_on_login_page(self):
        resp = self.login(password="wrong")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Login", resp.data)

    def test_add_student_happy_path(self):
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


if __name__ == "__main__":
    unittest.main()
