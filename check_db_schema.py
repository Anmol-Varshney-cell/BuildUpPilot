from app import app, db
from models import User
from sqlalchemy import text

with app.app_context():
    # Check current table schema
    result = db.session.execute(text('PRAGMA table_info(users)'))
    print("Current users table columns:")
    for row in result:
        print(f'Column: {row[1]} - Type: {row[2]}')
