"""
Validation utilities for secure authentication system
"""

import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List


class ValidationError(Exception):
    """Custom validation error"""
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
        super().__init__(self.message)


class AuthValidator:
    """Authentication validation utilities"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_mobile(mobile: str) -> bool:
        """Validate Indian mobile number"""
        # Remove spaces and dashes
        mobile = re.sub(r'[\s-]', '', mobile)
        
        # Check if 10 digits and starts with 6-9
        return re.match(r'^[6-9]\d{9}$', mobile) is not None
    
    @staticmethod
    def validate_aadhaar(aadhaar: str) -> bool:
        """Validate Aadhaar number format"""
        # Remove spaces and dashes
        aadhaar = re.sub(r'[\s-]', '', aadhaar)
        
        # Check if exactly 12 digits
        return re.match(r'^\d{12}$', aadhaar) is not None
    
    @staticmethod
    def validate_password(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if len(password) > 128:
            errors.append("Password must not exceed 128 characters")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    @staticmethod
    def validate_name(name: str) -> bool:
        """Validate person's name"""
        # Check if name contains only letters, spaces, and basic punctuation
        pattern = r'^[a-zA-Z\s\.\'-]{2,50}$'
        return re.match(pattern, name) is not None
    
    @staticmethod
    def validate_company_id(company_id: str) -> bool:
        """Validate company ID format"""
        # Basic validation - adjust based on your requirements
        if not company_id or len(company_id.strip()) < 3:
            return False
        
        # Allow alphanumeric with basic special characters
        pattern = r'^[a-zA-Z0-9\s\-_]{3,50}$'
        return re.match(pattern, company_id) is not None
    
    @staticmethod
    def validate_otp(otp: str) -> bool:
        """Validate OTP format"""
        # Remove spaces
        otp = re.sub(r'\s', '', otp)
        
        # Check if exactly 6 digits
        return re.match(r'^\d{6}$', otp) is not None
    
    @staticmethod
    def validate_mfa_code(mfa_code: str) -> bool:
        """Validate MFA code format"""
        # Remove spaces
        mfa_code = re.sub(r'\s', '', mfa_code)
        
        # Check if exactly 6 digits
        return re.match(r'^\d{6}$', mfa_code) is not None
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """Sanitize user input"""
        if not input_string:
            return ""
        
        # Remove potentially harmful characters
        sanitized = re.sub(r'[<>"\']', '', input_string)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        return sanitized
    
    @staticmethod
    def validate_file_upload(file_obj, allowed_extensions: List[str], max_size_mb: int = 5) -> Dict[str, Any]:
        """Validate file upload"""
        errors = []
        
        if not file_obj:
            errors.append("No file provided")
            return {'valid': False, 'errors': errors}
        
        # Check file extension
        filename = file_obj.filename.lower()
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            errors.append(f"File type not allowed. Allowed: {', '.join(allowed_extensions)}")
        
        # Check file size
        file_size_mb = len(file_obj.read()) / (1024 * 1024)
        file_obj.seek(0)  # Reset file pointer
        
        if file_size_mb > max_size_mb:
            errors.append(f"File size exceeds {max_size_mb}MB limit")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'size_mb': file_size_mb
        }


class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def check_rate_limit(identifier: str, max_attempts: int = 5, window_minutes: int = 15) -> Dict[str, Any]:
        """Check if identifier has exceeded rate limit"""
        # This would typically use Redis or database to track attempts
        # For demo, return as not limited
        return {
            'limited': False,
            'attempts': 0,
            'reset_time': None
        }
    
    @staticmethod
    def detect_suspicious_activity(data: Dict[str, Any]) -> List[str]:
        """Detect suspicious activity patterns"""
        warnings = []
        
        # Check for rapid successive requests
        if 'request_count' in data and data['request_count'] > 10:
            warnings.append("High number of requests detected")
        
        # Check for unusual user agent patterns
        if 'user_agent' in data:
            ua = data['user_agent'].lower()
            if any(pattern in ua for pattern in ['bot', 'crawler', 'script']):
                warnings.append("Automated/bot activity detected")
        
        # Check for IP-based patterns
        if 'ip_address' in data:
            ip = data['ip_address']
            if ip.startswith('127.') or ip.startswith('192.168.'):
                warnings.append("Internal IP access detected")
        
        return warnings
    
    @staticmethod
    def validate_session_integrity(session_data: Dict[str, Any]) -> bool:
        """Validate session integrity"""
        required_fields = ['user_id', 'timestamp']
        
        for field in required_fields:
            if field not in session_data:
                return False
        
        # Check session age
        if 'timestamp' in session_data:
            session_age = datetime.utcnow() - session_data['timestamp']
            if session_age > timedelta(hours=24):
                return False
        
        return True


def validate_signup_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate complete signup data"""
    errors = {}
    
    # Validate email
    email = data.get('email', '').strip()
    if not email:
        errors['email'] = 'Email is required'
    elif not AuthValidator.validate_email(email):
        errors['email'] = 'Invalid email format'
    
    # Validate password
    password = data.get('password', '')
    if not password:
        errors['password'] = 'Password is required'
    else:
        password_validation = AuthValidator.validate_password(password)
        if not password_validation['valid']:
            errors['password'] = password_validation['errors']
    
    # Validate mobile
    mobile = data.get('mobile', '').strip()
    if not mobile:
        errors['mobile'] = 'Mobile number is required'
    elif not AuthValidator.validate_mobile(mobile):
        errors['mobile'] = 'Invalid mobile number format'
    
    # Validate name
    name = data.get('name', '').strip()
    if not name:
        errors['name'] = 'Name is required'
    elif not AuthValidator.validate_name(name):
        errors['name'] = 'Invalid name format'
    
    # Validate role
    role = data.get('role', '').strip()
    if not role:
        errors['role'] = 'Role is required'
    elif role not in ['student', 'recruiter', 'admin']:
        errors['role'] = 'Invalid role'
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def validate_login_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate login data"""
    errors = {}
    
    # Validate email
    email = data.get('email', '').strip()
    if not email:
        errors['email'] = 'Email is required'
    elif not AuthValidator.validate_email(email):
        errors['email'] = 'Invalid email format'
    
    # Validate password
    password = data.get('password', '')
    if not password:
        errors['password'] = 'Password is required'
    
    # Validate company ID for recruiters
    if data.get('role') == 'recruiter':
        company_id = data.get('company_id', '').strip()
        if not company_id:
            errors['company_id'] = 'Company ID is required'
        elif not AuthValidator.validate_company_id(company_id):
            errors['company_id'] = 'Invalid company ID format'
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def validate_aadhaar_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate Aadhaar verification data"""
    errors = {}
    
    # Validate Aadhaar number
    aadhaar = data.get('aadhaar_number', '').strip()
    if not aadhaar:
        errors['aadhaar_number'] = 'Aadhaar number is required'
    elif not AuthValidator.validate_aadhaar(aadhaar):
        errors['aadhaar_number'] = 'Invalid Aadhaar number format'
    
    # Validate OTP
    otp = data.get('otp', '').strip()
    if otp and not AuthValidator.validate_otp(otp):
        errors['otp'] = 'Invalid OTP format'
    
    # Validate XML data
    xml_data = data.get('xml_data', '').strip()
    if xml_data and len(xml_data) < 10:
        errors['xml_data'] = 'Invalid XML data'
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }
