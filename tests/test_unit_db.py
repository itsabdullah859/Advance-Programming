import os
import sqlite3
import tempfile
import unittest

from backend.app import init_db, set_database_path


class TestDatabaseInitialization(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self._tmpdir.name, "test_database.db")
        set_database_path(self.db_path)
        init_db()

    def tearDown(self):
        self._tmpdir.cleanup()

    def test_init_db_creates_admin(self):
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
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM classes").fetchone()[0]
        conn.close()

        self.assertGreater(count, 0)


if __name__ == "__main__":
    unittest.main()
