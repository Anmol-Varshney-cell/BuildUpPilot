from flask import Flask
from flask_login import LoginManager
from flask_cors import CORS
import redis
import os

from config import Config

app = Flask(__name__)
app.config.from_object(Config)
app.config['TEMPLATES_AUTO_RELOAD'] = True
from datetime import timedelta

is_production = bool(os.environ.get('VERCEL') or os.environ.get('FLASK_ENV') == 'production')

app.secret_key = Config.SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = is_production

# Remember Me Cookie configuration for browser saved credentials
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(days=30)
app.config['REMEMBER_COOKIE_HTTPONLY'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_SECURE'] = is_production

# Initialize Redis session store if available, otherwise use secure signed cookie sessions
try:
    redis_client = redis.from_url(Config.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
    redis_client.ping()  # Test connection
    app.config['SESSION_REDIS'] = redis_client
    app.config['SESSION_TYPE'] = 'redis'
    try:
        from flask_session import Session
        Session(app)
        print("✓ Redis session store initialized")
    except ImportError:
        app.config['SESSION_TYPE'] = None
        print("[WARN] flask_session module issue, using built-in signed cookie sessions")
except Exception as e:
    app.config['SESSION_TYPE'] = None
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

def _seed_default_accounts():
    """Ensure default test and seed accounts exist with valid hashed passwords."""
    from models import User, StudentProfile
    
    seed_users = [
        {
            'email': 'student@buildup.com',
            'password': 'student123',
            'role': 'student',
            'student_id': 'BUPS00',
            'first_name': 'Student',
            'last_name': 'User'
        },
        {
            'email': 'admin@buildup.com',
            'password': 'admin123',
            'role': 'admin',
            'student_id': 'BUPA00',
            'first_name': 'Admin',
            'last_name': 'User'
        },
        {
            'email': 'recruiter@buildup.com',
            'password': 'recruiter123',
            'role': 'recruiter',
            'student_id': 'BUPR00',
            'first_name': 'Recruiter',
            'last_name': 'User'
        }
    ]

    for seed in seed_users:
        user = User.query.filter_by(email=seed['email']).first()
        if not user:
            pw_hash = bcrypt.generate_password_hash(seed['password']).decode('utf-8')
            user = User(
                email=seed['email'],
                password_hash=pw_hash,
                role=seed['role'],
                student_id=seed['student_id'],
                active=True,
                first_name=seed['first_name'],
                last_name=seed['last_name']
            )
            db.session.add(user)
            db.session.commit()

            if seed['role'] == 'student':
                profile = StudentProfile.query.filter_by(user_id=user.id).first()
                if not profile:
                    profile = StudentProfile(
                        user_id=user.id,
                        first_name=seed['first_name'],
                        last_name=seed['last_name']
                    )
                    db.session.add(profile)
                    db.session.commit()

with app.app_context():
    db.create_all()
    _ensure_user_schema()
    _seed_default_accounts()

from routes import main, auth, student, admin, recruiter, api
app.register_blueprint(main)
app.register_blueprint(auth)
app.register_blueprint(student)
app.register_blueprint(admin)
app.register_blueprint(recruiter)
app.register_blueprint(api)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))
    # Disable reloader and debug signals for compatibility with cloud threads/containers
    app.run(debug=False, use_reloader=False, host='0.0.0.0', port=port)