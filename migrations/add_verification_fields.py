"""
Database migration script to add verification fields for secure authentication
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Add verification fields to the users table"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'buildup.db')
    
    if not os.path.exists(db_path):
        print("Database not found. Creating new database with verification fields...")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if masked_aadhaar column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add Aadhaar verification fields
        if 'masked_aadhaar' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN masked_aadhaar VARCHAR(14)
            ''')
            print("Added masked_aadhaar column")
        
        if 'aadhaar_number' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN aadhaar_number VARCHAR(12)
            ''')
            print("Added aadhaar_number column")
        
        if 'is_aadhaar_verified' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN is_aadhaar_verified BOOLEAN DEFAULT FALSE
            ''')
            print("Added is_aadhaar_verified column")
        
        if 'aadhaar_verification_status' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN aadhaar_verification_status VARCHAR(20) DEFAULT 'pending'
            ''')
            print("Added aadhaar_verification_status column")
        
        if 'aadhaar_verification_id' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN aadhaar_verification_id VARCHAR(100)
            ''')
            print("Added aadhaar_verification_id column")
        
        if 'aadhaar_verified_at' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN aadhaar_verified_at DATETIME
            ''')
            print("Added aadhaar_verified_at column")
        
        # Add Company ID verification fields for recruiters
        if 'company_id' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN company_id VARCHAR(100)
            ''')
            print("Added company_id column")
        
        if 'company_id_image_path' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN company_id_image_path VARCHAR(200)
            ''')
            print("Added company_id_image_path column")
        
        if 'company_id_status' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN company_id_status VARCHAR(20) DEFAULT 'pending_verification'
            ''')
            print("Added company_id_status column")
        
        # Add Company ID verification fields
        if 'company_id' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN company_id VARCHAR(50)
            ''')
            print("Added company_id column")
        
        if 'company_id_status' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN company_id_status VARCHAR(20) DEFAULT 'pending'
            ''')
            print("Added company_id_status column")
        
        if 'company_id_image_path' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN company_id_image_path VARCHAR(200)
            ''')
            print("Added company_id_image_path column")
        
        if 'company_id_verified_at' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN company_id_verified_at DATETIME
            ''')
            print("Added company_id_verified_at column")
        
        if 'company_id_verified_by' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN company_id_verified_by INTEGER
            ''')
            print("Added company_id_verified_by column")
        
        # Add admin fields
        if 'is_admin' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE
            ''')
            print("Added is_admin column")
        
        if 'created_by_admin_id' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN created_by_admin_id INTEGER
            ''')
            print("Added created_by_admin_id column")
        
        # Add security fields
        if 'mfa_secret' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(32)
            ''')
            print("Added mfa_secret column")
        
        if 'last_login_at' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN last_login_at DATETIME
            ''')
            print("Added last_login_at column")
        
        if 'login_attempts' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN login_attempts INTEGER DEFAULT 0
            ''')
            print("Added login_attempts column")
        
        if 'locked_until' not in columns:
            cursor.execute('''
                ALTER TABLE users ADD COLUMN locked_until DATETIME
            ''')
            print("Added locked_until column")
        
        # Update existing admin user
        cursor.execute('''
            UPDATE users SET is_admin = TRUE, aadhaar_verification_status = 'verified'
            WHERE email = 'admin@buildup.com'
        ''')
        
        # Update existing student user
        cursor.execute('''
            UPDATE users SET aadhaar_verification_status = 'verified'
            WHERE email = 'student@buildup.com'
        ''')
        
        # Update existing recruiter user
        cursor.execute('''
            UPDATE users SET aadhaar_verification_status = 'verified', company_id_status = 'verified'
            WHERE email = 'recruiter@buildup.com'
        ''')
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()
