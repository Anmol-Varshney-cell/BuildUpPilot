#!/usr/bin/env python3
"""
Test script for secure authentication system
Tests: signup, login, Aadhaar verification, MFA
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5002"
DEMO_OTP = "123456"
DEMO_MFA = "123456"

class SecureAuthTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
    
    def log_result(self, test_name, success, message):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
    
    def test_student_signup(self):
        """Test student signup with Aadhaar verification"""
        print("\n=== Testing Student Signup ===")
        
        # Step 1: Basic signup
        signup_data = {
            'name': 'Test Student',
            'email': 'teststudent@example.com',
            'password': 'testpass123',
            'mobile': '9876543210',
            'role': 'student'
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/signup_basic", 
                                   json=signup_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("Student Basic Signup", True, 
                                 f"User ID: {data.get('user_id')}")
                    self.student_user_id = data.get('user_id')
                    return self.test_student_aadhaar_verification()
                else:
                    self.log_result("Student Basic Signup", False, 
                                 data.get('message', 'Unknown error'))
            else:
                self.log_result("Student Basic Signup", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Student Basic Signup", False, str(e))
        
        return False
    
    def test_student_aadhaar_verification(self):
        """Test Aadhaar verification for student"""
        print("\n=== Testing Student Aadhaar Verification ===")
        
        # Step 2: Send OTP
        otp_data = {
            'aadhaar_number': '123456789012',
            'user_id': self.student_user_id
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/send_aadhaar_otp", 
                                   json=otp_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("Send Aadhaar OTP", True, "OTP sent successfully")
                    return self.test_verify_aadhaar_otp()
                else:
                    self.log_result("Send Aadhaar OTP", False, 
                                 data.get('message', 'Unknown error'))
            else:
                self.log_result("Send Aadhaar OTP", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Send Aadhaar OTP", False, str(e))
        
        return False
    
    def test_verify_aadhaar_otp(self):
        """Test Aadhaar OTP verification"""
        print("\n=== Testing Aadhaar OTP Verification ===")
        
        verify_data = {
            'aadhaar_number': '123456789012',
            'otp': DEMO_OTP,
            'request_id': 'test_request_id',
            'user_id': self.student_user_id
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/verify_aadhaar_otp", 
                                   json=verify_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("Verify Aadhaar OTP", True, 
                                 "Aadhaar verified successfully")
                    return self.test_complete_signup()
                else:
                    self.log_result("Verify Aadhaar OTP", False, 
                                 data.get('message', 'Unknown error'))
            else:
                self.log_result("Verify Aadhaar OTP", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Verify Aadhaar OTP", False, str(e))
        
        return False
    
    def test_complete_signup(self):
        """Test complete signup"""
        print("\n=== Testing Complete Signup ===")
        
        complete_data = {
            'user_id': self.student_user_id
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/complete-signup", 
                                   json=complete_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("Complete Signup", True, 
                                 "Account activated successfully")
                    return True
                else:
                    self.log_result("Complete Signup", False, 
                                 data.get('message', 'Unknown error'))
            else:
                self.log_result("Complete Signup", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Complete Signup", False, str(e))
        
        return False
    
    def test_recruiter_signup(self):
        """Test recruiter signup with Company ID verification"""
        print("\n=== Testing Recruiter Signup ===")
        
        # Step 1: Basic signup
        signup_data = {
            'name': 'Test Recruiter',
            'email': 'testrecruiter@example.com',
            'password': 'testpass123',
            'mobile': '9876543211',
            'role': 'recruiter'
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/signup_basic", 
                                   json=signup_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("Recruiter Basic Signup", True, 
                                 f"User ID: {data.get('user_id')}")
                    self.recruiter_user_id = data.get('user_id')
                    return self.test_recruiter_aadhaar_verification()
                else:
                    self.log_result("Recruiter Basic Signup", False, 
                                 data.get('message', 'Unknown error'))
            else:
                self.log_result("Recruiter Basic Signup", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Recruiter Basic Signup", False, str(e))
        
        return False
    
    def test_recruiter_aadhaar_verification(self):
        """Test Aadhaar verification for recruiter"""
        print("\n=== Testing Recruiter Aadhaar Verification ===")
        
        # Use XML verification for recruiter
        xml_data = {
            'xml_data': '''<?xml version="1.0" encoding="UTF-8"?>
<UidData>
    <Poi>
        <Pa>Test</Pa>
        <City>Test City</City>
        <State>Test State</State>
        <Pin>123456</Pin>
    </Poi>
    <Pht>123456789012</Pht>
</UidData>''',
            'user_id': self.recruiter_user_id
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/verify_aadhaar_xml", 
                                   json=xml_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("Recruiter Aadhaar XML", True, 
                                 "Aadhaar verified via XML")
                    return self.test_company_id_verification()
                else:
                    self.log_result("Recruiter Aadhaar XML", False, 
                                 data.get('message', 'Unknown error'))
            else:
                self.log_result("Recruiter Aadhaar XML", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Recruiter Aadhaar XML", False, str(e))
        
        return False
    
    def test_company_id_verification(self):
        """Test Company ID verification"""
        print("\n=== Testing Company ID Verification ===")
        
        company_data = {
            'user_id': self.recruiter_user_id,
            'company_id': 'COMP123456'
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/verify_company_id", 
                                   data=company_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_result("Company ID Verification", True, 
                                 "Company ID verified successfully")
                    return self.test_complete_signup()
                else:
                    self.log_result("Company ID Verification", False, 
                                 data.get('message', 'Unknown error'))
            else:
                self.log_result("Company ID Verification", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Company ID Verification", False, str(e))
        
        return False
    
    def test_admin_login(self):
        """Test admin login with MFA"""
        print("\n=== Testing Admin Login ===")
        
        # Step 1: Initial login
        login_data = {
            'email': 'admin@buildup.com',
            'password': 'admin123'
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", 
                                   data=login_data)
            
            if response.status_code == 200:
                # Check if redirected to MFA page
                if 'mfa' in response.url:
                    self.log_result("Admin Login Redirect", True, 
                                 "Redirected to MFA page")
                    return self.test_mfa_verification()
                else:
                    self.log_result("Admin Login", True, "Login successful (demo mode)")
                    return True
            else:
                self.log_result("Admin Login", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Admin Login", False, str(e))
        
        return False
    
    def test_mfa_verification(self):
        """Test MFA verification"""
        print("\n=== Testing MFA Verification ===")
        
        # Get MFA page
        try:
            response = self.session.get(f"{BASE_URL}/auth/mfa")
            
            if response.status_code == 200:
                self.log_result("MFA Page Access", True, "MFA page loaded")
                
                # Submit MFA code
                mfa_data = {
                    'mfa_code': DEMO_MFA
                }
                
                response = self.session.post(f"{BASE_URL}/auth/mfa", 
                                        data=mfa_data)
                
                if response.status_code == 200:
                    if 'dashboard' in response.url:
                        self.log_result("MFA Verification", True, 
                                     "MFA verification successful")
                        return True
                    else:
                        self.log_result("MFA Verification", False, 
                                     "MFA verification failed")
                else:
                    self.log_result("MFA Verification", False, 
                                 f"HTTP {response.status_code}")
            else:
                self.log_result("MFA Page Access", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("MFA Verification", False, str(e))
        
        return False
    
    def test_existing_user_login(self):
        """Test existing user login"""
        print("\n=== Testing Existing User Login ===")
        
        login_data = {
            'email': 'student@buildup.com',
            'password': 'student123'
        }
        
        try:
            response = self.session.post(f"{BASE_URL}/auth/login", 
                                   data=login_data)
            
            if response.status_code == 200:
                if 'dashboard' in response.url:
                    self.log_result("Student Login", True, 
                                 "Login successful")
                    return True
                else:
                    self.log_result("Student Login", False, 
                                 "Login failed - redirected")
            else:
                self.log_result("Student Login", False, 
                             f"HTTP {response.status_code}")
        except Exception as e:
            self.log_result("Student Login", False, str(e))
        
        return False
    
    def run_all_tests(self):
        """Run all authentication tests"""
        print("🚀 Starting Secure Authentication Tests")
        print("=" * 50)
        
        # Test student flow
        self.test_student_signup()
        
        # Test recruiter flow
        self.test_recruiter_signup()
        
        # Test admin login
        self.test_admin_login()
        
        # Test existing user login
        self.test_existing_user_login()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        print("\n🔗 Test URLs:")
        print(f"Secure Signup: {BASE_URL}/auth/signup_secure")
        print(f"MFA Page: {BASE_URL}/auth/mfa")
        print(f"Login: {BASE_URL}/auth/login")

if __name__ == "__main__":
    tester = SecureAuthTester()
    tester.run_all_tests()
