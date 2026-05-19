from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
import redis
import os

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = Config.SECRET_KEY

# Initialize Redis session store (required for up to 10000 student users)
# Fallback to simple signed cookie sessions if Redis is unavailable
try:
    redis_client = redis.from_url(Config.REDIS_URL)
    redis_client.ping()  # Test connection
    app.config['SESSION_REDIS'] = redis_client
    try:
        from flask_session import Session
        Session(app)
        print("✓ Redis session store initialized")
    except ImportError:
        print("[WARN] flask_session module issue, using built-in signed cookie sessions")
except redis.ConnectionError as e:
    print(f"[WARN] Redis unavailable ({e}), using built-in signed cookie sessions instead")

# Configure CORS
CORS(app, origins=[
    'http://localhost:5173', 'http://127.0.0.1:5173',
    'http://localhost:5174', 'http://127.0.0.1:5174'
], supports_credentials=True)

from extensions import db, bcrypt
db.init_app(app)
bcrypt.init_app(app)

def _ensure_user_schema():
    """Add columns used by newer recruiter approval/profile flows."""
    from sqlalchemy import inspect, text

    required_columns = {
        'company_id': 'VARCHAR(100)',
        'company_id_image_path': 'VARCHAR(200)',
        'company_id_status': "VARCHAR(20) DEFAULT 'pending_verification'",
        'company_id_verified_at': 'DATETIME',
        'company_id_verified_by': 'INTEGER',
        'company_name': 'VARCHAR(120)',
        'recruiter_request_email': 'VARCHAR(120)',
        'recruiter_request_otp': 'VARCHAR(6)',
        'recruiter_request_otp_expires': 'DATETIME',
        'recruiter_request_decline_count': 'INTEGER DEFAULT 0',
        'recruiter_request_last_submitted_at': 'DATETIME',
        'recruiter_request_last_notification': 'TEXT',
        'profile_image_path': 'VARCHAR(200)',
        'first_name': 'VARCHAR(50)',
        'last_name': 'VARCHAR(50)',
        'profession': 'VARCHAR(100)',
        'linkedin': 'VARCHAR(200)',
        'github': 'VARCHAR(200)'
    }

    inspector = inspect(db.engine)
    existing_columns = {column['name'] for column in inspector.get_columns('users')}
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            db.session.execute(text(f'ALTER TABLE users ADD COLUMN {column_name} {column_type}'))
    db.session.commit()

# Import and register simple OIDC provider
from simple_oidc import simple_oidc_bp
app.register_blueprint(simple_oidc_bp)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

# Import models before create_all so SQLAlchemy metadata is populated.
import models  # noqa: F401

with app.app_context():
    db.create_all()
    _ensure_user_schema()

from routes import main, auth, student, admin, recruiter, api
app.register_blueprint(main)
app.register_blueprint(auth)
app.register_blueprint(student)
app.register_blueprint(admin)
app.register_blueprint(recruiter)
app.register_blueprint(api)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    app.run(debug=True, port=port)
