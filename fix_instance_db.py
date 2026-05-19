import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'buildup.db')

if not os.path.exists(db_path):
    print("Database not found in instance folder.")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add Company ID verification fields
    if 'company_id' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN company_id VARCHAR(50)')
        print("Added company_id column")
        
    if 'company_id_status' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN company_id_status VARCHAR(20) DEFAULT 'pending'")
        print("Added company_id_status column")

    # --- Recruiter request + email OTP (demo-first) ---
    def _add_col(col, ddl):
        if col not in columns:
            cursor.execute(ddl)
            print(f"Added {col} column")

    _add_col('recruiter_request_status', "ALTER TABLE users ADD COLUMN recruiter_request_status VARCHAR(20) DEFAULT 'not_submitted'")
    _add_col('recruiter_request_email', "ALTER TABLE users ADD COLUMN recruiter_request_email VARCHAR(120)")
    _add_col('recruiter_request_otp', "ALTER TABLE users ADD COLUMN recruiter_request_otp VARCHAR(6)")
    _add_col('recruiter_request_otp_expires', "ALTER TABLE users ADD COLUMN recruiter_request_otp_expires DATETIME")
    _add_col('recruiter_request_decline_count', "ALTER TABLE users ADD COLUMN recruiter_request_decline_count INTEGER DEFAULT 0")
    _add_col('recruiter_request_last_submitted_at', "ALTER TABLE users ADD COLUMN recruiter_request_last_submitted_at DATETIME")
    _add_col('recruiter_request_last_notification', "ALTER TABLE users ADD COLUMN recruiter_request_last_notification TEXT")
    _add_col('profile_image_path', "ALTER TABLE users ADD COLUMN profile_image_path VARCHAR(200)")

        
    if 'company_id_image_path' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN company_id_image_path VARCHAR(200)')
        print("Added company_id_image_path column")
        
    if 'company_id_verified_at' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN company_id_verified_at DATETIME')
        print("Added company_id_verified_at column")
        
    if 'company_id_verified_by' not in columns:
        cursor.execute('ALTER TABLE users ADD COLUMN company_id_verified_by INTEGER')
        print("Added company_id_verified_by column")

    conn.commit()
    print("Database in instance folder updated successfully!")
    
except sqlite3.Error as e:
    print(f"Database error: {e}")
    conn.rollback()
finally:
    conn.close()
