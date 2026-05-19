from app import app, db
from models import User
from sqlalchemy import text

with app.app_context():
    # Create the new columns using text() for proper SQL execution
    db.session.execute(text('ALTER TABLE users ADD COLUMN company_id VARCHAR(100)'))
    db.session.execute(text('ALTER TABLE users ADD COLUMN company_id_card VARCHAR(200)'))
    db.session.execute(text('ALTER TABLE users ADD COLUMN company_id_status VARCHAR(20) DEFAULT "pending_verification"'))
    db.session.commit()
    print('Database columns added successfully')
