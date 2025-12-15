import os

from flask import Flask

from backend.config import TEMPLATES_DIR
from backend.db import get_db_connection, init_db, set_database_path
from backend.routes import register_routes


app = Flask(__name__, template_folder=TEMPLATES_DIR)
app.secret_key = os.urandom(24)

register_routes(app)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
