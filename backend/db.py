import sqlite3

from werkzeug.security import generate_password_hash

from backend.config import DEFAULT_DATABASE_PATH

DATABASE = DEFAULT_DATABASE_PATH


def set_database_path(database_path: str):
    global DATABASE
    DATABASE = database_path


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()

    # Create admin table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')

    # Create classes table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create students table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            roll_no TEXT UNIQUE NOT NULL,
            class_id INTEGER NOT NULL,
            subjects TEXT NOT NULL,
            marks INTEGER NOT NULL,
            attendance INTEGER NOT NULL,
            FOREIGN KEY (class_id) REFERENCES classes (id)
        )
    ''')

    # Check if admin exists, if not create default admin
    admin = conn.execute('SELECT * FROM admin WHERE username = ?', ('admin',)).fetchone()
    if not admin:
        password_hash = generate_password_hash('admin123')
        conn.execute('INSERT INTO admin (username, password_hash) VALUES (?, ?)',
                    ('admin', password_hash))

    # Add some default classes if none exist
    classes_count = conn.execute('SELECT COUNT(*) FROM classes').fetchone()[0]
    if classes_count == 0:
        default_classes = [
            ('Grade 10-A', 'Mathematics and Science focused class'),
            ('Grade 10-B', 'Commerce and Arts focused class'),
            ('Grade 11-Science', 'Science stream for Grade 11'),
            ('Grade 11-Commerce', 'Commerce stream for Grade 11'),
            ('Grade 12-Science', 'Science stream for Grade 12'),
            ('Grade 12-Commerce', 'Commerce stream for Grade 12')
        ]
        for class_name, description in default_classes:
            conn.execute('INSERT INTO classes (name, description) VALUES (?, ?)',
                        (class_name, description))

    conn.commit()
    conn.close()
