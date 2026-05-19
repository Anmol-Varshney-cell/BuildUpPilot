"""
Company ID Verification Service
Handles company ID verification for recruiters
"""

import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class CompanyIDVerificationService:
    """Service for handling company ID verification"""
    
    def __init__(self):
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'pdf'}
        self.max_file_size = 5 * 1024 * 1024  # 5MB
        self.upload_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'company_ids')
        
        # Create upload folder if it doesn't exist
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def validate_company_id_format(self, company_id):
        """
        Validate company ID number format
        
        Args:
            company_id (str): Company ID number
            
        Returns:
            dict: Validation result
        """
        if not company_id or not company_id.strip():
            return {
                'valid': False,
                'error': 'Company ID is required',
                'error_code': 'MISSING_ID'
            }
        
        company_id = company_id.strip()
        
        # Basic format validation - adjust based on your requirements
        if len(company_id) < 6 or len(company_id) > 50:
            return {
                'valid': False,
                'error': 'Company ID must be between 6 and 50 characters',
                'error_code': 'INVALID_LENGTH'
            }
        
        # Check for valid characters (alphanumeric and common symbols)
        valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_/')
        if not all(char in valid_chars for char in company_id):
            return {
                'valid': False,
                'error': 'Company ID contains invalid characters',
                'error_code': 'INVALID_CHARS'
            }
        
        return {
            'valid': True,
            'error': None,
            'error_code': None
        }
    
    def save_company_id_image(self, file):
        """
        Save uploaded company ID image
        
        Args:
            file: Uploaded file object
            
        Returns:
            dict: Result with file path or error
        """
        try:
            # Check if file was uploaded
            if not file or file.filename == '':
                return {
                    'success': False,
                    'error': 'No file selected',
                    'error_code': 'NO_FILE'
                }
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > self.max_file_size:
                return {
                    'success': False,
                    'error': 'File size too large. Maximum size is 5MB',
                    'error_code': 'FILE_TOO_LARGE'
                }
            
            # Check file extension
            filename = secure_filename(file.filename)
            if not self._allowed_file(filename):
                return {
                    'success': False,
                    'error': 'Invalid file type. Allowed types: PNG, JPG, JPEG, PDF',
                    'error_code': 'INVALID_FILE_TYPE'
                }
            
            # Generate unique filename
            file_extension = filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            # Save file
            file.save(file_path)
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': unique_filename,
                'error': None,
                'error_code': None
            }
            
        except Exception as e:
            logger.error(f"Error saving company ID image: {str(e)}")
            return {
                'success': False,
                'error': 'Error saving file',
                'error_code': 'SAVE_ERROR'
            }
    
    def verify_company_id_number(self, company_id):
        """
        Verify company ID number (basic validation)
        
        Args:
            company_id (str): Company ID number
            
        Returns:
            dict: Verification result
        """
        try:
            # Basic validation
            validation_result = self.validate_company_id_format(company_id)
            if not validation_result['valid']:
                return validation_result
            
            # In production, this would integrate with company verification APIs
            # For demo, we'll do basic validation
            if current_app.config.get('DEMO_MODE', True):
                return self._simulate_company_id_verification(company_id)
            
            # Production implementation would go here
            # Could integrate with government business registration APIs
            return {
                'valid': True,
                'verified': True,
                'company_name': 'Demo Company',
                'error': None,
                'error_code': None
            }
            
        except Exception as e:
            logger.error(f"Error verifying company ID: {str(e)}")
            return {
                'valid': False,
                'verified': False,
                'error': 'Verification service error',
                'error_code': 'SERVICE_ERROR'
            }
    
    def review_uploaded_image(self, file_path):
        """
        Review uploaded company ID image (for admin manual review)
        
        Args:
            file_path (str): Path to uploaded image
            
        Returns:
            dict: Review result
        """
        try:
            # In production, this could use OCR or AI to validate the image
            # For now, return basic info
            return {
                'success': True,
                'file_path': file_path,
                'file_exists': os.path.exists(file_path),
                'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                'review_status': 'pending'
            }
            
        except Exception as e:
            logger.error(f"Error reviewing company ID image: {str(e)}")
            return {
                'success': False,
                'error': 'Error reviewing image',
                'error_code': 'REVIEW_ERROR'
            }
    
    def delete_company_id_image(self, file_path):
        """
        Delete company ID image file
        
        Args:
            file_path (str): Path to image file
            
        Returns:
            dict: Deletion result
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return {
                    'success': True,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'error': 'File not found',
                    'error_code': 'FILE_NOT_FOUND'
                }
                
        except Exception as e:
            logger.error(f"Error deleting company ID image: {str(e)}")
            return {
                'success': False,
                'error': 'Error deleting file',
                'error_code': 'DELETE_ERROR'
            }
    
    def _allowed_file(self, filename):
        """Check if file has allowed extension"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    
    def _simulate_company_id_verification(self, company_id):
        """Simulate company ID verification for demo"""
        # For demo, accept company IDs that start with 'COMP' or contain digits
        if company_id.startswith('COMP') or any(char.isdigit() for char in company_id):
            return {
                'valid': True,
                'verified': True,
                'company_name': f'Demo Company ({company_id[:8]}...)',
                'error': None,
                'error_code': None
            }
        else:
            return {
                'valid': False,
                'verified': False,
                'error': 'Company ID verification failed',
                'error_code': 'VERIFICATION_FAILED'
            }

# Global instance
company_id_service = CompanyIDVerificationService()
