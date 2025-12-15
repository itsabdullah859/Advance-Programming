import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, os.pardir))
TEMPLATES_DIR = os.path.join(PROJECT_ROOT, 'frontend', 'templates')
DEFAULT_DATABASE_PATH = os.path.join(PROJECT_ROOT, 'database.db')
