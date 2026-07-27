import os
import shutil
from dotenv import load_dotenv

SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'

db_filename = 'buildup.db'
if os.environ.get('VERCEL'):
    tmp_db = os.path.join('/tmp', db_filename)
    if not os.path.exists(tmp_db) and os.path.exists(db_filename):
        try:
            shutil.copyfile(db_filename, tmp_db)
        except Exception:
            pass
    db_path = tmp_db
else:
    db_path = os.path.abspath(db_filename)

DATABASE_URL = os.environ.get('DATABASE_URL') or f'sqlite:///{db_path}'
REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379'
MAX_STUDENT_ACCOUNTS = int(os.environ.get('MAX_STUDENT_ACCOUNTS') or 10000)

class Config:
    SECRET_KEY = SECRET_KEY
    DATABASE_URL = DATABASE_URL
    REDIS_URL = REDIS_URL
    MAX_STUDENT_ACCOUNTS = MAX_STUDENT_ACCOUNTS
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_TYPE = 'redis'
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
