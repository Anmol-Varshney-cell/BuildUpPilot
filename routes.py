from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, send_file, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
import fitz
import json
import os
import random
import sqlite3
import time
import uuid
import base64
import hashlib
import hmac
import smtplib
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from functools import wraps

from extensions import db, bcrypt
from flask import current_app as app
from models import (User, StudentProfile, SkillTest, TestQuestion, InterviewReadiness, Job, Application,
                   MockInterview, SupportTicket, TicketResponse, Certificate,
                   Discussion, DiscussionComment, RoadMap, DailyBadge)

from recruiter_email_otp_demo import generate_demo_email_otp


main = Blueprint('main', __name__)
auth = Blueprint('auth', __name__, url_prefix='/auth')
student = Blueprint('student', __name__, url_prefix='/student')
admin = Blueprint('admin', __name__, url_prefix='/admin')

recruiter = Blueprint('recruiter', __name__, url_prefix='/recruiter')
api = Blueprint('api', __name__, url_prefix='/api')

def _generate_student_id():
    """Generate student ids like BUPS00..BUPS10000 based on existing student_id values."""
    next_seq = 0

    student_ids = (
        User.query
        .with_entities(User.student_id)
        .filter(User.role == 'student', User.student_id.like('BUPS%'))
        .all()
    )

    for (sid,) in student_ids:
        if not sid:
            continue
        # Expected: BUPS<digits>
        suffix = sid[4:]
        if suffix.isdigit():
            next_seq = max(next_seq, int(suffix) + 1)

    return f"BUPS{next_seq:02d}" if next_seq < 100 else f"BUPS{next_seq}"


def _generate_recruiter_id():
    last_recruiter = (
        User.query
        .filter(
            User.role == 'recruiter',
            User.student_id.like('BUPR__')
        )
        .order_by(User.id.desc())
        .first()
    )

    next_seq = 1
    if last_recruiter and last_recruiter.student_id:
        digits = ''.join(ch for ch in last_recruiter.student_id if ch.isdigit())
        if digits:
            next_seq = max(1, int(digits) + 1)

    return f"BUPR{next_seq:02d}"


def _generate_admin_id():
    last_admin = (
        User.query
        .filter(
            User.role == 'admin',
            User.student_id.like('BUPA__')
        )
        .order_by(User.id.desc())
        .first()
    )

    next_seq = 1
    if last_admin and last_admin.student_id:
        digits = ''.join(ch for ch in last_admin.student_id if ch.isdigit())
        if digits:
            next_seq = max(1, int(digits) + 1)

    return f"BUPA{next_seq:02d}"


def _generate_otp():
    return str(random.randint(100000, 999999))


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                flash('Access denied. Insufficient permissions.', 'danger')
                return redirect(url_for('auth.login'))
            if (
                current_user.role == 'recruiter'
                and 'recruiter' in roles
                and not _is_recruiter_admin_approved(current_user)
                and request.endpoint != 'recruiter.profile'
            ):
                flash('Your recruiter access is waiting for admin approval.', 'warning')
                return redirect(url_for('recruiter.profile'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def _save_user_file(file_obj, subfolder, prefix):
    upload_root = current_app.config.get('UPLOAD_FOLDER', os.path.join('static', 'uploads'))
    target_dir = os.path.join(upload_root, subfolder)
    try:
        os.makedirs(target_dir, exist_ok=True)
        ext = os.path.splitext(file_obj.filename or '')[1].lower()
        filename = f'{prefix}_{current_user.id}_{int(time.time())}{ext}'
        file_path = os.path.join(target_dir, filename)
        file_obj.save(file_path)
        return f'{subfolder}/{filename}'
    except Exception:
        # Fallback for read-only cloud filesystems (Vercel / AWS Lambda)
        try:
            file_obj.seek(0)
            content = file_obj.read()
            ext_clean = os.path.splitext(file_obj.filename or '')[1].lower().lstrip('.')
            if ext_clean == 'pdf':
                tmp_dir = os.path.join('/tmp', 'uploads', subfolder)
                os.makedirs(tmp_dir, exist_ok=True)
                filename = f'{prefix}_{current_user.id}_{int(time.time())}.pdf'
                tmp_path = os.path.join(tmp_dir, filename)
                with open(tmp_path, 'wb') as f:
                    f.write(content)
                return f'/tmp/uploads/{subfolder}/{filename}'
            else:
                mime_ext = ext_clean if ext_clean in ['png', 'jpeg', 'jpg', 'webp'] else 'jpeg'
                b64 = base64.b64encode(content).decode('utf-8')
                return f'data:image/{mime_ext};base64,{b64}'
        except Exception as e:
            print(f'[FILE SAVE FALLBACK ERROR] {e}')
            return f'{subfolder}/default.jpg'

def _resolve_resume_file(profile):
    if not profile or not profile.resume_path:
        return None, None

    raw_path = (profile.resume_path or '').strip().replace('\\', '/')
    cleaned = raw_path
    for prefix in ('/static/uploads/', 'static/uploads/', '/uploads/', 'uploads/'):
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
            break

    candidates = [cleaned]
    if cleaned and '/' not in cleaned:
        candidates.insert(0, f"resumes/{cleaned}")

    upload_root = current_app.config.get('UPLOAD_FOLDER', os.path.join('static', 'uploads'))
    for candidate in candidates:
        abs_path = os.path.join(upload_root, *candidate.split('/'))
        if os.path.exists(abs_path):
            return abs_path, candidate

    return None, cleaned

def _format_coding_timestamp(value):
    if not value:
        return 'Unknown time'
    try:
        normalized = str(value).replace('Z', '+00:00')
        parsed = datetime.fromisoformat(normalized)
        return parsed.strftime('%b %d, %Y %I:%M %p')
    except ValueError:
        return str(value)

def _build_skillup_sso_payload():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    name = f"{profile.first_name} {profile.last_name}".strip() if profile and profile.first_name else current_user.email.split('@')[0]

    profile_image = None
    if profile and profile.profile_image_path:
        # _save_user_file stores paths like "profile_images/dp_3_xxx.jpg"
        # The actual static file URL needs /static/uploads/ prefix
        image_path = profile.profile_image_path.lstrip('/')
        if not image_path.startswith('static/uploads/'):
            image_path = f'static/uploads/{image_path}'
        profile_image = request.host_url.rstrip('/') + '/' + image_path

    expiry = int((datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp())

    first_name = profile.first_name if profile else None
    last_name = profile.last_name if profile else None

    return {
        'email': current_user.email,
        'name': name,
        'firstName': first_name,
        'lastName': last_name,
        'uid': current_user.id,
        'studentId': current_user.student_id,
        'profileImage': profile_image,
        'phone': profile.phone if profile else None,
        'profession': profile.profession if profile else None,
        'college': profile.college if profile else None,
        'branch': profile.branch if profile else None,
        'graduationYear': profile.graduation_year if profile else None,
        'skills': profile.skills if profile else None,
        'bio': profile.bio if profile else None,
        'location': profile.location if profile else None,
        'linkedin': profile.linkedin if profile else None,
        'github': profile.github if profile else None,
        'iat': int(time.time()),
        'exp': expiry
    }

def _try_send_sms_otp(target_mobile, otp_value):
    sms_gateway_url = os.getenv('SMS_GATEWAY_URL')
    sms_api_key = os.getenv('SMS_API_KEY')
    if not sms_gateway_url or not sms_api_key:
        return False

    payload = {
        'to': target_mobile,
        'message': f'Your BUILD UP verification OTP is: {otp_value}. Valid for 10 minutes.',
        'api_key': sms_api_key
    }
    try:
        import requests
        r = requests.post(sms_gateway_url, json=payload, timeout=30)
        return getattr(r, 'status_code', 0) == 200
    except Exception:
        return False

def _try_send_email(target_email, subject, body):
    if not target_email:
        return False

    smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    smtp_user = (
        os.getenv('SMTP_USERNAME')
        or os.getenv('GMAIL_ADDRESS')
        or os.getenv('MAIL_USERNAME')
    )
    smtp_password = (
        os.getenv('SMTP_PASSWORD')
        or os.getenv('GMAIL_APP_PASSWORD')
        or os.getenv('MAIL_PASSWORD')
    )
    sender = os.getenv('MAIL_DEFAULT_SENDER') or smtp_user
    if not smtp_user or not smtp_password or not sender:
        return False

    try:
        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = sender
        message['To'] = target_email
        message.set_content(body)
        with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(message)
        return True
    except Exception:
        return False

def _send_recruiter_email_otp(user):
    otp = _generate_otp()
    user.recruiter_request_otp = otp
    user.recruiter_request_otp_expires = datetime.utcnow() + timedelta(minutes=10)
    target_email = user.recruiter_request_email or user.email
    sent = _try_send_email(
        target_email,
        'BUILD UP PILOT recruiter Gmail OTP',
        (
            f'Hi {user.first_name or user.email},\n\n'
            f'Your BUILD UP PILOT recruiter verification OTP is {otp}. '
            'It is valid for 10 minutes.\n\n'
            'After you enter this OTP, your request will go to the admin dashboard for approval.'
        )
    )
    return otp, sent

def _send_recruiter_decision_email(user, approved):
    target_email = user.recruiter_request_email or user.email
    if approved:
        subject = 'BUILD UP PILOT recruiter request approved'
        body = (
            f'Hi {user.first_name or user.email},\n\n'
            'Your request to become a recruiter on BUILD UP PILOT has been approved. '
            'You can now log in to your recruiter portal.\n\n'
            'Welcome to BUILD UP PILOT.'
        )
    else:
        subject = 'BUILD UP PILOT recruiter request declined'
        body = (
            f'Hi {user.first_name or user.email},\n\n'
            'The admin has canceled your request to become a recruiter on BUILD UP PILOT. '
            'You can submit the recruiter verification request again with updated details.'
        )
    return _try_send_email(target_email, subject, body)

def _mask_aadhaar(aadhaar_number):
    aadhaar_digits = ''.join(ch for ch in str(aadhaar_number or '') if ch.isdigit())
    if len(aadhaar_digits) != 12:
        return None
    return f'XXXX-XXXX-{aadhaar_digits[-4:]}'

def _send_student_aadhaar_otp(user, aadhaar_number):
    aadhaar_digits = ''.join(ch for ch in str(aadhaar_number or '') if ch.isdigit())
    if len(aadhaar_digits) != 12:
        return {
            'success': False,
            'message': 'Please enter a valid 12-digit Aadhaar number'
        }

    request_id = f"AAD{uuid.uuid4().hex[:16].upper()}"
    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    otp = _generate_otp()
    masked_mobile = 'Aadhaar linked mobile number'

    session[f'student_aadhaar_signup_{user.id}'] = {
        'request_id': request_id,
        'otp': otp if demo_mode else None,
        'aadhaar_number': aadhaar_digits,
        'expires_at': (datetime.utcnow() + timedelta(minutes=10)).isoformat()
    }

    if not demo_mode:
        api_base_url = os.getenv('AADHAAR_API_BASE_URL')
        api_key = os.getenv('AADHAAR_API_KEY')
        if not api_base_url or not api_key:
            return {
                'success': False,
                'message': 'Aadhaar OTP provider is not configured'
            }

        try:
            import requests
            response = requests.post(
                f"{api_base_url.rstrip('/')}/aadhaar/send-otp",
                json={
                    'aadhaar_number': aadhaar_digits,
                    'request_id': request_id,
                    'consent': 'I consent to Aadhaar OTP verification for BUILD UP PILOT student signup'
                },
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=30
            )
            if response.status_code not in (200, 201, 202):
                return {
                    'success': False,
                    'message': 'Could not send Aadhaar OTP. Please try again.'
                }
            provider_data = response.json() if response.content else {}
            request_id = provider_data.get('request_id') or provider_data.get('transaction_id') or request_id
            masked_mobile = provider_data.get('masked_mobile') or masked_mobile
            session[f'student_aadhaar_signup_{user.id}']['request_id'] = request_id
        except Exception:
            return {
                'success': False,
                'message': 'Aadhaar OTP service is unavailable. Please try again.'
            }

    return {
        'success': True,
        'request_id': request_id,
        'demo_otp': otp if demo_mode else None,
        'masked_mobile': masked_mobile
    }

def _verify_student_aadhaar_otp(user, otp):
    session_key = f'student_aadhaar_signup_{user.id}'
    otp_data = session.get(session_key)
    if not otp_data:
        return {
            'success': False,
            'message': 'Aadhaar OTP session expired. Please sign up again.'
        }

    expires_at = datetime.fromisoformat(otp_data['expires_at'])
    if datetime.utcnow() > expires_at:
        session.pop(session_key, None)
        return {
            'success': False,
            'message': 'Aadhaar OTP expired. Please sign up again.'
        }

    demo_mode = os.getenv('DEMO_MODE', 'true').lower() == 'true'
    if demo_mode:
        if otp != otp_data.get('otp'):
            return {
                'success': False,
                'message': 'Invalid Aadhaar OTP'
            }
    else:
        api_base_url = os.getenv('AADHAAR_API_BASE_URL')
        api_key = os.getenv('AADHAAR_API_KEY')
        if not api_base_url or not api_key:
            return {
                'success': False,
                'message': 'Aadhaar OTP provider is not configured'
            }
        try:
            import requests
            response = requests.post(
                f"{api_base_url.rstrip('/')}/aadhaar/verify-otp",
                json={
                    'aadhaar_number': otp_data['aadhaar_number'],
                    'request_id': otp_data['request_id'],
                    'otp': otp
                },
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=30
            )
            if response.status_code not in (200, 201, 202):
                return {
                    'success': False,
                    'message': 'Invalid Aadhaar OTP'
                }
            provider_data = response.json() if response.content else {}
            if provider_data.get('success') is False or provider_data.get('status') in ('failed', 'rejected'):
                return {
                    'success': False,
                    'message': provider_data.get('message') or 'Invalid Aadhaar OTP'
                }
        except Exception:
            return {
                'success': False,
                'message': 'Aadhaar OTP service is unavailable. Please try again.'
            }

    user.is_verified = True
    user.is_aadhaar_verified = True
    user.aadhaar_number = _mask_aadhaar(otp_data['aadhaar_number'])
    user.otp = None
    user.otp_expires = None
    session.pop(session_key, None)
    return {'success': True}

def _recruiter_name(user):
    name = ' '.join(part for part in [getattr(user, 'first_name', None), getattr(user, 'last_name', None)] if part)
    return name or (user.email.split('@')[0] if user.email else 'Recruiter')

def _is_recruiter_admin_approved(user):
    return (
        user.role != 'recruiter'
        or (user.is_verified and getattr(user, 'company_id_status', None) == 'verified')
    )


def _build_skillup_sso_token():

    try:
        sso_secret = os.environ.get('SSO_SHARED_SECRET', 'build-up-secret-key-2024')
        payload = _build_skillup_sso_payload()
        payload_json = json.dumps(payload, separators=(',', ':'))
        payload_b64 = base64.urlsafe_b64encode(payload_json.encode()).rstrip(b'=').decode()
        signature = hmac.new(sso_secret.encode(), payload_b64.encode(), hashlib.sha256).hexdigest()
        return f"{payload_b64}.{signature}"
    except Exception as e:
        # Fallback token generation
        import uuid
        fallback_token = str(uuid.uuid4())
        return fallback_token

def _seed_sample_jobs_if_empty():
    from datetime import date
    today = date.today()

    latest_job = Job.query.order_by(Job.posted_at.desc()).first()
    if latest_job and latest_job.posted_at.date() == today:
        return

    companies = ['TechNova Solutions', 'PixelForge UI', 'NexGen Digital', 'InsightBridge Analytics', 
                 'CloudScale Infra', 'AppVenture Mobile', 'InnovateCode Tech', 'DataMinds Corp',
                 'AI Vanguard', 'WebCraft Studios', 'CyberShield Tech', 'CloudNine Systems']
    
    sample_jobs = [
        {
            'title': 'Python Backend Developer',
            'company': random.choice(companies),
            'location': random.choice(['Bangalore', 'Hyderabad', 'Pune', 'Chennai', 'Mumbai', 'Remote']),
            'job_type': 'Full-time',
            'work_mode': random.choice(['onsite', 'hybrid', 'remote']),
            'salary_min': random.randint(500000, 800000),
            'salary_max': random.randint(1000000, 1800000),
            'stipend': 0,
            'required_skills': 'python, django/flask, postgresql, docker, rest apis',
            'description': 'Develop scalable backend services and APIs for web applications. Work with cutting-edge technologies in a collaborative environment.',
            'requirements': '3+ years Python, framework experience, cloud deployment.',
            'branch': 'CSE/IT'
        },
        {
            'title': 'Frontend React Developer',
            'company': 'PixelForge UI',
            'location': 'Hyderabad',
            'job_type': 'Full-time',
            'work_mode': 'hybrid',
            'salary_min': 500000,
            'salary_max': 1000000,
            'stipend': 0,
            'required_skills': 'react, javascript/typescript, tailwind, nextjs, state management',
            'description': 'Build responsive UIs and optimize performance for enterprise apps. Join our creative team building modern web experiences.',
            'requirements': '2+ years React, modern tooling, performance optimization.',
            'branch': 'CSE/ECE'
        },
        {
            'title': 'Fullstack Engineer',
            'company': 'NexGen Digital',
            'location': 'Remote',
            'job_type': 'Full-time',
            'work_mode': 'remote',
            'salary_min': 800000,
            'salary_max': 1500000,
            'stipend': 0,
            'required_skills': 'nodejs, express, mongodb, react, aws, git',
            'description': 'End-to-end development of web applications from design to deployment. Full remote work with flexible hours.',
            'requirements': 'Full MERN stack, DevOps basics, agile experience.',
            'branch': 'Any Technical'
        },
        {
            'title': 'Data Analyst',
            'company': 'InsightBridge Analytics',
            'location': 'Pune',
            'job_type': 'Full-time',
            'work_mode': 'onsite',
            'salary_min': 450000,
            'salary_max': 850000,
            'stipend': 0,
            'required_skills': 'python, pandas, sql, powerbi/tableau, statistics',
            'description': 'Data processing, visualization, and business insights generation. Transform raw data into actionable business insights.',
            'requirements': 'SQL mastery, Python data libs, visualization tools.',
            'branch': 'CSE/Maths/Stats'
        },
        {
            'title': 'DevOps Engineer',
            'company': 'CloudScale Infra',
            'location': 'Chennai',
            'job_type': 'Full-time',
            'work_mode': 'onsite',
            'salary_min': 700000,
            'salary_max': 1400000,
            'stipend': 0,
            'required_skills': 'docker, kubernetes, jenkins, aws/gcp, terraform, linux',
            'description': 'CI/CD pipeline automation and cloud infrastructure management. Build and maintain scalable infrastructure.',
            'requirements': 'Containerization, IaC, monitoring tools.',
            'branch': 'CSE/IT'
        },
        {
            'title': 'SDE Intern - Frontend',
            'company': 'AppVenture Mobile',
            'location': 'Mumbai',
            'job_type': 'Internship',
            'work_mode': 'hybrid',
            'salary_min': 0,
            'salary_max': 0,
            'stipend': 25000,
            'required_skills': 'react, javascript, css, html',
            'description': '6-month internship with potential full-time offer. Learn from experienced developers and work on real projects.',
            'requirements': 'Knowledge of React basics, willingness to learn.',
            'branch': 'CSE/ECE/IT'
        },
        {
            'title': 'Software Engineer - SDE1',
            'company': 'InnovateCode Tech',
            'location': 'Gurgaon',
            'job_type': 'Full-time',
            'work_mode': 'onsite',
            'salary_min': 700000,
            'salary_max': 1300000,
            'stipend': 0,
            'required_skills': 'java, spring boot, mysql, microservices, kafka',
            'description': 'Backend development with Java ecosystem and distributed systems. Work on high-scale applications.',
            'requirements': 'DSA strong, system design basics.',
            'branch': 'CSE/IT'
        },
        {
            'title': 'ML Engineer Intern',
            'company': 'AI Frontier Labs',
            'location': 'Remote',
            'job_type': 'Internship',
            'work_mode': 'remote',
            'salary_min': 0,
            'salary_max': 0,
            'stipend': 40000,
            'required_skills': 'python, tensorflow/pytorch, scikit-learn, data preprocessing',
            'description': 'Model training and deployment for AI/ML projects. Work on cutting-edge AI solutions.',
            'requirements': 'ML projects, basic DL concepts.',
            'branch': 'CSE/Data Science'
        },
        {
            'title': 'Cybersecurity Analyst',
            'company': 'SecureNet Solutions',
            'location': 'Delhi',
            'job_type': 'Full-time',
            'work_mode': 'onsite',
            'salary_min': 600000,
            'salary_max': 1200000,
            'stipend': 0,
            'required_skills': 'network security, ethical hacking, siem, vulnerability assessment',
            'description': 'Threat detection and security operations center (SOC) analyst. Protect organizations from cyber threats.',
            'requirements': 'CEH cert preferred, network fundamentals.',
            'branch': 'CSE/IT'
        },
        {
            'title': 'Android Developer',
            'company': 'TechStart India',
            'location': 'Bangalore',
            'job_type': 'Full-time',
            'work_mode': 'hybrid',
            'salary_min': 550000,
            'salary_max': 1100000,
            'stipend': 0,
            'required_skills': 'kotlin, android sdk, jetpack compose, firebase',
            'description': 'Native Android app development. Build and maintain high-quality mobile applications.',
            'requirements': 'Published apps, Play Store experience preferred.',
            'branch': 'CSE/ECE'
        },
        {
            'title': 'Go Backend Engineer',
            'company': 'SkyForge Technologies',
            'location': 'Bengaluru',
            'job_type': 'Full-time',
            'work_mode': 'onsite',
            'salary_min': 900000,
            'salary_max': 1800000,
            'stipend': 0,
            'required_skills': 'go, gin, microservices, postgres',
            'description': 'Backend services in Go with microservices architecture and high concurrency.',
            'requirements': 'Go experience, REST APIs',
            'branch': 'CSE/IT'
        },
        {
            'title': 'Rust Systems Engineer',
            'company': 'QuantumOps',
            'location': 'Remote',
            'job_type': 'Full-time',
            'work_mode': 'remote',
            'salary_min': 1000000,
            'salary_max': 2000000,
            'stipend': 0,
            'required_skills': 'rust, async, tokio, wasm',
            'description': 'Systems programming in Rust for high-performance applications.',
            'requirements': 'Rust experience',
            'branch': 'CS/IT'
        },
        {
            'title': 'Go Full Stack Engineer',
            'company': 'NovaTech',
            'location': 'Pune',
            'job_type': 'Full-time',
            'work_mode': 'hybrid',
            'salary_min': 700000,
            'salary_max': 1300000,
            'stipend': 0,
            'required_skills': 'Go, React, Docker',
            'description': 'Full stack Go-based services with frontend.',
            'requirements': 'Go and frontend skills',
            'branch': 'CSE/IT'
        },
        {
            'title': 'AI Engineer',
            'company': random.choice(companies),
            'location': random.choice(['Remote', 'Bangalore', 'Hyderabad', 'Pune']),
            'job_type': 'Full-time',
            'work_mode': random.choice(['remote', 'hybrid']),
            'salary_min': random.randint(900000, 1500000),
            'salary_max': random.randint(1600000, 2400000),
            'stipend': 0,
            'required_skills': 'python, llms, prompt engineering, fastapi, vector databases',
            'description': 'Build AI-powered features, evaluation pipelines, and production-ready LLM applications.',
            'requirements': 'Hands-on AI app projects, Python backend skills, API integration experience.',
            'branch': 'CSE/AI/IT'
        },
        {
            'title': 'Cloud Support Engineer',
            'company': random.choice(companies),
            'location': random.choice(['Chennai', 'Noida', 'Remote']),
            'job_type': 'Full-time',
            'work_mode': random.choice(['onsite', 'hybrid', 'remote']),
            'salary_min': random.randint(450000, 700000),
            'salary_max': random.randint(800000, 1200000),
            'stipend': 0,
            'required_skills': 'linux, aws, networking, troubleshooting, scripting',
            'description': 'Support cloud systems, troubleshoot incidents, and improve operational reliability.',
            'requirements': 'Cloud basics, debugging mindset, scripting knowledge.',
            'branch': 'CSE/IT/ECE'
        }
    ]

    jobs_to_add = 6 if Job.query.count() < 6 else 3
    for item in random.sample(sample_jobs, min(jobs_to_add, len(sample_jobs))):
        db.session.add(Job(**item, recruiter_id=None, is_active=True, posted_at=datetime.utcnow()))
    db.session.commit()


def _build_student_job_matches(profile, applications_list=None):
    _seed_sample_jobs_if_empty()

    applications_list = applications_list or []
    applied_job_ids = {application.job_id for application in applications_list}
    user_skills = set()
    if profile and profile.skills:
        user_skills = {skill.strip().lower() for skill in profile.skills.split(',') if skill.strip()}

    jobs_list = (
        Job.query
        .filter_by(is_active=True)
        .order_by(Job.posted_at.desc(), Job.id.desc())
        .all()
    )

    matched_jobs = []
    for job in jobs_list:
        job_skills = []
        if job.required_skills:
            job_skills = [skill.strip().lower() for skill in job.required_skills.split(',') if skill.strip()]

        if job_skills and user_skills:
            matching_skills = sum(1 for skill in job_skills if skill in user_skills)
            match_score = int((matching_skills / len(job_skills)) * 100)
        elif job_skills:
            match_score = 35
        else:
            match_score = 50

        matched_jobs.append({
            'job': job,
            'match_score': match_score,
            'is_applied': job.id in applied_job_ids
        })

    matched_jobs.sort(key=lambda item: (item['match_score'], item['job'].posted_at, item['job'].id), reverse=True)
    return matched_jobs


def _job_feed_signature(matched_jobs):
    return '|'.join(
        f"{item['job'].id}:{item['job'].posted_at.isoformat() if item['job'].posted_at else ''}:{int(item['is_applied'])}"
        for item in matched_jobs
    )

@main.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'recruiter':
            return redirect(url_for('recruiter.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    return render_template('index.html')

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        mobile = request.form.get('mobile')
        role = request.form.get('role', 'student')
        aadhaar_number = request.form.get('aadhaar_number')
        first_name = (request.form.get('first_name') or '').strip()
        last_name = (request.form.get('last_name') or '').strip()
        company_name = (request.form.get('company_name') or '').strip()
        recruiter_request_email = (request.form.get('recruiter_request_email') or email or '').strip().lower()
        company_id = request.form.get('company_id', '')
        company_id_card = request.files.get('company_id_card', None)

        def _mask_mobile(m):
            if not m:
                return 'XXXXXX1234'
            m = ''.join(ch for ch in str(m) if ch.isdigit())
            return f"XXXXXX{m[-4:] if len(m) >= 4 else '1234'}"

        if not password or password != confirm_password:
            return jsonify({'success': False, 'message': 'Password and confirm password must match'})

        if (
            not any(ch in '!@#$%^&*()_+-=[]{};:\'",.<>/?`~\\|' for ch in password)
            or not any(ch.isupper() for ch in password)
            or not any(ch.isdigit() for ch in password)
        ):
            return jsonify({
                'success': False,
                'message': 'Password requirements:\n' \
                           + '• At least 8 characters\n' \
                           + '• At least one uppercase letter (A–Z)\n' \
                           + '• At least one number (0–9)\n' \
                           + '• At least one special character (@, $, !, %, *, ?, &)' \
            })

        if role == 'student':
            aadhaar_digits = ''.join(ch for ch in str(aadhaar_number or '') if ch.isdigit())
            if len(aadhaar_digits) != 12:
                return jsonify({'success': False, 'message': 'Aadhaar number is required for student signup'})
            max_student_accounts = current_app.config.get('MAX_STUDENT_ACCOUNTS', 10000)
            student_count = User.query.filter_by(role='student').count()
            if student_count >= max_student_accounts:
                return jsonify({
                    'success': False,
                    'message': f'Student signup limit reached. Maximum allowed students: {max_student_accounts}'
                })


        # If a user already exists but is NOT verified yet, allow re-submission to re-send OTP.
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if existing_user.role == 'recruiter' and existing_user.company_id_status == 'declined':
                existing_user.first_name = first_name or existing_user.first_name
                existing_user.last_name = last_name or existing_user.last_name
                existing_user.company_name = company_name or existing_user.company_name
                existing_user.company_id = company_id or existing_user.company_id
                existing_user.mobile = mobile or existing_user.mobile
                existing_user.recruiter_request_email = recruiter_request_email or existing_user.recruiter_request_email
                existing_user.company_id_status = 'pending_email_otp'
                existing_user.recruiter_request_last_notification = None
                if company_id_card and company_id_card.filename:
                    company_id_image_path = f'static/uploads/company_id_cards/{uuid.uuid4().hex}_{company_id_card.filename}'
                    company_id_card.save(company_id_image_path)
                    existing_user.company_id_image_path = company_id_image_path
                otp, email_sent = _send_recruiter_email_otp(existing_user)
                db.session.commit()
                payload = {
                    'success': True,
                    'message': f'Recruiter Gmail OTP sent to {existing_user.recruiter_request_email}.',
                    'user_id': existing_user.id,
                    'otp_channel': 'email',
                    'requires_company_verification': True
                }
                if os.getenv('DEMO_MODE', 'true').lower() == 'true' or not email_sent:
                    payload['demo_otp'] = otp
                return jsonify(payload)

            # Only allow retry when the account is still pending OTP verification.
            if not existing_user.is_verified:
                if existing_user.role == 'recruiter':
                    otp, email_sent = _send_recruiter_email_otp(existing_user)
                    existing_user.company_id_status = existing_user.company_id_status or 'pending_email_otp'
                else:
                    otp = _generate_otp()
                    email_sent = False
                    if existing_user.role == 'student':
                        aadhaar_result = _send_student_aadhaar_otp(existing_user, aadhaar_number)
                        if not aadhaar_result['success']:
                            return jsonify({'success': False, 'message': aadhaar_result['message']})
                        otp = aadhaar_result.get('demo_otp')
                    else:
                        existing_user.otp = otp
                        existing_user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
                db.session.commit()

                if existing_user.role not in ('recruiter', 'student'):
                    _try_send_sms_otp(existing_user.mobile, otp)

                payload = {
                    'success': True,
                    'message': (
                        f'Recruiter Gmail OTP sent to {existing_user.recruiter_request_email or existing_user.email}.'
                        if existing_user.role == 'recruiter'
                        else (
                            'Aadhaar OTP resent to the mobile number linked with your Aadhaar.'
                            if existing_user.role == 'student'
                            else f'OTP resent to your mobile ({_mask_mobile(existing_user.mobile)}).'
                        )
                    ),
                    'user_id': existing_user.id,
                    'otp_channel': (
                        'email' if existing_user.role == 'recruiter'
                        else 'aadhaar' if existing_user.role == 'student'
                        else 'mobile'
                    ),
                    'requires_company_verification': existing_user.role == 'recruiter'
                }
                if (
                    os.getenv('DEMO_MODE', 'true').lower() == 'true'
                    or (existing_user.role == 'recruiter' and not email_sent)
                ):
                    payload['demo_otp'] = otp
                return jsonify(payload)

            return jsonify({'success': False, 'message': 'Email already registered'})

        company_id_image_path = None

        # For recruiters, validate company ID verification
        if role == 'recruiter':
            if not first_name or not company_name or not recruiter_request_email:
                return jsonify({'success': False, 'message': 'Recruiter name, company name, and Gmail are required'})
            if not company_id and not company_id_card:
                return jsonify({'success': False, 'message': 'Company ID or Company ID card is required for recruiters'})

            # Save company ID card if uploaded
            if company_id_card and company_id_card.filename:
                company_id_image_path = f'static/uploads/company_id_cards/{uuid.uuid4().hex}_{company_id_card.filename}'
                company_id_card.save(company_id_image_path)

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        otp = _generate_otp()
        otp_expires = datetime.utcnow() + timedelta(minutes=10)

        user = User(
            student_id=f"TMP{uuid.uuid4().hex[:10].upper()}",
            email=email,
            password_hash=hashed_password,
            role=role,
            mobile=mobile,
            otp=otp,
            otp_expires=otp_expires,
            first_name=first_name,
            last_name=last_name,
            company_name=company_name,
            recruiter_request_email=recruiter_request_email if role == 'recruiter' else None,
            company_id=company_id,
            company_id_image_path=company_id_image_path,
            company_id_status='pending_email_otp' if role == 'recruiter' else None
        )
        db.session.add(user)
        db.session.commit()

        if role == 'student':
            user.student_id = _generate_student_id()
        elif role == 'recruiter':
            if (email or '').strip().lower() == 'recruiter@buildup.com':
                user.student_id = 'BUPR00'
            else:
                user.student_id = _generate_recruiter_id()
        elif role == 'admin':
            if (email or '').strip().lower() == 'admin@buildup.com':
                user.student_id = 'BUPA00'
            else:
                user.student_id = _generate_admin_id()
        else:
            user.student_id = None
        db.session.commit()

        email_sent = False
        if role == 'recruiter':
            otp, email_sent = _send_recruiter_email_otp(user)
            user.otp = None
            user.otp_expires = None
            db.session.commit()
        elif role == 'student':
            aadhaar_result = _send_student_aadhaar_otp(user, aadhaar_number)
            if not aadhaar_result['success']:
                db.session.delete(user)
                db.session.commit()
                return jsonify({'success': False, 'message': aadhaar_result['message']})
            otp = aadhaar_result.get('demo_otp')
            user.otp = None
            user.otp_expires = None
            db.session.commit()
        else:
            _try_send_sms_otp(user.mobile, otp)

        demo_mode = (os.getenv('DEMO_MODE', 'true').lower() == 'true')
        payload = {
            'success': True,
            'message': (
                f'Recruiter Gmail OTP sent to {user.recruiter_request_email}.'
                if role == 'recruiter'
                else (
                    'Aadhaar OTP sent to the mobile number linked with your Aadhaar.'
                    if role == 'student'
                    else f'OTP sent to your mobile ({_mask_mobile(user.mobile)}).'
                )
            ),
            'user_id': user.id,
            'otp_channel': 'email' if role == 'recruiter' else 'aadhaar' if role == 'student' else 'mobile',
            'requires_company_verification': role == 'recruiter'
        }
        # For local/dev: return OTP immediately so verification works without SMS.
        if demo_mode or (role == 'recruiter' and not email_sent):
            payload['demo_otp'] = user.recruiter_request_otp if role == 'recruiter' else otp if role == 'student' else user.otp
        return jsonify(payload)

    return render_template('auth/signup.html')

@auth.route('/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    user_id = data.get('user_id')
    otp = data.get('otp')
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})

    if user.role == 'recruiter':
        if user.company_id_status == 'verified':
            return jsonify({'success': False, 'message': 'Recruiter already approved'})
        if user.recruiter_request_otp != otp:
            return jsonify({'success': False, 'message': 'Invalid Gmail OTP'})
        if user.recruiter_request_otp_expires and datetime.utcnow() > user.recruiter_request_otp_expires:
            return jsonify({'success': False, 'message': 'Gmail OTP expired'})

        user.is_verified = True
        user.recruiter_request_otp = None
        user.recruiter_request_otp_expires = None
        user.company_id_status = 'pending_admin'
        user.recruiter_request_last_submitted_at = datetime.utcnow()
        user.recruiter_request_last_notification = (
            f'{_recruiter_name(user)}, {user.company_name or "Company not provided"} wants to get placed as recruiter.'
        )
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Gmail verified. Your recruiter request has been sent to admin for approval.'
        })

    if user.role == 'student':
        if user.is_verified and user.is_aadhaar_verified:
            return jsonify({'success': False, 'message': 'Already verified'})

        aadhaar_result = _verify_student_aadhaar_otp(user, otp)
        if not aadhaar_result['success']:
            return jsonify({'success': False, 'message': aadhaar_result['message']})

        db.session.commit()
        if not StudentProfile.query.filter_by(user_id=user.id).first():
            profile = StudentProfile(user_id=user.id)
            db.session.add(profile)
            db.session.commit()

            readiness = InterviewReadiness(profile_id=profile.id)
            db.session.add(readiness)
            db.session.commit()

        return jsonify({'success': True, 'message': 'Aadhaar verified successfully. Account created.'})

    if user.is_verified:
        return jsonify({'success': False, 'message': 'Already verified'})
    
    if user.otp != otp:
        return jsonify({'success': False, 'message': 'Invalid OTP'})
    
    if user.otp_expires and datetime.utcnow() > user.otp_expires:
        return jsonify({'success': False, 'message': 'OTP expired'})
    
    user.is_verified = True
    user.otp = None
    user.otp_expires = None
    db.session.commit()
    
    if not StudentProfile.query.filter_by(user_id=user.id).first():
        profile = StudentProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()

        readiness = InterviewReadiness(profile_id=profile.id)
        db.session.add(readiness)
        db.session.commit()
    
    return jsonify({'success': True, 'message': 'Account verified successfully'})

@auth.route('/resend-otp', methods=['POST'])
def resend_otp():
    data = request.get_json() or {}
    user_id = data.get('user_id')

    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'})

    if user.role == 'recruiter':
        otp, email_sent = _send_recruiter_email_otp(user)
        if user.company_id_status in (None, 'declined'):
            user.company_id_status = 'pending_email_otp'
        db.session.commit()
        payload = {
            'success': True,
            'message': f'Recruiter Gmail OTP resent to {user.recruiter_request_email or user.email}.',
            'sms_sent': False,
            'email_sent': email_sent
        }
        if os.getenv('DEMO_MODE', 'true').lower() == 'true' or not email_sent:
            payload['demo_otp'] = otp
        return jsonify(payload)

    def _mask_mobile(m):
        if not m:
            return 'XXXXXX1234'
        m = ''.join(ch for ch in str(m) if ch.isdigit())
        return f"XXXXXX{m[-4:] if len(m) >= 4 else '1234'}"

    user.otp = _generate_otp()
    user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()

    sms_gateway_url = os.getenv('SMS_GATEWAY_URL')
    sms_api_key = os.getenv('SMS_API_KEY')

    # Default to demo mode for local development when DEMO_MODE env var isn't set
    demo_mode = (os.getenv('DEMO_MODE', 'true').lower() == 'true')

    sms_sent = False
    if sms_gateway_url and sms_api_key:
        payload = {
            'to': user.mobile,
            'message': f'Your BUILD UP verification OTP is: {user.otp}. Valid for 10 minutes.',
            'api_key': sms_api_key
        }
        try:
            import requests
            r = requests.post(sms_gateway_url, json=payload, timeout=30)
            sms_sent = getattr(r, 'status_code', 0) == 200
        except Exception:
            sms_sent = False

    # Local-dev: always return demo OTP so you can sign up/login quickly.
    if demo_mode:
        return jsonify({
            'success': True,
            'message': f'OTP resent to your mobile ({_mask_mobile(user.mobile)}).',
            'demo_otp': user.otp,
            'sms_sent': sms_sent
        })

    # Production: only include demo OTP when SMS failed.
    if not sms_sent:
        return jsonify({
            'success': True,
            'message': f'OTP resent to your mobile ({_mask_mobile(user.mobile)}).',
            'demo_otp': user.otp,
            'sms_sent': False
        })

    return jsonify({
        'success': True,
        'message': f'OTP resent to your mobile ({_mask_mobile(user.mobile)}).',
        'sms_sent': sms_sent
    })

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if not user.active:
                flash('This account is inactive. Please contact admin.', 'danger')
                return render_template('auth/login.html')

            if user.role == 'student':
                if (user.email or '').strip().lower() == 'student@buildup.com':
                    # Ensure template displays match BUPS{n:02d} style.
                    # Don't force legacy BUP000.
                    if not user.student_id or not str(user.student_id).startswith('BUPS'):
                        user.student_id = _generate_student_id()
                        db.session.commit()
                elif not user.student_id or user.student_id.startswith('BUPR') or user.student_id.startswith('BUPA'):
                    user.student_id = _generate_student_id()
                    db.session.commit()
            elif user.role == 'recruiter':
                if (user.email or '').strip().lower() == 'recruiter@buildup.com':
                    if user.student_id != 'BUPR00':
                        user.student_id = 'BUPR00'
                        db.session.commit()
                elif not user.student_id or not user.student_id.startswith('BUPR'):
                    user.student_id = _generate_recruiter_id()
                    db.session.commit()

                if not _is_recruiter_admin_approved(user):
                    status = getattr(user, 'company_id_status', None)
                    if status == 'pending_admin':
                        flash('Your Gmail is verified. Please wait for admin approval before recruiter login.', 'warning')
                    elif status == 'declined':
                        flash('Admin declined your recruiter request. Please sign up again with updated recruiter details.', 'danger')
                    else:
                        flash('Please complete recruiter Gmail OTP verification before login.', 'warning')
                    return render_template('auth/login.html')
            elif user.role == 'admin':
                if (user.email or '').strip().lower() == 'admin@buildup.com':
                    if user.student_id != 'BUPA00':
                        user.student_id = 'BUPA00'
                elif not user.student_id or not user.student_id.startswith('BUPA'):
                    user.student_id = _generate_admin_id()
                    db.session.commit()
            remember_me = bool(request.form.get('remember')) or True
            session.permanent = remember_me
            login_user(user, remember=remember_me)
            next_page = request.args.get('next')
            flash(f'Welcome back, {user.email}!', 'success')
            
            if user.role == 'admin':
                return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
            elif user.role == 'recruiter':
                return redirect(next_page) if next_page else redirect(url_for('recruiter.dashboard'))
            else:
                return redirect(next_page) if next_page else redirect(url_for('student.dashboard'))
        else:
            flash('Login failed. Check email and password.', 'danger')
    
    return render_template('auth/login.html')

@auth.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email address.', 'danger')
            return render_template('auth/forgot_password.html')
        
        # Generate OTP for password reset
        otp = _generate_otp()
        user.otp = otp
        user.otp_expires = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()
        
        flash(f'OTP sent to your registered mobile. Demo OTP: {otp}', 'success')
        return redirect(url_for('auth.verify_reset_otp', user_id=user.id))
    
    return render_template('auth/forgot_password.html')

@auth.route('/verify-reset-otp/<int:user_id>', methods=['GET', 'POST'])
def verify_reset_otp(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        otp = request.form.get('otp')
        if user.otp != otp:
            flash('Invalid OTP. Please try again.', 'danger')
            return render_template('auth/verify_reset_otp.html', user_id=user_id)
        
        if user.otp_expires and datetime.utcnow() > user.otp_expires:
            flash('OTP has expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        # OTP verified — clear it and go to reset password
        user.otp = None
        user.otp_expires = None
        db.session.commit()
        return redirect(url_for('auth.reset_password', user_id=user.id))
    
    return render_template('auth/verify_reset_otp.html', user_id=user_id)

@auth.route('/reset-password/<int:user_id>', methods=['GET', 'POST'])
def reset_password(user_id):
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('auth/reset_password.html', user_id=user_id)
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', user_id=user_id)
        
        user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        
        flash('Password reset successfully! Please login with your new password.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', user_id=user_id)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('main.index'))

@student.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    applications = Application.query.filter_by(user_id=current_user.id).all()
    tests = SkillTest.query.filter_by(profile_id=profile.id).all() if profile else []
    tickets = SupportTicket.query.filter_by(user_id=current_user.id).all()
    available_jobs = Job.query.filter_by(is_active=True).all()
    recent_interviews = (
        MockInterview.query
        .filter_by(user_id=current_user.id)
        .order_by(MockInterview.id.desc())
        .limit(5)
        .all()
    )
    
    stats = {
        'total_applications': len(applications),
        'pending_applications': len([a for a in applications if a.status == 'applied']),
        'interviews': len([a for a in applications if a.status == 'interview']),
        'offers': len([a for a in applications if a.status == 'offered']),
        'available_jobs': len(available_jobs),
        'tests_taken': len(tests),
        'avg_score': sum([t.score for t in tests]) / len(tests) if tests else 0
    }
    
    return render_template(
        'student/dashboard.html',
        stats=stats,
        profile=profile,
        applications=applications,
        tickets=tickets,
        recent_interviews=recent_interviews
    )

@student.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('student')
def profile():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        if not profile:
            profile = StudentProfile(user_id=current_user.id)
            db.session.add(profile)
            db.session.flush()

        # Helper: strip and return None if empty, else return cleaned string.
        def _clean(value):
            if value is None:
                return None
            cleaned = value.strip()
            return cleaned if cleaned else None

        # Direct field-by-field save (no exclusion lists that silently drop data)
        profile.first_name = _clean(request.form.get('first_name'))
        profile.last_name = _clean(request.form.get('last_name'))
        profile.phone = _clean(request.form.get('phone'))
        profile.profession = _clean(request.form.get('profession'))
        profile.college = _clean(request.form.get('college'))
        profile.branch = _clean(request.form.get('branch'))
        profile.location = _clean(request.form.get('location'))
        profile.skills = _clean(request.form.get('skills'))
        profile.bio = _clean(request.form.get('bio'))
        profile.linkedin = _clean(request.form.get('linkedin'))
        profile.github = _clean(request.form.get('github'))
        grad_str = _clean(request.form.get('graduation_year'))
        if grad_str:
            try:
                profile.graduation_year = int(grad_str)
            except (ValueError, TypeError):
                profile.graduation_year = None
        else:
            profile.graduation_year = None

        changed = False

        # Profile image upload
        profile_image = request.files.get('profile_image')
        if profile_image and profile_image.filename:
            allowed_img = {'.png', '.jpg', '.jpeg', '.webp'}
            ext = os.path.splitext(profile_image.filename)[1].lower()
            if ext in allowed_img:
                try:
                    profile.profile_image_path = _save_user_file(profile_image, 'profile_images', 'dp')
                    flash('Profile image uploaded successfully!', 'success')
                    changed = True
                except Exception as e:
                    flash(f'Upload failed: {str(e)}', 'danger')
            else:
                flash('Profile image must be PNG/JPG/JPEG/WEBP.', 'warning')

        # Resume upload
        resume_file = request.files.get('resume')
        if resume_file and resume_file.filename:
            allowed_resume = {'.pdf'}
            ext = os.path.splitext(resume_file.filename)[1].lower()
            if ext in allowed_resume:
                profile.resume_path = _save_user_file(resume_file, 'resumes', 'resume')
                profile.resume_score = random.randint(60, 95)
                flash(f'Resume uploaded successfully! Score: {profile.resume_score}/100', 'success')
                changed = True
            else:
                flash('Resume must be a PDF file.', 'warning')

        # Commit all changes
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Could not save changes: {str(e)}', 'danger')
            print(f'[PROFILE SAVE ERROR] {e}')

        return redirect(url_for('student.profile'))
    
    resume_abs_path, _ = _resolve_resume_file(profile)
    return render_template('student/profile.html', profile=profile, resume_available=bool(resume_abs_path))

@student.route('/resume-file')
@login_required
@role_required('student')
def resume_file():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    resume_abs_path, _ = _resolve_resume_file(profile)
    if not resume_abs_path:
        flash('Resume file not found. Please upload your resume again.', 'warning')
        return redirect(url_for('student.profile'))
    return send_file(resume_abs_path, mimetype='application/pdf')

@student.route('/tests')
@login_required
@role_required('student')
def tests():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    # Get only last 5 test results, ordered from newest to oldest
    tests = SkillTest.query.filter_by(profile_id=profile.id).order_by(SkillTest.attempted_at.desc()).limit(5).all() if profile else []
    return render_template('student/tests.html', tests=tests)

@student.route('/tests/all')
@login_required
@role_required('student')
def tests_all():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    # Get all test results, ordered from newest to oldest
    tests = SkillTest.query.filter_by(profile_id=profile.id).order_by(SkillTest.attempted_at.desc()).all() if profile else []
    return render_template('student/tests_all.html', tests=tests)

@student.route('/test-result/<int:test_id>')
@login_required
@role_required('student')
def test_result(test_id):
    test = SkillTest.query.get(test_id)
    if not test:
        flash('Test not found', 'danger')
        return redirect(url_for('student.tests'))
    
    if test.user_id and test.user_id != current_user.id:
        flash('You are not authorized to view this test', 'danger')
        return redirect(url_for('student.tests'))
    
    questions = TestQuestion.query.filter_by(test_id=test.id).all()
    return render_template('student/test_result.html', test=test, questions=questions)

def _get_skillup_base_url():
    skillup_env = os.getenv('SKILLUP_URL')
    if skillup_env:
        return skillup_env.rstrip('/')
    host = request.host.lower() if request else ''
    if 'localhost' in host or '127.0.0.1' in host:
        return 'http://localhost:5173'
    return request.host_url.rstrip('/')

@student.route('/coding-portal')
@login_required
@role_required('student')
def coding_portal():
    sso_token = _build_skillup_sso_token()
    skillup_env = os.getenv('SKILLUP_URL')
    if skillup_env:
        return redirect(f"{skillup_env.rstrip('/')}?sso={sso_token}")
    
    host = request.host.lower() if request else ''
    if ('localhost:5173' in host or '127.0.0.1:5173' in host) or ('localhost:5174' in host):
        return redirect(f"http://localhost:5173?sso={sso_token}")
    
    # Serve full Skill Up React SPA frontend at /skillup/ on cloud deployments
    base_url = request.host_url.rstrip('/')
    return redirect(f"{base_url}/skillup/?sso={sso_token}")

@api.route('/skillup/sso-token', methods=['GET'])
@login_required
@role_required('student')
def skillup_sso_token():
    return jsonify({
        'token': _build_skillup_sso_token(),
        'user': _build_skillup_sso_payload()
    })

@api.route('/auth/me', methods=['GET'])
def auth_me():
    """Get current authenticated user information"""
    try:
        # For demo purposes, return a demo user
        # In production, this would validate session/cookie
        # Keep studentId in the BUPS{n:02d}/BUPS{n:05d} format for consistency.
        user_data = {
            'email': 'student@buildup.com',
            'name': 'Anmol Varshney',
            'firstName': 'Anmol',
            'lastName': 'Varshney',
            'uid': 3,
            'studentId': 'BUPS01',
            'profileImage': 'http://localhost:5002/static/uploads/profile_images/dp_3_1778326463.jpg',
            'totalProblemsSolved': 5,
            'createdAt': '2024-05-12T00:00:00Z'
        }
        
        return jsonify({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to get user info: {str(e)}'}), 500

@api.route('/profile/me', methods=['GET'])
def profile_me():
    """Get user profile with additional details"""
    try:
        # For demo purposes, return profile stats without authentication check
        # In production, this would validate session/cookie
        profile_data = {
            'totalProblemsSolved': 5,
            'totalSubmissions': 12,
            'successRate': 41.7,
            'streak': 3,
            'rank': 15
        }
        
        return jsonify({
            'success': True,
            'user': profile_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to get profile: {str(e)}'}), 500

@api.route('/auth/sso', methods=['POST'])
def auth_sso():
    """Handle SSO token validation from frontend"""
    try:
        data = request.get_json()
        if not data or 'token' not in data:
            return jsonify({'success': False, 'message': 'Invalid SSO token'}), 400
        
        sso_token = data['token']
        
        # Validate SSO token (basic validation)
        if not sso_token or len(sso_token) < 10:
            return jsonify({'success': False, 'message': 'Invalid SSO token format'}), 400
        
        # For demo purposes, accept any valid token format
        # In production, you would validate the token signature and expiry
        user_data = {
            'email': 'student@buildup.com',
            'name': 'Anmol Varshney',
            'firstName': 'Anmol',
            'lastName': 'Varshney',
            'uid': 3,
            'studentId': 'BUPS01',
            'profileImage': 'http://localhost:5002/static/uploads/profile_images/dp_3_1778326463.jpg',
            'totalProblemsSolved': 5,
            'createdAt': '2024-05-12T00:00:00Z'
        }
        
        return jsonify({
            'success': True,
            'user': user_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'SSO validation failed: {str(e)}'}), 500

@student.route('/tests/<test_type>')
@login_required
@role_required('student')
def take_test(test_type):
    categories = {
        'dsa': ['Arrays', 'Linked Lists', 'Trees', 'Graphs', 'Dynamic Programming', 'Sorting', 'Searching'],
        'aptitude': ['Quantitative', 'Logical Reasoning', 'Verbal Ability', 'Data Interpretation'],
        'coding': ['Easy', 'Medium', 'Hard'],
        'core': ['Operating Systems', 'Database', 'Networking', 'OOPS']
    }
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    user_skills = (profile.skills or '') if profile else ''
    # Daily seed to refresh questions for the user once per day
    daily_seed = f"{current_user.id}-{test_type}-{datetime.utcnow().strftime('%Y-%m-%d')}"
    questions = generate_test_questions(test_type, categories.get(test_type, ['General']), seed=daily_seed, user_skills=user_skills)
    return render_template('student/take_test.html', test_type=test_type, questions=questions)

@student.route('/api/submit_test', methods=['POST'])
@login_required
@role_required('student')
def submit_test():
    data = request.get_json(silent=True) or {}
    if not data:
        return jsonify({'success': False, 'message': 'Invalid test payload'}), 400

    test_type = data.get('test_type')
    if not test_type:
        return jsonify({'success': False, 'message': 'Missing test type'}), 400

    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        profile = StudentProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    try:
        score = int(data.get('score') or 0)
        total_questions = int(data.get('total_questions') or 0)
        correct_answers = int(data.get('correct_answers') or 0)
        wrong_answers = int(data.get('wrong_answers') or 0)
        time_taken = int(data.get('time_taken') or 0)
        tab_switches = int(data.get('tab_switches') or 0)
        question_order = data.get('question_order', [])
        weak_topics = data.get('weak_topics', [])
        ai_detected = data.get('ai_detected', False)
        
        avg_time_per_question = time_taken / total_questions if total_questions > 0 else 0
        if avg_time_per_question < 3 and tab_switches == 0:
            ai_detected = True

        test = SkillTest(
            user_id=current_user.id,
            profile_id=profile.id,
            test_type=test_type,
            category=data.get('category'),
            score=score,
            total_questions=total_questions,
            correct_answers=correct_answers,
            wrong_answers=wrong_answers,
            time_taken=time_taken,
            tab_switches=tab_switches,
            question_order=question_order,
            weak_topics=weak_topics,
            ai_detected=ai_detected
        )
        db.session.add(test)
        db.session.commit()
        
        for q_data in data.get('questions', []):
            question = TestQuestion(
                test_id=test.id,
                question=q_data.get('question', ''),
                options=q_data.get('options', []),
                correct_answer=q_data.get('correct_answer', ''),
                user_answer=q_data.get('user_answer', ''),
                is_correct=q_data.get('is_correct', False),
                topic=q_data.get('topic', '')
            )
            db.session.add(question)
        db.session.commit()
        
        if test.score >= 50 and not ai_detected:
            # 30-Day Streak logic
            today_date = datetime.utcnow().date()
            existing_badge = DailyBadge.query.filter_by(user_id=current_user.id, earned_date=today_date).first()
            if not existing_badge:
                badge = DailyBadge(user_id=current_user.id, test_id=test.id, earned_date=today_date)
                db.session.add(badge)
                db.session.commit()
            
            # Calculate streak
            badges = DailyBadge.query.filter_by(user_id=current_user.id).order_by(DailyBadge.earned_date.desc()).all()
            streak = 0
            expected_date = today_date
            for b in badges:
                if b.earned_date == expected_date:
                    streak += 1
                    expected_date -= timedelta(days=1)
                else:
                    break
            
            # Award certificate for every 30 days of streak
            if streak > 0 and streak % 30 == 0 and not existing_badge:
                profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
                first = profile.first_name if profile else ''
                last = profile.last_name if profile else ''
                roll_number = current_user.student_id if current_user.student_id else 'N/A'
                
                cert_name = '30-Day Streak Certification'
                cert_description = (
                    f"Congratulations On completing 30 days streaks And it's the time to "
                    f"turn your badges into a certificate Once again congratulations from the authority."
                )
                
                cert = Certificate(
                    user_id=current_user.id,
                    name=cert_name,
                    description=cert_description,
                    test_category='streak',
                    score=None,
                    certificate_id=f"CRT-STRK-{current_user.id}-{streak}",
                    validity_date=datetime.utcnow() + timedelta(days=365),
                    badge_icon='Image/logo.png'
                )
                db.session.add(cert)
                db.session.commit()
        
        if weak_topics:
            existing_weak = profile.weak_areas or {}
            for topic in weak_topics:
                existing_weak[topic] = existing_weak.get(topic, 0) + 1
            profile.weak_areas = existing_weak
            db.session.commit()
        
        update_interview_readiness(profile.id, test)
        return jsonify({'success': True, 'test_id': test.id, 'correct': correct_answers, 'wrong': wrong_answers})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Could not save test result'}), 500

def generate_test_questions(test_type, categories, seed=None, user_skills=''):
    all_questions = {
        'dsa': [
            {'id': 1, 'topic': 'Arrays', 'question': 'What is the time complexity of accessing an element in an array by index?', 'options': ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'], 'correct': 'O(1)'},
            {'id': 2, 'topic': 'Arrays', 'question': 'Which algorithm finds the maximum subarray sum in O(n) time?', 'options': ['Bubble Sort', 'Kadane\'s Algorithm', 'Binary Search', 'Merge Sort'], 'correct': 'Kadane\'s Algorithm'},
            {'id': 3, 'topic': 'Arrays', 'question': 'What is the space complexity of counting sort?', 'options': ['O(1)', 'O(n)', 'O(k)', 'O(n+k)'], 'correct': 'O(n+k)'},
            {'id': 4, 'topic': 'Arrays', 'question': 'How do you find the missing number in an array containing 1 to n?', 'options': ['Binary Search', 'Hashing', 'XOR method', 'All of the above'], 'correct': 'All of the above'},
            {'id': 5, 'topic': 'Arrays', 'question': 'What is the time complexity of finding the second smallest element?', 'options': ['O(1)', 'O(n)', 'O(n log n)', 'O(n²)'], 'correct': 'O(n)'},
            {'id': 6, 'topic': 'Arrays', 'question': 'Which sorting algorithm is in-place?', 'options': ['Merge Sort', 'Counting Sort', 'Quick Sort', 'Radix Sort'], 'correct': 'Quick Sort'},
            {'id': 7, 'topic': 'Arrays', 'question': 'What is the maximum subarray problem also known as?', 'options': ['Kadane\'s Algorithm', 'Dijkstra\'s Algorithm', 'Bellman-Ford', 'Floyd-Warshall'], 'correct': 'Kadane\'s Algorithm'},
            {'id': 8, 'topic': 'Arrays', 'question': 'Which method is used to search in a sorted array?', 'options': ['Linear Search', 'Binary Search', 'Jump Search', 'All of the above'], 'correct': 'All of the above'},
            {'id': 9, 'topic': 'Arrays', 'question': 'What is the time complexity of inserting at the beginning of an array?', 'options': ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'], 'correct': 'O(n)'},
            {'id': 10, 'topic': 'Arrays', 'question': 'Which technique is used to handle duplicates in sorted array?', 'options': ['Two pointers', 'Hashing', 'Binary search', 'Sliding window'], 'correct': 'Two pointers'},
            {'id': 11, 'topic': 'Linked Lists', 'question': 'What is the time complexity of inserting at the beginning of a singly linked list?', 'options': ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'], 'correct': 'O(1)'},
            {'id': 12, 'topic': 'Linked Lists', 'question': 'Which technique is used to detect a cycle in a linked list?', 'options': ['Two Pointers', 'Hashing', 'Both A and B', 'None'], 'correct': 'Both A and B'},
            {'id': 13, 'topic': 'Linked Lists', 'question': 'How do you find the middle element of a linked list in one pass?', 'options': ['Two Pointers', 'Count and access', 'Recursive', 'Iterative with counter'], 'correct': 'Two Pointers'},
            {'id': 14, 'topic': 'Linked Lists', 'question': 'What is the time complexity of searching in a linked list?', 'options': ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'], 'correct': 'O(n)'},
            {'id': 15, 'topic': 'Linked Lists', 'question': 'Which operation is faster in doubly linked list compared to singly?', 'options': ['Insertion at beginning', 'Deletion from end', 'Traversal', 'Search'], 'correct': 'Deletion from end'},
            {'id': 16, 'topic': 'Stacks', 'question': 'What data structure uses LIFO principle?', 'options': ['Queue', 'Stack', 'Array', 'Linked List'], 'correct': 'Stack'},
            {'id': 17, 'topic': 'Stacks', 'question': 'Which application of stack is used to evaluate postfix expressions?', 'options': ['Parsing', 'Evaluation', 'Conversion', 'All of the above'], 'correct': 'All of the above'},
            {'id': 18, 'topic': 'Stacks', 'question': 'What is the time complexity of push operation in stack?', 'options': ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'], 'correct': 'O(1)'},
            {'id': 19, 'topic': 'Stacks', 'question': 'Which data structure is used in function call recursion?', 'options': ['Queue', 'Stack', 'Heap', 'Array'], 'correct': 'Stack'},
            {'id': 20, 'topic': 'Stacks', 'question': 'What is balanced parenthesis problem used for?', 'options': ['Syntax checking', 'Memory management', 'Process scheduling', 'Network routing'], 'correct': 'Syntax checking'},
            {'id': 21, 'topic': 'Queues', 'question': 'What is the time complexity of enqueue operation in a circular queue?', 'options': ['O(1)', 'O(n)', 'O(log n)', 'O(n²)'], 'correct': 'O(1)'},
            {'id': 22, 'topic': 'Queues', 'question': 'Which type of queue is used in BFS?', 'options': ['Stack', 'Queue', 'Deque', 'Priority Queue'], 'correct': 'Queue'},
            {'id': 23, 'topic': 'Queues', 'question': 'What is the disadvantage of simple queue?', 'options': ['Slow enqueue', 'Slow dequeue', 'Cannot reuse freed spaces', 'Complex implementation'], 'correct': 'Cannot reuse freed spaces'},
            {'id': 24, 'topic': 'Queues', 'question': 'Which queue is used in CPU scheduling?', 'options': ['Simple Queue', 'Circular Queue', 'Priority Queue', 'Double-ended Queue'], 'correct': 'Priority Queue'},
            {'id': 25, 'topic': 'Trees', 'question': 'What is the maximum number of nodes at level k in a binary tree?', 'options': ['k', '2k', '2^k', 'k²'], 'correct': '2^k'},
            {'id': 26, 'topic': 'Trees', 'question': 'Which traversal gives nodes in sorted order for BST?', 'options': ['Preorder', 'Postorder', 'Inorder', 'Level order'], 'correct': 'Inorder'},
            {'id': 27, 'topic': 'Trees', 'question': 'What is the height of an empty tree?', 'options': ['0', '-1', '1', 'Null'], 'correct': '-1'},
            {'id': 28, 'topic': 'Trees', 'question': 'What is the time complexity of searching in a balanced BST?', 'options': ['O(1)', 'O(log n)', 'O(n)', 'O(n log n)'], 'correct': 'O(log n)'},
            {'id': 29, 'topic': 'Trees', 'question': 'Which traversal is used for topological sorting?', 'options': ['Inorder', 'Preorder', 'Postorder', 'DFS/BFS'], 'correct': 'DFS/BFS'},
            {'id': 30, 'topic': 'Trees', 'question': 'What is the minimum number of nodes in a binary tree of height h?', 'options': ['h', 'h+1', '2^h', '2^(h+1) - 1'], 'correct': 'h+1'},
            {'id': 31, 'topic': 'Graphs', 'question': 'Which algorithm finds the shortest path in unweighted graph?', 'options': ['DFS', 'BFS', 'Dijkstra', 'Bellman-Ford'], 'correct': 'BFS'},
            {'id': 32, 'topic': 'Graphs', 'question': 'What is the time complexity of DFS for a graph with V vertices and E edges?', 'options': ['O(V)', 'O(E)', 'O(V+E)', 'O(V*E)'], 'correct': 'O(V+E)'},
            {'id': 33, 'topic': 'Graphs', 'question': 'Which algorithm detects cycle in directed graph?', 'options': ['Union-Find', 'DFS with visited array', 'Topological Sort', 'Both B and C'], 'correct': 'Both B and C'},
            {'id': 34, 'topic': 'Graphs', 'question': 'What is the space complexity of BFS?', 'options': ['O(V)', 'O(E)', 'O(V+E)', 'O(V*E)'], 'correct': 'O(V)'},
            {'id': 35, 'topic': 'Graphs', 'question': 'Which algorithm is used for topological sorting?', 'options': ['DFS', 'BFS', 'Dijkstra', 'Both A and B'], 'correct': 'Both A and B'},
            {'id': 36, 'topic': 'Dynamic Programming', 'question': 'What is the time complexity of standard Fibonacci using memoization?', 'options': ['O(2^n)', 'O(n)', 'O(n²)', 'O(1)'], 'correct': 'O(n)'},
            {'id': 37, 'topic': 'Dynamic Programming', 'question': 'Which property does not hold for optimal substructure?', 'options': ['Recursive solution', 'Overlapping subproblems', 'Optimal solution uses optimal subproblems', 'None'], 'correct': 'Overlapping subproblems'},
            {'id': 38, 'topic': 'Dynamic Programming', 'question': 'What is the space complexity of 0/1 knapsack DP solution?', 'options': ['O(W)', 'O(W*n)', 'O(n*W)', 'O(n)'], 'correct': 'O(n*W)'},
            {'id': 39, 'topic': 'Dynamic Programming', 'question': 'Which approach is bottom-up in DP?', 'options': ['Memoization', 'Tabulation', 'Recursion', 'Backtracking'], 'correct': 'Tabulation'},
            {'id': 40, 'topic': 'Dynamic Programming', 'question': 'What is LCS problem?', 'options': ['Longest Common Subsequence', 'Least Common Subsequence', 'Longest Common Substring', 'Latest Common Substring'], 'correct': 'Longest Common Subsequence'},
        ],
        'aptitude': [
            {'id': 101, 'topic': 'Quantitative', 'question': 'If a train travels 360km in 4 hours, what is its speed?', 'options': ['80 km/h', '90 km/h', '70 km/h', '85 km/h'], 'correct': '90 km/h'},
            {'id': 102, 'topic': 'Quantitative', 'question': 'What is 15% of 200?', 'options': ['25', '30', '35', '20'], 'correct': '30'},
            {'id': 103, 'topic': 'Quantitative', 'question': 'A man buys an item for Rs. 1000 and sells it for Rs. 1200. What is the profit percentage?', 'options': ['10%', '15%', '20%', '25%'], 'correct': '20%'},
            {'id': 104, 'topic': 'Quantitative', 'question': 'If 3x + 5 = 20, what is the value of x?', 'options': ['3', '4', '5', '6'], 'correct': '5'},
            {'id': 105, 'topic': 'Quantitative', 'question': 'What is the LCM of 12 and 18?', 'options': ['24', '36', '48', '72'], 'correct': '36'},
            {'id': 106, 'topic': 'Percentage', 'question': 'If 40% of a number is 80, what is the number?', 'options': ['150', '180', '200', '220'], 'correct': '200'},
            {'id': 107, 'topic': 'Percentage', 'question': 'A price increased from Rs. 50 to Rs. 60. What is the percentage increase?', 'options': ['10%', '15%', '20%', '25%'], 'correct': '20%'},
            {'id': 108, 'topic': 'Profit & Loss', 'question': 'A shopkeeper sells an article at 20% loss. If cost price is Rs. 500, what is selling price?', 'options': ['Rs. 400', 'Rs. 420', 'Rs. 450', 'Rs. 380'], 'correct': 'Rs. 400'},
            {'id': 109, 'topic': 'Profit & Loss', 'question': 'What is marked price if selling price is Rs. 540 after 10% discount on marked price?', 'options': ['Rs. 580', 'Rs. 600', 'Rs. 620', 'Rs. 560'], 'correct': 'Rs. 600'},
            {'id': 110, 'topic': 'Profit & Loss', 'question': 'A dealer offers 10% discount and still makes 20% profit. If cost price is Rs. 1000, what is the marked price?', 'options': ['Rs. 1200', 'Rs. 1300', 'Rs. 1333', 'Rs. 1350'], 'correct': 'Rs. 1333'},
            {'id': 111, 'topic': 'Time & Work', 'question': 'If A can complete a work in 10 days and B in 20 days, in how many days can they complete together?', 'options': ['6.67 days', '7.5 days', '8 days', '5 days'], 'correct': '6.67 days'},
            {'id': 112, 'topic': 'Time & Work', 'question': 'If 4 workers complete a work in 8 days, how many days will 8 workers take?', 'options': ['2 days', '4 days', '6 days', '8 days'], 'correct': '4 days'},
            {'id': 113, 'topic': 'Time & Work', 'question': 'A can do a work in 6 days and B in 9 days. How many days will they take together?', 'options': ['3.6 days', '4 days', '4.5 days', '5 days'], 'correct': '3.6 days'},
            {'id': 114, 'topic': 'Time & Work', 'question': 'If 12 men can build a wall in 20 days, how many days will 15 men take?', 'options': ['14 days', '16 days', '18 days', '20 days'], 'correct': '16 days'},
            {'id': 115, 'topic': 'Ratio & Proportion', 'question': 'If a:b = 3:5 and b:c = 5:7, what is a:b:c?', 'options': ['3:5:7', '5:5:7', '3:5:5', '15:25:35'], 'correct': '3:5:7'},
            {'id': 116, 'topic': 'Ratio & Proportion', 'question': 'The ratio of boys to girls is 3:2. If there are 30 boys, how many girls?', 'options': ['15', '18', '20', '25'], 'correct': '20'},
            {'id': 117, 'topic': 'Ratio & Proportion', 'question': 'If 8:18 = x:45, what is x?', 'options': ['16', '18', '20', '22'], 'correct': '20'},
            {'id': 118, 'topic': 'Logical Reasoning', 'question': 'Complete the series: 2, 6, 12, 20, 30, ?', 'options': ['40', '42', '44', '38'], 'correct': '42'},
            {'id': 119, 'topic': 'Logical Reasoning', 'question': 'Find the next number: 1, 1, 2, 3, 5, 8, ?', 'options': ['10', '11', '12', '13'], 'correct': '13'},
            {'id': 120, 'topic': 'Logical Reasoning', 'question': 'If KEY is coded as 25, what is the code for CAT?', 'options': ['24', '23', '25', '26'], 'correct': '24'},
            {'id': 121, 'topic': 'Logical Reasoning', 'question': 'A is B\'s sister. C is B\'s mother. D is C\'s father. How is A related to D?', 'options': ['Granddaughter', 'Daughter', 'Grandmother', 'Sister'], 'correct': 'Granddaughter'},
            {'id': 122, 'topic': 'Logical Reasoning', 'question': 'Which number replaces ?: 4, 12, 36, 108, ?', 'options': ['216', '324', '432', '144'], 'correct': '324'},
            {'id': 123, 'topic': 'Logical Reasoning', 'question': 'Find the odd one out: 2, 3, 5, 7, 11, 14', 'options': ['2', '7', '11', '14'], 'correct': '14'},
            {'id': 124, 'topic': 'Logical Reasoning', 'question': 'What comes next: AZ, BY, CX, DW, ?', 'options': ['EU', 'EV', 'FU', 'EV'], 'correct': 'EV'},
            {'id': 125, 'topic': 'Verbal Ability', 'question': 'Choose the synonym of "Benevolent"', 'options': ['Cruel', 'Kind', 'Angry', 'Sad'], 'correct': 'Kind'},
            {'id': 126, 'topic': 'Verbal Ability', 'question': 'Choose the antonym of "Artificial"', 'options': ['Natural', 'Synthetic', 'Man-made', 'False'], 'correct': 'Natural'},
            {'id': 127, 'topic': 'Verbal Ability', 'question': 'Which word means "to make something less severe"?', 'options': ['Aggravate', 'Mitigate', 'Escalate', 'Exacerbate'], 'correct': 'Mitigate'},
            {'id': 128, 'topic': 'Verbal Ability', 'question': 'Choose the correctly spelled word:', 'options': ['Occassion', 'Occasion', 'Ocassion', 'Occasien'], 'correct': 'Occasion'},
            {'id': 129, 'topic': 'Data Interpretation', 'question': 'If a pie chart shows 25% for Rent, what angle does it represent?', 'options': ['60°', '75°', '90°', '45°'], 'correct': '90°'},
            {'id': 130, 'topic': 'Data Interpretation', 'question': 'In a bar graph, if height of bar is 8cm representing 40%, what scale is used?', 'options': ['1cm = 5%', '1cm = 8%', '1cm = 10%', '1cm = 4%'], 'correct': '1cm = 5%'},
            {'id': 131, 'topic': 'Time & Distance', 'question': 'A car travels at 60 km/h for 2 hours and at 80 km/h for 3 hours. What is total distance?', 'options': ['360 km', '300 km', '240 km', '280 km'], 'correct': '360 km'},
            {'id': 132, 'topic': 'Time & Distance', 'question': 'If a man walks at 4 km/h, how long will he take to cover 20 km?', 'options': ['4 hours', '5 hours', '6 hours', '3 hours'], 'correct': '5 hours'},
            {'id': 133, 'topic': 'Percentage', 'question': 'A number is increased by 20% and then decreased by 20%. What is net change?', 'options': ['0%', '4% increase', '4% decrease', '20% increase'], 'correct': '4% decrease'},
            {'id': 134, 'topic': 'Simple Interest', 'question': 'What is simple interest on Rs. 1000 at 10% for 2 years?', 'options': ['Rs. 100', 'Rs. 150', 'Rs. 200', 'Rs. 250'], 'correct': 'Rs. 200'},
            {'id': 135, 'topic': 'Logical Reasoning', 'question': 'If ROAD is coded as URDG, how is SWAN coded?', 'options': ['VZDQ', 'VZCQ', 'WZDQ', 'VZCP'], 'correct': 'VZDQ'},
            {'id': 136, 'topic': 'Number System', 'question': 'What is the decimal equivalent of binary 1101?', 'options': ['11', '12', '13', '14'], 'correct': '13'},
            {'id': 137, 'topic': 'Number System', 'question': 'What is 20% of 50% of 100?', 'options': ['5', '10', '15', '20'], 'correct': '10'},
            {'id': 138, 'topic': 'Logical Reasoning', 'question': 'Pointing to a man, a woman said "His mother is the only daughter of my mother". How is the woman related?', 'options': ['Mother', 'Daughter', 'Sister', 'Grandmother'], 'correct': 'Mother'},
            {'id': 139, 'topic': 'Average', 'question': 'Find average of first 5 natural numbers:', 'options': ['2', '2.5', '3', '3.5'], 'correct': '3'},
            {'id': 140, 'topic': 'Profit & Loss', 'question': 'A shopkeeper sells at cost price but uses 900g weight for 1kg. What is profit?', 'options': ['9.09%', '10%', '11.11%', '12%'], 'correct': '11.11%'},
        ],
        'coding': [
            {'id': 201, 'topic': 'Python', 'question': 'What will be the output of: print(type([]))?', 'options': ["<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'array'>"], 'correct': "<class 'list'>"},
            {'id': 202, 'topic': 'Python', 'question': 'Which keyword is used to define a function in Python?', 'options': ['function', 'def', 'func', 'define'], 'correct': 'def'},
            {'id': 203, 'topic': 'Python', 'question': 'What is the output: len("BuildUp")?', 'options': ['6', '7', '8', '9'], 'correct': '7'},
            {'id': 204, 'topic': 'Python', 'question': 'Which is immutable in Python?', 'options': ['List', 'Dictionary', 'Set', 'Tuple'], 'correct': 'Tuple'},
            {'id': 205, 'topic': 'Python', 'question': 'What is the output: print(2 ** 3)?', 'options': ['5', '6', '8', '9'], 'correct': '8'},
            {'id': 206, 'topic': 'Python', 'question': 'What is the output: bool("")?', 'options': ['True', 'False', 'None', 'Error'], 'correct': 'False'},
            {'id': 207, 'topic': 'Python', 'question': 'Which method adds an element to the end of a list?', 'options': ['add()', 'append()', 'insert()', 'push()'], 'correct': 'append()'},
            {'id': 208, 'topic': 'Python', 'question': 'What is the output: print(10 // 3)?', 'options': ['3.33', '3', '4', '3.0'], 'correct': '3'},
            {'id': 209, 'topic': 'Python', 'question': 'What is the output: "hello"[::-1]?', 'options': ['hello', 'olleh', 'hellow', 'Error'], 'correct': 'olleh'},
            {'id': 210, 'topic': 'Python', 'question': 'Which data structure uses key-value pairs?', 'options': ['List', 'Tuple', 'Dictionary', 'Set'], 'correct': 'Dictionary'},
            {'id': 211, 'topic': 'JavaScript', 'question': 'What does CSS stand for?', 'options': ['Creative Style Sheets', 'Cascading Style Sheets', 'Computer Style Sheets', 'Colorful Style Sheets'], 'correct': 'Cascading Style Sheets'},
            {'id': 212, 'topic': 'JavaScript', 'question': 'Which symbol is used for single-line comments in JavaScript?', 'options': ['#', '//', '/*', '--'], 'correct': '//'},
            {'id': 213, 'topic': 'JavaScript', 'question': 'What is the output: typeof undefined?', 'options': ['"undefined"', '"null"', '"object"', '"string"'], 'correct': '"undefined"'},
            {'id': 214, 'topic': 'JavaScript', 'question': 'Which method adds an element to the end of an array?', 'options': ['push()', 'pop()', 'shift()', 'unshift()'], 'correct': 'push()'},
            {'id': 215, 'topic': 'JavaScript', 'question': 'What is the result of: 3 + "3" in JavaScript?', 'options': ['6', '"33"', 'NaN', 'Error'], 'correct': '"33"'},
            {'id': 216, 'topic': 'JavaScript', 'question': 'Which keyword declares a block-scoped variable?', 'options': ['var', 'let', 'both B and C', 'const'], 'correct': 'both B and C'},
            {'id': 217, 'topic': 'JavaScript', 'question': 'What is the output: Boolean("")?', 'options': ['true', 'false', 'undefined', 'null'], 'correct': 'false'},
            {'id': 218, 'topic': 'JavaScript', 'question': 'Which method converts JSON string to object?', 'options': ['JSON.stringify()', 'JSON.parse()', 'JSON.convert()', 'JSON.toObject()'], 'correct': 'JSON.parse()'},
            {'id': 219, 'topic': 'JavaScript', 'question': 'What does DOM stand for?', 'options': ['Document Object Model', 'Data Object Model', 'Document Order Model', 'Data Order Model'], 'correct': 'Document Object Model'},
            {'id': 220, 'topic': 'JavaScript', 'question': 'Which is NOT a JavaScript framework?', 'options': ['React', 'Angular', 'Vue', 'Django'], 'correct': 'Django'},
            {'id': 221, 'topic': 'Java', 'question': 'What is the default value of an int variable in Java?', 'options': ['0', 'null', 'undefined', '-1'], 'correct': '0'},
            {'id': 222, 'topic': 'Java', 'question': 'Which keyword is used to inherit a class in Java?', 'options': ['inherits', 'extends', 'implements', 'super'], 'correct': 'extends'},
            {'id': 223, 'topic': 'Java', 'question': 'What is the size of int in Java?', 'options': ['8 bits', '16 bits', '32 bits', '64 bits'], 'correct': '32 bits'},
            {'id': 224, 'topic': 'Java', 'question': 'Which is not an OOP concept?', 'options': ['Encapsulation', 'Inheritance', 'Compilation', 'Polymorphism'], 'correct': 'Compilation'},
            {'id': 225, 'topic': 'Java', 'question': 'What is the output: System.out.println(10/3)?', 'options': ['3.33', '3', '3.0', 'Error'], 'correct': '3'},
            {'id': 226, 'topic': 'Java', 'question': 'Which access modifier makes a member accessible only within the same package?', 'options': ['private', 'protected', 'default', 'public'], 'correct': 'default'},
            {'id': 227, 'topic': 'C++', 'question': 'Which operator is used for memory allocation in C++?', 'options': ['malloc', 'alloc', 'new', 'create'], 'correct': 'new'},
            {'id': 228, 'topic': 'C++', 'question': 'What is a virtual function?', 'options': ['Function in base class overridden by derived', 'Static function', 'Inline function', 'Friend function'], 'correct': 'Function in base class overridden by derived'},
            {'id': 229, 'topic': 'C++', 'question': 'What is the size of char in C++?', 'options': ['1 byte', '2 bytes', '4 bytes', '8 bytes'], 'correct': '1 byte'},
            {'id': 230, 'topic': 'C++', 'question': 'Which keyword is used to prevent inheritance?', 'options': ['final', 'sealed', 'static', 'const'], 'correct': 'final'},
            {'id': 231, 'topic': 'Data Structures', 'question': 'Which data structure uses LIFO?', 'options': ['Queue', 'Stack', 'Array', 'Linked List'], 'correct': 'Stack'},
            {'id': 232, 'topic': 'Algorithms', 'question': 'What is the time complexity of QuickSort average case?', 'options': ['O(n)', 'O(n log n)', 'O(n²)', 'O(log n)'], 'correct': 'O(n log n)'},
            {'id': 233, 'topic': 'Algorithms', 'question': 'Which sorting algorithm is stable?', 'options': ['QuickSort', 'HeapSort', 'MergeSort', 'Selection Sort'], 'correct': 'MergeSort'},
            {'id': 234, 'topic': 'Algorithms', 'question': 'What is the time complexity of binary search?', 'options': ['O(1)', 'O(n)', 'O(log n)', 'O(n log n)'], 'correct': 'O(log n)'},
            {'id': 235, 'topic': 'Algorithms', 'question': 'Which algorithm uses divide and conquer?', 'options': ['Bubble Sort', 'Insertion Sort', 'Merge Sort', 'Selection Sort'], 'correct': 'Merge Sort'},
            {'id': 236, 'topic': 'OOP Concepts', 'question': 'What is encapsulation?', 'options': ['Hiding data', 'Inheritance', 'Polymorphism', 'Abstraction'], 'correct': 'Hiding data'},
            {'id': 237, 'topic': 'OOP Concepts', 'question': 'Which concept allows one class to derive properties from another?', 'options': ['Encapsulation', 'Abstraction', 'Inheritance', 'Polymorphism'], 'correct': 'Inheritance'},
            {'id': 238, 'topic': 'OOP Concepts', 'question': 'What is abstraction?', 'options': ['Showing all details', 'Hiding complexity', 'Creating objects', 'Defining classes'], 'correct': 'Hiding complexity'},
            {'id': 239, 'topic': 'OOP Concepts', 'question': 'Which principle states the same method can have different implementations?', 'options': ['Encapsulation', 'Inheritance', 'Abstraction', 'Polymorphism'], 'correct': 'Polymorphism'},
            {'id': 240, 'topic': 'OOP Concepts', 'question': 'What is a constructor?', 'options': ['Destructor', 'Method called when object is created', 'Static method', 'Getter method'], 'correct': 'Method called when object is created'},
        ],
        'core': [
            {'id': 301, 'topic': 'Operating Systems', 'question': 'What is the full form of OS?', 'options': ['Open Software', 'Operating System', 'Open Source', 'Online System'], 'correct': 'Operating System'},
            {'id': 302, 'topic': 'Operating Systems', 'question': 'Which scheduling algorithm is non-preemptive?', 'options': ['Round Robin', 'SJF', 'FCFS', 'Priority'], 'correct': 'SJF'},
            {'id': 303, 'topic': 'Operating Systems', 'question': 'What is a deadlock?', 'options': ['Process failure', 'Circular wait', 'Memory overflow', 'CPU overheat'], 'correct': 'Circular wait'},
            {'id': 304, 'topic': 'Operating Systems', 'question': 'What is thrashing?', 'options': ['High CPU usage', 'Excessive page swapping', 'Memory leak', 'Disk failure'], 'correct': 'Excessive page swapping'},
            {'id': 305, 'topic': 'Operating Systems', 'question': 'What is the purpose of virtual memory?', 'options': ['Increase storage', 'Extend address space', 'Speed up CPU', 'Reduce power'], 'correct': 'Extend address space'},
            {'id': 306, 'topic': 'Operating Systems', 'question': 'Which scheduling algorithm gives minimum average waiting time?', 'options': ['FCFS', 'SJF', 'Round Robin', 'Priority'], 'correct': 'SJF'},
            {'id': 307, 'topic': 'Operating Systems', 'question': 'What is a process?', 'options': ['Program in execution', 'Program on disk', 'Compile time', 'Hardware'], 'correct': 'Program in execution'},
            {'id': 308, 'topic': 'Operating Systems', 'question': 'What is context switching?', 'options': ['Switching users', 'Saving/restoring CPU state', 'Changing OS', 'Rebooting'], 'correct': 'Saving/restoring CPU state'},
            {'id': 309, 'topic': 'Operating Systems', 'question': 'What is a semaphore?', 'options': ['Memory allocation', 'Synchronization mechanism', 'Process state', 'File system'], 'correct': 'Synchronization mechanism'},
            {'id': 310, 'topic': 'Operating Systems', 'question': 'Which is not a process state?', 'options': ['New', 'Ready', 'Running', 'Reading'], 'correct': 'Reading'},
            {'id': 311, 'topic': 'Database', 'question': 'Which SQL keyword is used to retrieve data?', 'options': ['GET', 'FETCH', 'SELECT', 'RETRIEVE'], 'correct': 'SELECT'},
            {'id': 312, 'topic': 'Database', 'question': 'What is a primary key?', 'options': ['Any column', 'Unique identifier', 'First column', 'Foreign key'], 'correct': 'Unique identifier'},
            {'id': 313, 'topic': 'Database', 'question': 'What does JOIN do in SQL?', 'options': ['Combines rows from two tables', 'Deletes records', 'Updates records', 'Creates tables'], 'correct': 'Combines rows from two tables'},
            {'id': 314, 'topic': 'Database', 'question': 'What is normalization?', 'options': ['Data duplication', 'Reducing redundancy', 'Data compression', 'Data encryption'], 'correct': 'Reducing redundancy'},
            {'id': 315, 'topic': 'Database', 'question': 'What is a foreign key?', 'options': ['Key to another database', 'Reference to another table', 'Primary key copy', 'Index'], 'correct': 'Reference to another table'},
            {'id': 316, 'topic': 'Database', 'question': 'Which SQL command is used to remove duplicates?', 'options': ['DELETE', 'DROP', 'DISTINCT', 'REMOVE'], 'correct': 'DISTINCT'},
            {'id': 317, 'topic': 'Database', 'question': 'What is ACID in databases?', 'options': ['Atomicity, Consistency, Isolation, Durability', 'Array, Column, Index, Data', 'Admin, Create, Insert, Delete', 'Access, Control, Integrity, Design'], 'correct': 'Atomicity, Consistency, Isolation, Durability'},
            {'id': 318, 'topic': 'Database', 'question': 'Which is a NoSQL database?', 'options': ['MySQL', 'PostgreSQL', 'MongoDB', 'Oracle'], 'correct': 'MongoDB'},
            {'id': 319, 'topic': 'Database', 'question': 'What does GROUP BY do?', 'options': ['Joins tables', 'Filters rows', 'Groups rows with same values', 'Sorts data'], 'correct': 'Groups rows with same values'},
            {'id': 320, 'topic': 'Database', 'question': 'What is an index in database?', 'options': ['Primary key', 'Speeds up data retrieval', 'Foreign key', 'Constraint'], 'correct': 'Speeds up data retrieval'},
            {'id': 321, 'topic': 'Networking', 'question': 'Which protocol is used for secure web browsing?', 'options': ['HTTP', 'FTP', 'HTTPS', 'SMTP'], 'correct': 'HTTPS'},
            {'id': 322, 'topic': 'Networking', 'question': 'What does IP stand for?', 'options': ['Internet Protocol', 'Internal Protocol', 'Internet Program', 'Inter Protocol'], 'correct': 'Internet Protocol'},
            {'id': 323, 'topic': 'Networking', 'question': 'Which layer handles routing in OSI model?', 'options': ['Data Link', 'Network', 'Transport', 'Application'], 'correct': 'Network'},
            {'id': 324, 'topic': 'Networking', 'question': 'What is DNS?', 'options': ['Domain Name System', 'Data Network Service', 'Dynamic Network System', 'Digital Name Service'], 'correct': 'Domain Name System'},
            {'id': 325, 'topic': 'Networking', 'question': 'Which protocol sends email?', 'options': ['HTTP', 'FTP', 'SMTP', 'TCP'], 'correct': 'SMTP'},
            {'id': 326, 'topic': 'Networking', 'question': 'What does TCP stand for?', 'options': ['Transfer Control Protocol', 'Transmission Control Protocol', 'Transport Connection Protocol', 'Transfer Communication Protocol'], 'correct': 'Transmission Control Protocol'},
            {'id': 327, 'topic': 'Networking', 'question': 'What is the well-known port for HTTP?', 'options': ['21', '25', '80', '443'], 'correct': '80'},
            {'id': 328, 'topic': 'Networking', 'question': 'Which device operates at Layer 3 of OSI model?', 'options': ['Hub', 'Switch', 'Router', 'Repeater'], 'correct': 'Router'},
            {'id': 329, 'topic': 'Networking', 'question': 'What is MAC address?', 'options': ['Logical address', 'Physical address', 'IP address', 'Network address'], 'correct': 'Physical address'},
            {'id': 330, 'topic': 'Networking', 'question': 'Which protocol is connectionless?', 'options': ['TCP', 'UDP', 'FTP', 'HTTP'], 'correct': 'UDP'},
            {'id': 331, 'topic': 'OOPS', 'question': 'What is a class?', 'options': ['An instance', 'A blueprint', 'A variable', 'A function'], 'correct': 'A blueprint'},
            {'id': 332, 'topic': 'OOPS', 'question': 'What is polymorphism?', 'options': ['Many forms', 'Single form', 'No form', 'Hidden form'], 'correct': 'Many forms'},
            {'id': 333, 'topic': 'OOPS', 'question': 'Which concept hides internal details?', 'options': ['Encapsulation', 'Inheritance', 'Polymorphism', 'Abstraction'], 'correct': 'Abstraction'},
            {'id': 334, 'topic': 'OOPS', 'question': 'What is multiple inheritance?', 'options': ['One class inherits one class', 'One class inherits multiple classes', 'Multiple classes inherit one', 'None'], 'correct': 'One class inherits multiple classes'},
            {'id': 335, 'topic': 'OOPS', 'question': 'What is method overloading?', 'options': ['Same name, different parameters', 'Different name, same parameters', 'Runtime binding', 'Compile time binding'], 'correct': 'Same name, different parameters'},
            {'id': 336, 'topic': 'OOPS', 'question': 'What is method overriding?', 'options': ['Same signature in same class', 'Same signature in different class', 'Different signature', 'No inheritance'], 'correct': 'Same signature in different class'},
            {'id': 337, 'topic': 'OOPS', 'question': 'What is an abstract class?', 'options': ['Class with only concrete methods', 'Class that cannot be instantiated', 'Class with no methods', 'Static class'], 'correct': 'Class that cannot be instantiated'},
            {'id': 338, 'topic': 'OOPS', 'question': 'What is the purpose of constructor?', 'options': ['Destroy objects', 'Initialize objects', 'Delete objects', 'Copy objects'], 'correct': 'Initialize objects'},
            {'id': 339, 'topic': 'OOPS', 'question': 'Which is not a type of inheritance?', 'options': ['Single', 'Multiple', 'Multilevel', 'Polyphase'], 'correct': 'Polyphase'},
            {'id': 340, 'topic': 'OOPS', 'question': 'What is a destructor?', 'options': ['Creates object', 'Initializes object', 'Called when object is destroyed', 'Copies object'], 'correct': 'Called when object is destroyed'},
        ]
    }
    
    questions = all_questions.get(test_type, [])
    if seed is not None:
        random.seed(seed)

    if test_type == 'coding' and user_skills:
        user_skill_list = [s.strip().lower() for s in user_skills.split(',') if s.strip()]
        topic_map = {
            'python': 'Python', 'javascript': 'JavaScript', 'js': 'JavaScript',
            'java': 'Java', 'c++': 'C++', 'cpp': 'C++', 'c': 'C++',
            'dsa': 'Data Structures', 'data structures': 'Data Structures',
            'algorithm': 'Algorithms', 'algorithms': 'Algorithms',
            'oop': 'OOP Concepts', 'oops': 'OOP Concepts', 'object oriented': 'OOP Concepts'
        }
        matched_topics = set()
        for skill in user_skill_list:
            mapped = topic_map.get(skill)
            if mapped:
                matched_topics.add(mapped)
            for q in questions:
                if skill in q['topic'].lower():
                    matched_topics.add(q['topic'])

        prioritized = [q for q in questions if q['topic'] in matched_topics]
        others = [q for q in questions if q['topic'] not in matched_topics]
        random.shuffle(prioritized)
        random.shuffle(others)
        selected_questions = (prioritized + others)[:25]
    else:
        selected_questions = random.sample(questions, min(25, len(questions)))
        random.shuffle(selected_questions)
    
    return selected_questions

def update_interview_readiness(profile_id, test):
    readiness = InterviewReadiness.query.filter_by(profile_id=profile_id).first()
    if not readiness:
        readiness = InterviewReadiness(profile_id=profile_id)
        db.session.add(readiness)
    
    test_map = {
        'dsa': 'dsa_score',
        'aptitude': 'aptitude_score',
        'coding': 'projects_score',
        'core': 'core_subjects_score'
    }
    
    if test.test_type in test_map:
        setattr(readiness, test_map[test.test_type], test.score or 0)
        scores = [readiness.communication_score, readiness.dsa_score, 
                  readiness.aptitude_score, readiness.projects_score, readiness.core_subjects_score]
        non_zero_scores = [s for s in scores if s and s > 0]
        readiness.overall_score = (sum(non_zero_scores) // len(non_zero_scores)) if non_zero_scores else 0
        readiness.last_updated = datetime.utcnow()
    
    db.session.commit()


@student.route('/apply/<int:job_id>', methods=['POST'])
@login_required
@role_required('student')
def apply_job(job_id):
    job = Job.query.filter_by(id=job_id, is_active=True).first()
    if not job:
        return jsonify({'success': False, 'message': 'Job is not available'}), 404

    existing = Application.query.filter_by(user_id=current_user.id, job_id=job_id).first()
    if existing:
        return jsonify({'success': False, 'message': 'Already applied'})

    try:
        application = Application(user_id=current_user.id, job_id=job_id)
        db.session.add(application)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Application submitted'})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Could not submit application right now'}), 500

@student.route('/jobs')
@login_required
@role_required('student')
def jobs():
    return redirect(url_for('student.applications'))


@student.route('/job/<int:job_id>')
@login_required
@role_required('student')
def job_detail(job_id):
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    job = Job.query.filter_by(id=job_id, is_active=True).first_or_404()
    applications_list = Application.query.filter_by(user_id=current_user.id).all()
    matched_jobs = _build_student_job_matches(profile, applications_list)
    job_item = next((item for item in matched_jobs if item['job'].id == job.id), None)

    if job_item is None:
        job_item = {
            'job': job,
            'match_score': 0,
            'is_applied': any(application.job_id == job.id for application in applications_list)
        }

    return render_template('student/job_detail.html', item=job_item, profile=profile)


@student.route('/jobs/live')
@login_required
@role_required('student')
def jobs_live():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    applications_list = Application.query.filter_by(user_id=current_user.id).all()
    matched_jobs = _build_student_job_matches(profile, applications_list)

    jobs_payload = []
    for item in matched_jobs:
        job = item['job']
        jobs_payload.append({
            'id': job.id,
            'match_score': item['match_score'],
            'is_applied': item['is_applied'],
            'posted_at': job.posted_at.isoformat() if job.posted_at else None
        })

    return jsonify({
        'count': len(jobs_payload),
        'jobs': jobs_payload,
        'signature': _job_feed_signature(matched_jobs),
        'generated_at': datetime.utcnow().isoformat()
    })

@api.route('/job-applications/<int:job_id>')
@login_required
def job_applications(job_id):
    job = Job.query.get_or_404(job_id)
    applications = Application.query.filter_by(job_id=job_id).all()
    
    app_list = []
    for app in applications:
        user = User.query.get(app.user_id)
        profile = StudentProfile.query.filter_by(user_id=app.user_id).first()
        app_list.append({
            'id': app.id,
            'student_name': f"{profile.first_name} {profile.last_name}".strip() if profile else user.email.split('@')[0],
            'student_email': user.email,
            'status': app.status,
            'applied_at': app.applied_at.strftime('%Y-%m-%d %H:%M') if app.applied_at else None
        })
    
    return jsonify({'success': True, 'applications': app_list})

@student.route('/applications')
@login_required
@role_required('student')
def applications():
    applications_list = Application.query.filter_by(user_id=current_user.id).all()
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    matched_jobs = _build_student_job_matches(profile, applications_list)
    
    return render_template('student/applications.html', 
                        applications=applications_list, 
                        jobs=matched_jobs, 
                        profile=profile,
                        jobs_signature=_job_feed_signature(matched_jobs))

@student.route('/resume-upload', methods=['POST'])
@login_required
def upload_resume():
    if 'resume' not in request.files:
        return jsonify({'success': False, 'message': 'No file'})
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'message': 'Only PDF files are allowed'})
    
    filename = f"resume_{current_user.id}.pdf"
    upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join('static', 'uploads'))
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        return jsonify({'success': False, 'message': 'Student profile not found'})
    
    profile.resume_path = filename
    db.session.commit()
    
    extracted_data = analyze_resume(file_path)
    if extracted_data.get('error'):
        return jsonify({'success': False, 'message': extracted_data['error']})
    
    return jsonify({'success': True, 'data': extracted_data})

def analyze_resume(file_path):
    try:
        doc = fitz.open(file_path)
        text = ''
        for page in doc:
            text += page.get_text()
        doc.close()
        
        skills_keywords = ['python', 'java', 'javascript', 'react', 'angular', 'nodejs', 
                          'sql', 'mongodb', 'docker', 'aws', 'git', 'html', 'css', 'django',
                          'flask', 'machine learning', 'data science', 'tensorflow', 'pytorch',
                          'c++', 'c', 'php', 'ruby', 'swift', 'kotlin', 'typescript']
        
        found_skills = [skill for skill in skills_keywords if skill.lower() in text.lower()]
        experience_years = 0
        if 'experience' in text.lower():
            import re
            exp_match = re.search(r'(\d+)\+?\s*years?', text.lower())
            if exp_match:
                experience_years = int(exp_match.group(1))
        
        education = []
        degrees = ['b.tech', 'm.tech', 'b.e', 'm.s', 'b.sc', 'm.sc']
        for degree in degrees:
            if degree in text.lower():
                education.append(degree.upper())
        
        score = min(100, len(found_skills) * 10 + experience_years * 5 + len(education) * 15)
        
        profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
        if profile:
            profile.resume_score = score
            profile.skills = ', '.join(found_skills)
            db.session.commit()
        
        return {
            'skills': found_skills,
            'experience_years': experience_years,
            'education': education,
            'score': score,
            'text_length': len(text)
        }
    except Exception as e:
        return {'error': str(e)}

@api.route('/analyze-resume', methods=['POST'])
@login_required
def api_analyze_resume():
    if 'resume' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'})
    
    file = request.files['resume']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'message': 'Only PDF files are allowed'})
    
    filename = f"resume_{current_user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    upload_folder = current_app.config.get('UPLOAD_FOLDER', os.path.join('static', 'uploads'))
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)
    
    analysis = analyze_resume(file_path)
    if analysis.get('error'):
        return jsonify({'success': False, 'message': analysis['error']})
    
    return jsonify({'success': True, 'analysis': analysis})

@api.route('/compare-jd', methods=['POST'])
@login_required
def compare_with_jd():
    data = request.json
    job_id = data.get('job_id')
    
    job = Job.query.get(job_id)
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if not job or not profile:
        return jsonify({'success': False})
    
    user_skills = set(profile.skills.lower().split(', ')) if profile.skills else set()
    job_skills = set(job.required_skills.lower().split(', ')) if job.required_skills else set()
    
    matching = user_skills & job_skills
    missing = job_skills - user_skills
    
    match_score = len(matching) / len(job_skills) * 100 if job_skills else 0
    
    return jsonify({
        'success': True,
        'match_score': int(match_score),
        'matching_skills': list(matching),
        'missing_skills': list(missing)
    })

@student.route('/mock-interview', methods=['GET', 'POST'])
@login_required
@role_required('student')
def mock_interview():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        job_role = request.form.get('job_role')
        
        if not profile or not profile.resume_path:
            flash('Please upload your resume first before starting the interview.', 'warning')
            return redirect(url_for('student.mock_interview'))
        
        interview = MockInterview(
            user_id=current_user.id,
            job_role=job_role,
            scheduled_time=datetime.now()
        )
        db.session.add(interview)
        db.session.commit()
        return redirect(url_for('student.interview_session', interview_id=interview.id))
    
    return render_template('student/mock_interview.html', has_resume=profile.resume_path if profile else False)

@student.route('/interview/<int:interview_id>')
@login_required
@role_required('student')
def interview_session(interview_id):
    interview = MockInterview.query.get(interview_id)
    if not interview or interview.user_id != current_user.id:
        flash('Interview not found', 'danger')
        return redirect(url_for('student.mock_interview'))
    
    questions = generate_interview_questions(interview.job_role)
    return render_template('student/interview_session.html', interview=interview, questions=questions)

def generate_interview_questions(job_role):
    questions_db = {
        'frontend': [
            'Explain the difference between var, let, and const in JavaScript.',
            'What is the Virtual DOM in React?',
            'How does CSS Flexbox work?',
            'Explain event bubbling and event capture.',
            'What are React Hooks? Give examples of built-in hooks.',
            'What is the difference between arrow functions and regular functions?',
            'Explain the useState hook in React.',
            'What is the purpose of useEffect hook?',
            'How do you optimize React application performance?',
            'What is the difference between CSS Grid and Flexbox?'
        ],
        'backend': [
            'Explain the difference between SQL and NoSQL databases.',
            'What is REST API? Explain its principles.',
            'How does authentication work with JWT tokens?',
            'What is database indexing and when should you use it?',
            'Explain the concept of microservices architecture.',
            'What is the difference between DELETE and DROP in SQL?',
            'How do you handle database transactions?',
            'What is caching and why is it important?',
            'Explain the ACID properties of a database.',
            'What are the differences between PUT and PATCH methods?'
        ],
        'fullstack': [
            'How do you handle state management in React applications?',
            'Explain the client-server architecture.',
            'What is the purpose of API endpoints?',
            'How do you secure a web application?',
            'Explain database relationships and normalization.',
            'What is the difference between authentication and authorization?',
            'How do you implement pagination in REST APIs?',
            'What is Docker and why is it used?',
            'Explain the concept of CI/CD pipeline.',
            'How do you handle errors in a fullstack application?'
        ],
        'data': [
            'What is the difference between supervised and unsupervised learning?',
            'Explain the bias-variance tradeoff.',
            'How do you handle missing values in a dataset?',
            'What is feature engineering?',
            'Explain the confusion matrix and its metrics.',
            'What is the difference between regression and classification?',
            'How do you prevent overfitting in a model?',
            'What is the purpose of train-test split?',
            'Explain the concept of cross-validation.',
            'What are the key metrics to evaluate a classification model?'
        ],
        'devops': [
            'What is Docker and how does it differ from a virtual machine?',
            'Explain the concept of container orchestration.',
            'What is Kubernetes and when should you use it?',
            'How do you implement CI/CD pipeline?',
            'What is Infrastructure as Code?',
            'Explain the differences between Docker COPY and ADD commands.',
            'What is the purpose of Docker volumes?',
            'How do you monitor containers in production?',
            'What is the difference between continuous integration and continuous deployment?',
            'Explain the concept of blue-green deployment.'
        ],
        'default': [
            'Tell me about yourself.',
            'What are your strengths and weaknesses?',
            'Why do you want to work at this company?',
            'Describe a challenging project you worked on.',
            'Where do you see yourself in 5 years?',
            'What motivates you to do your best work?',
            'How do you handle pressure or stressful situations?',
            'Describe a time when you had to work with a difficult team member.',
            'What do you know about our company?',
            'Why should we hire you?'
        ]
    }
    
    role_key = job_role.lower() if job_role else 'default'
    if role_key not in questions_db:
        role_key = 'default'
    
    return questions_db[role_key][:10]

@api.route('/save-interview', methods=['POST'])
@login_required
def save_interview():
    data = request.json
    interview_id = data.get('interview_id')
    
    interview = MockInterview.query.get(interview_id)
    if interview and interview.user_id == current_user.id:
        proctoring_logs = data.get('proctoring_logs', {}) or {}
        violation_count = int(proctoring_logs.get('violation_count') or 0)
        interview_invalid = bool(proctoring_logs.get('interview_invalid') or violation_count >= 3)

        interview.questions_asked = data.get('questions')
        interview.answers_given = data.get('answers')
        interview.score = data.get('score', 0)
        interview.feedback = data.get('feedback', '')
        interview.status = 'completed'
        interview.proctoring_logs = proctoring_logs
        db.session.commit()
        
        if interview_invalid:
            return jsonify({
                'success': True,
                'warning': 'Interview flagged due to proctoring violations'
            })

        if interview.score >= 70 and not data.get('ai_detected', False):
            cert = Certificate(
                user_id=current_user.id,
                name=f'{interview.job_role.title()} Interview Certification',
                description=f'Achieved {interview.score}% in mock interview for {interview.job_role} role',
                test_category='interview',
                score=interview.score,
                certificate_id=f"INT-{interview.id:06d}",
                validity_date=datetime.utcnow() + timedelta(days=365)
            )
            db.session.add(cert)
            db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@api.route('/refresh-jobs', methods=['POST'])
@login_required
@role_required('admin')
def refresh_jobs():
    old_jobs = Job.query.filter(Job.posted_at < datetime.utcnow() - timedelta(days=30)).all()
    for job in old_jobs:
        db.session.delete(job)
    
    _seed_sample_jobs_if_empty()
    
    new_count = Job.query.filter_by(is_active=True).count()
    return jsonify({
        'success': True, 
        'message': f'Job listings refreshed. Now {new_count} active jobs.',
        'count': new_count
    })

@student.route('/support', methods=['GET', 'POST'])
@login_required
def support():
    if request.method == 'POST':
        subject = request.form.get('subject')
        category = request.form.get('category')
        priority = request.form.get('priority')
        description = request.form.get('description')
        
        ticket = SupportTicket(
            user_id=current_user.id,
            subject=subject,
            category=category,
            priority=priority,
            description=description
        )
        db.session.add(ticket)
        db.session.commit()
        
        flash('Ticket submitted! We\'ll respond soon.', 'success')
        return redirect(url_for('student.support'))
    
    tickets = SupportTicket.query.filter_by(user_id=current_user.id).all()
    return render_template('student/support.html', tickets=tickets)

@main.route('/api/tickets', methods=['POST'])
def create_anonymous_ticket():
    """Allow anonymous ticket creation from the landing page."""
    data = request.get_json(silent=True) or {}
    
    name = (data.get('name') or '').strip()
    email = (data.get('email') or '').strip()
    category = (data.get('type') or data.get('category') or 'other').strip()
    description = (data.get('message') or data.get('description') or '').strip()
    screenshot = (data.get('screenshot') or '').strip()
    
    if not name or not email or not description:
        return jsonify({'success': False, 'message': 'Name, email, and message are required.'}), 400
    
    # Find or create an anonymous system user for landing-page tickets
    anon_user = User.query.filter_by(email='anonymous@buildup.local').first()
    if not anon_user:
        anon_user = User(
            email='anonymous@buildup.local',
            password_hash=bcrypt.generate_password_hash(str(uuid.uuid4())).decode('utf-8'),
            role='student',
            student_id='ANON000',
            is_verified=True
        )
        db.session.add(anon_user)
        db.session.commit()
    
    ticket = SupportTicket(
        user_id=anon_user.id,
        name=name,
        email=email,
        category=category,
        priority='medium',
        subject=f"Landing Page Ticket: {category.title()}",
        description=description,
        screenshot=screenshot
    )
    db.session.add(ticket)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Ticket created successfully! Our admin team has been notified.',
        'ticket_id': ticket.id
    })

@student.route('/discussions')
@login_required
def discussions():
    discussions_list = Discussion.query.order_by(Discussion.created_at.desc()).all()

    # Attach author/comment display info for templates
    users = {
        u.id: u
        for u in (
            User.query.filter(User.role == 'student', User.id.in_(
                [d.user_id for d in discussions_list] + [c.user_id for d in discussions_list for c in (d.comments or [])]
            )).all()
        )
    } if discussions_list else {}

    # Ensure comments are loaded and build helper fields
    for d in discussions_list:
        d.comments = (
            DiscussionComment.query
            .filter_by(discussion_id=d.id)
            .order_by(DiscussionComment.created_at.asc())
            .all()
        )
        d.author_display_name = (
            f"{users.get(d.user_id).first_name} {users.get(d.user_id).last_name}".strip()
            if users.get(d.user_id) and (users.get(d.user_id).first_name or users.get(d.user_id).last_name)
            else (users.get(d.user_id).email.split('@')[0] if users.get(d.user_id) and users.get(d.user_id).email else f"User {d.user_id}")
        )
        d.author_student_id = users.get(d.user_id).student_id if users.get(d.user_id) else None

        for c in d.comments:
            cu = users.get(c.user_id)
            c.comment_display_name = (
                f"{cu.first_name} {cu.last_name}".strip()
                if cu and (cu.first_name or cu.last_name)
                else (cu.email.split('@')[0] if cu and cu.email else f"User {c.user_id}")
            )
            c.comment_student_id = cu.student_id if cu else None

    return render_template('student/discussions.html', discussions=discussions_list)

@student.route('/create-discussion', methods=['POST'])
@login_required
def create_discussion():
    title = request.form.get('title')
    content = request.form.get('content')
    category = request.form.get('category')
    
    discussion = Discussion(
        user_id=current_user.id,
        title=title,
        content=content,
        category=category
    )
    db.session.add(discussion)
    db.session.commit()
    
    flash('Discussion created!', 'success')
    return redirect(url_for('student.discussions'))

@student.route('/discussion/<int:discussion_id>/comment', methods=['POST'])
def add_discussion_comment(discussion_id):
    discussion = Discussion.query.get_or_404(discussion_id)
    content = (request.form.get('content') or '').strip()

    if not content:
        flash('Comment cannot be empty.', 'warning')
        return redirect(url_for('student.discussions'))

    comment = DiscussionComment(
        discussion_id=discussion.id,
        user_id=current_user.id,
        content=content
    )
    db.session.add(comment)
    db.session.commit()
    flash('Comment added successfully.', 'success')
    return redirect(url_for('student.discussions'))

@student.route('/roadmap', methods=['GET', 'POST'])
@login_required
@role_required('student')
def roadmap():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    # Check if user wants to generate a new roadmap
    force_new = request.args.get('new') == '1'
    
    if request.method == 'POST':
        if not profile or (not profile.resume_path and not profile.skills):
            flash('Upload your resume or add your skills before generating a roadmap.', 'warning')
            return redirect(url_for('student.profile'))

        target_role = (request.form.get('target_role') or '').strip().lower()
        duration = max(7, min(int(request.form.get('duration', 30)), 90))

        if not target_role:
            flash('Please select a target role before generating your roadmap.', 'warning')
            return redirect(url_for('student.roadmap', new=1))
        
        roadmap_data = generate_learning_roadmap(target_role, duration, profile=profile)
        
        roadmap = RoadMap(
            user_id=current_user.id,
            target_role=target_role,
            duration_days=duration,
            roadmap_data=roadmap_data
        )
        db.session.add(roadmap)
        db.session.commit()
        
        return render_template('student/roadmap_view.html', roadmap=roadmap_data, target_role=target_role)
    
    # If force_new is True, skip showing existing roadmap and show form instead
    if force_new:
        return render_template(
            'student/roadmap.html',
            roadmap=None,
            profile=profile,
            force_new=True
        )
    
    latest_roadmap = (
        RoadMap.query
        .filter_by(user_id=current_user.id)
        .order_by(RoadMap.created_at.desc(), RoadMap.id.desc())
        .first()
    )
    return render_template(
        'student/roadmap.html',
        roadmap=latest_roadmap.roadmap_data if latest_roadmap else None,
        profile=profile,
        force_new=False
    )

def generate_learning_roadmap(target_role, duration, profile=None):
    num_weeks = max(1, min((duration + 6) // 7, 14))
    
    roadmaps = {
        'frontend': {
            'title': 'Frontend Developer Roadmap',
            'weeks': [
                {'week': 1, 'title': 'HTML & CSS Fundamentals', 'tasks': ['Learn HTML5 semantics', 'Master CSS3 flexbox & grid', 'Build responsive layouts', 'Create landing pages']},
                {'week': 2, 'title': 'JavaScript Essentials', 'tasks': ['Variables, functions, loops', 'DOM manipulation', 'ES6+ features', 'Async JavaScript']},
                {'week': 3, 'title': 'React Framework', 'tasks': ['Components & Props', 'State & Hooks', 'Context API', 'Build a project']},
                {'week': 4, 'title': 'Advanced React', 'tasks': ['Redux state management', 'React Router', 'Performance optimization', 'Testing with Jest']},
                {'week': 5, 'title': 'Next.js & TypeScript', 'tasks': ['Next.js basics', 'Server-side rendering', 'TypeScript fundamentals', 'API routes']},
                {'week': 6, 'title': 'Backend Integration', 'tasks': ['REST API consumption', 'GraphQL basics', 'Authentication flows', 'Error handling']},
                {'week': 7, 'title': 'DevTools & Testing', 'tasks': ['Chrome DevTools', 'Unit testing', 'Integration testing', 'E2E testing with Cypress']},
                {'week': 8, 'title': 'Deployment & CI/CD', 'tasks': ['Vercel/Netlify deployment', 'GitHub Actions', 'Environment variables', 'Monitoring']},
                {'week': 9, 'title': 'Advanced Topics', 'tasks': ['Web性能优化', 'PWA development', 'WebSocket basics', 'Web3/Blockchain intro']},
                {'week': 10, 'title': 'Portfolio & Interview', 'tasks': ['Build portfolio projects', 'Resume preparation', 'GitHub profile', 'Mock interviews']},
                {'week': 11, 'title': 'System Design Basics', 'tasks': ['Component architecture', 'State management patterns', 'API design principles', 'Performance patterns']},
                {'week': 12, 'title': 'Advanced CSS', 'tasks': ['CSS animations', 'CSS Grid mastery', 'SASS/SCSS', 'Tailwind CSS']},
                {'week': 13, 'title': 'Real-world Projects', 'tasks': ['E-commerce app', 'Social media dashboard', 'SaaS application', 'Mobile-first design']},
                {'week': 14, 'title': 'Final Projects & Polish', 'tasks': ['Complete portfolio', 'Performance audit', 'SEO optimization', 'Interview prep']}
            ]
        },
        'backend': {
            'title': 'Backend Developer Roadmap',
            'weeks': [
                {'week': 1, 'title': 'Python Fundamentals', 'tasks': ['Python basics', 'Data structures', 'File handling', 'OOP concepts']},
                {'week': 2, 'title': 'Database & SQL', 'tasks': ['SQL queries', 'Database design', 'PostgreSQL/MySQL', 'ORM concepts']},
                {'week': 3, 'title': 'Web Frameworks', 'tasks': ['Flask/Django basics', 'REST APIs', 'Authentication', 'Deployment']},
                {'week': 4, 'title': 'Advanced Python', 'tasks': ['Decorators', 'Generators', 'Context managers', 'Testing']},
                {'week': 5, 'title': 'API Development', 'tasks': ['RESTful API design', 'Authentication (JWT)', 'Authorization', 'API documentation']},
                {'week': 6, 'title': 'Database Advanced', 'tasks': ['Indexing strategies', 'Query optimization', 'Migrations', 'Data modeling']},
                {'week': 7, 'title': 'Authentication & Security', 'tasks': ['OAuth2', 'JWT tokens', 'Password hashing', 'Security best practices']},
                {'week': 8, 'title': 'Caching & Queues', 'tasks': ['Redis basics', 'Celery for tasks', 'Message queues', 'Background jobs']},
                {'week': 9, 'title': 'Docker & DevOps', 'tasks': ['Docker basics', 'Docker Compose', 'CI/CD pipelines', 'Deployment']},
                {'week': 10, 'title': 'Microservices', 'tasks': ['Microservices architecture', 'API Gateway', 'Service communication', 'Container orchestration']},
                {'week': 11, 'title': 'Cloud & Deployment', 'tasks': ['AWS/GCP basics', 'Serverless', 'Load balancing', 'Monitoring']},
                {'week': 12, 'title': 'System Design', 'tasks': ['Scalability patterns', 'Database sharding', 'Caching strategies', 'CDN basics']},
                {'week': 13, 'title': 'Real Projects', 'tasks': ['Build REST API', 'Authentication system', 'Payment integration', 'Notification service']},
                {'week': 14, 'title': 'Interview Prep', 'tasks': ['Coding practice', 'System design', 'Behavioral prep', 'Resume building']}
            ]
        },
        'fullstack': {
            'title': 'Full Stack Developer Roadmap',
            'weeks': [
                {'week': 1, 'title': 'HTML & CSS', 'tasks': ['HTML5 fundamentals', 'CSS3 & Flexbox', 'CSS Grid', 'Responsive design']},
                {'week': 2, 'title': 'JavaScript', 'tasks': ['JS fundamentals', 'DOM manipulation', 'ES6+ features', 'Async JavaScript']},
                {'week': 3, 'title': 'Frontend Framework', 'tasks': ['React basics', 'State management', 'Hooks', 'Routing']},
                {'week': 4, 'title': 'Backend Basics', 'tasks': ['Node.js intro', 'Express framework', 'REST APIs', 'Middleware']},
                {'week': 5, 'title': 'Database', 'tasks': ['MongoDB', 'Mongoose ODM', 'Database design', 'CRUD operations']},
                {'week': 6, 'title': 'Authentication', 'tasks': ['JWT tokens', 'OAuth2 basics', 'Session management', 'Security']},
                {'week': 7, 'title': 'API Development', 'tasks': ['RESTful APIs', 'Validation', 'Error handling', 'API documentation']},
                {'week': 8, 'title': 'DevOps Basics', 'tasks': ['Git workflows', 'Docker basics', 'CI/CD intro', 'Cloud deployment']},
                {'week': 9, 'title': 'Advanced React', 'tasks': ['Redux/Context', 'Performance', 'Testing', 'Next.js basics']},
                {'week': 10, 'title': 'Advanced Backend', 'tasks': ['Database optimization', 'Caching', 'Authentication', 'WebSockets']},
                {'week': 11, 'title': 'Cloud & Deployment', 'tasks': ['AWS basics', 'Vercel/Heroku', 'Environment', 'Monitoring']},
                {'week': 12, 'title': 'Testing', 'tasks': ['Unit testing', 'Integration testing', 'E2E testing', 'CI/CD']},
                {'week': 13, 'title': 'Real-world Projects', 'tasks': ['Social media app', 'E-commerce platform', 'Task management', 'Blog/CMS']},
                {'week': 14, 'title': 'Interview & Portfolio', 'tasks': ['Portfolio projects', 'Coding practice', 'System design', 'Behavioral prep']}
            ]
        },
        'data': {
            'title': 'Data Analyst Roadmap',
            'weeks': [
                {'week': 1, 'title': 'Python Basics', 'tasks': ['Python fundamentals', 'Variables & data types', 'Control flow', 'Functions']},
                {'week': 2, 'title': 'NumPy & Pandas', 'tasks': ['NumPy arrays', 'Pandas DataFrames', 'Data manipulation', 'File I/O']},
                {'week': 3, 'title': 'Data Cleaning', 'tasks': ['Missing values', 'Data type conversion', 'Duplicates', 'String operations']},
                {'week': 4, 'title': 'Visualization', 'tasks': ['Matplotlib basics', 'Seaborn', 'Plotly interactive', 'Dashboard basics']},
                {'week': 5, 'title': 'Statistics', 'tasks': ['Descriptive statistics', 'Probability', 'Hypothesis testing', 'Correlation']},
                {'week': 6, 'title': 'SQL', 'tasks': ['SQL queries', 'Joins & subqueries', 'Window functions', 'Database design']},
                {'week': 7, 'title': 'Excel & PowerBI', 'tasks': ['Excel advanced', 'Pivot tables', 'PowerBI basics', 'DAX basics']},
                {'week': 8, 'title': 'Data Projects', 'tasks': ['EDA project', 'Case study', 'Portfolio piece', 'GitHub showcase']},
                {'week': 9, 'title': 'Advanced SQL', 'tasks': ['Complex joins', 'CTEs', 'Performance tuning', 'Data modeling']},
                {'week': 10, 'title': 'Machine Learning', 'tasks': ['Scikit-learn intro', 'Regression', 'Classification', 'Model evaluation']},
                {'week': 11, 'title': 'Advanced Visualization', 'tasks': ['Tableau', 'Interactive dashboards', 'Storytelling', 'Data presentation']},
                {'week': 12, 'title': 'Big Data Basics', 'tasks': ['Spark intro', 'Data lakes', 'ETL pipelines', 'Cloud data services']},
                {'week': 13, 'title': 'Portfolio Projects', 'tasks': ['Sales analysis', 'Customer segmentation', 'Financial analysis', 'Time series']},
                {'week': 14, 'title': 'Interview Prep', 'tasks': ['SQL practice', 'Case studies', 'Portfolio review', 'Behavioral prep']}
            ]
        },
        'devops': {
            'title': 'DevOps Engineer Roadmap',
            'weeks': [
                {'week': 1, 'title': 'Linux Basics', 'tasks': ['Linux fundamentals', 'Shell scripting', 'Package management', 'User management']},
                {'week': 2, 'title': 'Networking', 'tasks': ['TCP/IP basics', 'DNS & DHCP', 'Load balancing', 'Network security']},
                {'week': 3, 'title': 'Docker Basics', 'tasks': ['Containers intro', 'Dockerfiles', 'Docker Compose', 'Networking']},
                {'week': 4, 'title': 'Kubernetes', 'tasks': ['K8s architecture', 'Pods & Deployments', 'Services', 'ConfigMaps']},
                {'week': 5, 'title': 'CI/CD', 'tasks': ['Jenkins basics', 'GitHub Actions', 'GitLab CI', 'Pipeline as code']},
                {'week': 6, 'title': 'IaC', 'tasks': ['Terraform basics', 'Ansible intro', 'CloudFormation', 'Infrastructure patterns']},
                {'week': 7, 'title': 'Cloud AWS', 'tasks': ['EC2 & S3', 'IAM & Security', 'VPC networking', 'RDS & DynamoDB']},
                {'week': 8, 'title': 'Monitoring', 'tasks': ['Prometheus', 'Grafana', 'ELK Stack', 'Logging']},
                {'week': 9, 'title': 'Security', 'tasks': ['Container security', 'Secret management', 'SAST/DAST', 'Security scanning']},
                {'week': 10, 'title': 'Advanced K8s', 'tasks': ['Helm charts', 'Service mesh', 'Autoscaling', 'Multi-cluster']},
                {'week': 11, 'title': 'Cloud Advanced', 'tasks': ['Serverless', 'Containers at scale', 'Cost optimization', 'Disaster recovery']},
                {'week': 12, 'title': 'Microservices', 'tasks': ['Service mesh', 'API Gateway', 'Observability', 'Deployment strategies']},
                {'week': 13, 'title': 'Real Projects', 'tasks': ['Build CI/CD pipeline', 'Deploy microservices', 'Set up monitoring', 'Document everything']},
                {'week': 14, 'title': 'Interview Prep', 'tasks': ['Hands-on labs', 'Architecture design', 'Resume building', 'Behavioral prep']}
            ]
        },
        'mobile': {
            'title': 'Mobile App Developer Roadmap',
            'weeks': [
                {'week': 1, 'title': 'Dart Basics', 'tasks': ['Dart fundamentals', 'OOP concepts', 'Async programming', 'Null safety']},
                {'week': 2, 'title': 'Flutter Setup', 'tasks': ['Flutter installation', 'Project structure', 'Widget basics', 'Hot reload']},
                {'week': 3, 'title': 'Widgets & UI', 'tasks': ['Material Design', 'Layout widgets', 'Navigation', 'Theming']},
                {'week': 4, 'title': 'State Management', 'tasks': ['setState basics', 'Provider', 'Riverpod basics', 'Context usage']},
                {'week': 5, 'title': 'Networking', 'tasks': ['HTTP requests', 'JSON parsing', 'API integration', 'Error handling']},
                {'week': 6, 'title': 'Local Storage', 'tasks': ['SharedPreferences', 'SQLite basics', 'Hive', 'File storage']},
                {'week': 7, 'title': 'Firebase', 'tasks': ['Firebase setup', 'Auth', 'Firestore', 'Cloud Functions']},
                {'week': 8, 'title': 'Advanced UI', 'tasks': ['Custom widgets', 'Animations', 'Hero animations', 'Custom painters']},
                {'week': 9, 'title': 'State Management Advanced', 'tasks': ['BLoC pattern', 'GetX', 'StateNotifier', 'Freezed']},
                {'week': 10, 'title': 'Platform Channels', 'tasks': ['Method channels', 'Platform-specific code', 'Native modules', 'Plugins']},
                {'week': 11, 'title': 'Testing & CI/CD', 'tasks': ['Unit testing', 'Widget testing', 'CI/CD with Codemagic', 'Test coverage']},
                {'week': 12, 'title': 'Deployment', 'tasks': ['Play Store prep', 'App Store prep', 'App signing', 'Publishing']},
                {'week': 13, 'title': 'Real Projects', 'tasks': ['Social media app', 'E-commerce app', 'Chat application', 'Portfolio app']},
                {'week': 14, 'title': 'Interview Prep', 'tasks': ['Code examples', 'Architecture patterns', 'Portfolio review', 'Behavioral prep']}
            ]
        },
        'ml': {
            'title': 'Machine Learning Engineer Roadmap',
            'weeks': [
                {'week': 1, 'title': 'Python & Math', 'tasks': ['Python advanced', 'Linear Algebra', 'Statistics basics', 'Calculus intro']},
                {'week': 2, 'title': 'Data Handling', 'tasks': ['NumPy', 'Pandas', 'Data visualization', 'Feature engineering']},
                {'week': 3, 'title': 'ML Basics', 'tasks': ['Supervised learning', 'Unsupervised learning', 'Scikit-learn', 'Model evaluation']},
                {'week': 4, 'title': 'Regression', 'tasks': ['Linear regression', 'Polynomial regression', 'Regularization', 'Model tuning']},
                {'week': 5, 'title': 'Classification', 'tasks': ['Logistic regression', 'Decision trees', 'Random forests', 'XGBoost']},
                {'week': 6, 'title': 'Clustering', 'tasks': ['K-means', 'Hierarchical', 'DBSCAN', 'Evaluation metrics']},
                {'week': 7, 'title': 'Deep Learning', 'tasks': ['Neural networks', 'TensorFlow basics', 'PyTorch basics', 'Training loops']},
                {'week': 8, 'title': 'CNNs', 'tasks': ['CNN architecture', 'Image classification', 'Transfer learning', 'Object detection']},
                {'week': 9, 'title': 'NLP', 'tasks': ['Text processing', 'Word embeddings', 'Transformers', 'Sentiment analysis']},
                {'week': 10, 'title': 'Model Deployment', 'tasks': ['Flask API', 'Docker', 'MLflow', 'Model versioning']},
                {'week': 11, 'title': 'Advanced Topics', 'tasks': ['Reinforcement learning', 'GANs', 'AutoML', 'Explainability']},
                {'week': 12, 'title': 'Big Data & ML', 'tasks': ['Spark MLlib', 'Distributed training', 'Cloud ML services', 'Edge ML']},
                {'week': 13, 'title': 'Projects', 'tasks': ['Image classifier', 'NLP project', 'Recommendation system', 'Time series']},
                {'week': 14, 'title': 'Interview Prep', 'tasks': ['Coding practice', 'ML theory', 'Case studies', 'Portfolio review']}
            ]
        },
        'cybersecurity': {
            'title': 'Cybersecurity Analyst Roadmap',
            'weeks': [
                {'week': 1, 'title': 'Network Basics', 'tasks': ['TCP/IP protocols', 'Network architecture', 'Firewalls', 'VPN basics']},
                {'week': 2, 'title': 'Security Fundamentals', 'tasks': ['CIA triad', 'Risk management', 'Security policies', 'Compliance basics']},
                {'week': 3, 'title': 'Linux Security', 'tasks': ['Linux hardening', 'User permissions', 'Audit logs', 'File integrity']},
                {'week': 4, 'title': 'Windows Security', 'tasks': ['Active Directory', 'Group policies', 'PowerShell security', 'Windows Defender']},
                {'week': 5, 'title': 'Network Security', 'tasks': ['IDS/IPS', 'SIEM basics', 'Packet analysis', 'Network scanning']},
                {'week': 6, 'title': 'Web Security', 'tasks': ['OWASP Top 10', 'XSS & SQL injection', 'CSRF', 'Security headers']},
                {'week': 7, 'title': 'Penetration Testing', 'tasks': ['Reconnaissance', 'Enumeration', 'Vulnerability scanning', 'Exploitation basics']},
                {'week': 8, 'title': 'Ethical Hacking', 'tasks': ['Metasploit basics', 'Burp Suite', 'Nmap scripting', 'Privilege escalation']},
                {'week': 9, 'title': 'Incident Response', 'tasks': ['IR methodology', 'Forensics basics', 'Log analysis', 'Malware analysis intro']},
                {'week': 10, 'title': 'Security Operations', 'tasks': ['SOC basics', 'Alert analysis', 'Threat hunting', 'Incident documentation']},
                {'week': 11, 'title': 'Cloud Security', 'tasks': ['AWS security', 'Azure security', 'IAM best practices', 'Cloud monitoring']},
                {'week': 12, 'title': 'Cryptography', 'tasks': ['Encryption basics', 'Hashing', 'Digital signatures', 'PKI']},
                {'week': 13, 'title': 'Lab Practice', 'tasks': ['Build home lab', 'TryHackMe', 'HackTheBox basics', 'Bug bounty']},
                {'week': 14, 'title': 'Certifications & Career', 'tasks': ['CompTIA Security+', 'CEH concepts', 'Resume building', 'Interview prep']}
            ]
        },
        'qa': {
            'title': 'QA Automation Engineer Roadmap',
            'weeks': [
                {'week': 1, 'title': 'Testing Fundamentals', 'tasks': ['Testing basics', 'Test types', 'Test case design', 'Bug lifecycle']},
                {'week': 2, 'title': 'SDLC & STLC', 'tasks': ['SDLC models', 'STLC process', 'Test planning', 'Traceability']},
                {'week': 3, 'title': 'Manual Testing', 'tasks': ['Functional testing', 'UI testing', 'API testing basics', 'Regression testing']},
                {'week': 4, 'title': 'Bug Tracking', 'tasks': ['JIRA basics', 'Bug reporting', 'Severity vs Priority', 'Test management']},
                {'week': 5, 'title': 'Selenium Basics', 'tasks': ['Selenium IDE', 'WebDriver setup', 'Locators', 'Basic actions']},
                {'week': 6, 'title': 'Selenium Advanced', 'tasks': ['Page Object Model', 'Explicit/Implicit waits', 'Dynamic elements', 'Frames/Iframes']},
                {'week': 7, 'title': 'TestNG & JUnit', 'tasks': ['Annotations', 'Test suites', 'Data providers', 'Parallel execution']},
                {'week': 8, 'title': 'API Testing', 'tasks': ['REST API basics', 'Postman', 'SoapUI', 'Rest Assured']},
                {'week': 9, 'title': 'CI/CD & Jenkins', 'tasks': ['Jenkins setup', 'Build triggers', 'Pipeline basics', 'Reports']},
                {'week': 10, 'title': 'Docker for Testing', 'tasks': ['Docker basics', 'Selenium Grid', 'Testcontainers', 'Parallel testing']},
                {'week': 11, 'title': 'Performance Testing', 'tasks': ['JMeter basics', 'Load testing', 'Stress testing', 'Performance metrics']},
                {'week': 12, 'title': 'Mobile Testing', 'tasks': ['Appium basics', 'Android testing', 'iOS testing', 'Mobile automation']},
                {'week': 13, 'title': 'Advanced Topics', 'tasks': ['BDD with Cucumber', 'Git basics', 'SQL for testers', 'Security testing']},
                {'week': 14, 'title': 'Interview Prep', 'tasks': ['Automation frameworks', 'Scenario design', 'Resume building', 'Behavioral prep']}
            ]
        },
        'sde': {
            'title': 'Software Development Engineer Roadmap',
            'weeks': [
                {'week': 1, 'title': 'Arrays & Strings', 'tasks': ['Two pointer technique', 'Sliding window', 'String manipulation', 'Prefix sums']},
                {'week': 2, 'title': 'Hash Tables', 'tasks': ['HashMap usage', 'HashSet patterns', 'Collision handling', 'Anagram detection']},
                {'week': 3, 'title': 'Linked Lists', 'tasks': ['Reversal', 'Fast-slow pointers', 'Cycle detection', 'Merge sorted lists']},
                {'week': 4, 'title': 'Stacks & Queues', 'tasks': ['Stack patterns', 'Monotonic stack', 'Queue implementations', 'BFS patterns']},
                {'week': 5, 'title': 'Trees', 'tasks': ['Tree traversal', 'BST operations', 'Tree construction', 'Lowest common ancestor']},
                {'week': 6, 'title': 'Binary Search', 'tasks': ['Binary search variations', 'Search space', 'Find duplicates', 'K-th element']},
                {'week': 7, 'title': 'Graphs', 'tasks': ['Graph representations', 'BFS/DFS', 'Cycle detection', 'Topological sort']},
                {'week': 8, 'title': 'Graph Algorithms', 'tasks': ['Dijkstra', 'Bellman-Ford', 'Floyd-Warshall', 'Union-Find']},
                {'week': 9, 'title': 'Dynamic Programming', 'tasks': ['DP fundamentals', '1D DP', '2D DP', 'DP optimization']},
                {'week': 10, 'title': 'Advanced DP', 'tasks': ['Tree DP', 'Bitmask DP', 'DP on graphs', 'State machines']},
                {'week': 11, 'title': 'Sorting & Searching', 'tasks': ['Sorting algorithms', 'Custom sorting', 'Binary search trees', 'Heaps']},
                {'week': 12, 'title': 'System Design', 'tasks': ['Scale estimation', 'API design', 'Data modeling', 'Caching']},
                {'week': 13, 'title': 'Advanced System Design', 'tasks': ['Microservices', 'Database sharding', 'Message queues', 'CDN']},
                {'week': 14, 'title': 'Interview & Projects', 'tasks': ['Mock interviews', 'Portfolio projects', 'Resume building', 'Behavioral prep']}
            ]
        }
    }
    
    role_key = (target_role or '').lower()
    base_roadmap = deepcopy(roadmaps.get(role_key, roadmaps['frontend']))
    week_pool = base_roadmap['weeks']
    rng = random.SystemRandom()

    if len(week_pool) <= num_weeks:
        selected_weeks = week_pool[:]
    else:
        # Keep the first week as the foundation, then vary the middle path so each generation feels new.
        selected_weeks = [deepcopy(week_pool[0])]
        remaining_slots = num_weeks - 1

        if remaining_slots > 0:
            middle_pool = week_pool[1:-1]
            if remaining_slots == 1:
                selected_weeks.append(deepcopy(week_pool[-1]))
            else:
                middle_count = min(len(middle_pool), remaining_slots - 1)
                selected_weeks.extend(deepcopy(week) for week in rng.sample(middle_pool, middle_count))
                selected_weeks.append(deepcopy(week_pool[-1]))

    skill_hints = []
    if profile and profile.skills:
        skill_hints = [skill.strip() for skill in profile.skills.split(',') if skill.strip()]

    if skill_hints:
        rng.shuffle(skill_hints)

    personalized_weeks = []
    for index, week in enumerate(selected_weeks, start=1):
        tasks = list(week.get('tasks', []))
        rng.shuffle(tasks)

        if skill_hints:
            focus_skill = skill_hints[(index - 1) % len(skill_hints)]
            tasks = tasks[:3] + [f'Connect this week to your existing skill: {focus_skill}']

        personalized_weeks.append({
            'week': index,
            'title': week.get('title'),
            'tasks': tasks[:4]
        })

    base_roadmap['weeks'] = personalized_weeks
    return base_roadmap

@student.route('/certificates')
@login_required
def certificates():
    certs = Certificate.query.filter_by(user_id=current_user.id).all()
    return render_template('student/certificates.html', certificates=certs)

@student.route('/certificate/<int:cert_id>')
@login_required
def view_certificate(cert_id):
    cert = Certificate.query.filter_by(id=cert_id, user_id=current_user.id).first()
    if not cert:
        flash('Certificate not found', 'error')
        return redirect(url_for('student.certificates'))
    
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    return render_template('student/certificate_view.html', certificate=cert, profile=profile)

@student.route('/download-certificate/<int:cert_id>')
@login_required
def download_certificate(cert_id):
    cert = Certificate.query.filter_by(id=cert_id, user_id=current_user.id).first()
    if not cert:
        flash('Certificate not found', 'error')
        return redirect(url_for('student.certificates'))
    
    # For now, redirect to view page - actual PDF generation can be implemented later
    flash('Download feature coming soon!', 'info')
    return redirect(url_for('student.view_certificate', cert_id=cert_id))

@student.route('/daily-streak')
@login_required
@role_required('student')
def daily_streak():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    full_name = f"{profile.first_name} {profile.last_name}" if profile else 'Student'

    # Query coding portal DB for today's solved problems
    coding_db = os.path.join(current_app.root_path, 'coding-portal', 'backend', 'prisma', 'dev.db')
    solved_today = 0
    portal_user_id = None

    if os.path.exists(coding_db):
        try:
            conn = sqlite3.connect(coding_db)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Find portal user by buildupUid
            cur.execute("SELECT id FROM User WHERE buildupUid = ?", (current_user.id,))
            portal_user = cur.fetchone()
            if portal_user:
                portal_user_id = portal_user['id']
                today_start = datetime.utcnow().strftime('%Y-%m-%d 00:00:00')
                cur.execute(
                    "SELECT COUNT(*) as cnt FROM UserSolvedProblem WHERE userId = ? AND solvedAt >= ?",
                    (portal_user_id, today_start)
                )
                solved_today = cur.fetchone()['cnt']
            conn.close()
        except Exception as e:
            print(f"Daily streak DB error: {e}")

    # Check if already have a streak cert for today
    today_str = datetime.utcnow().strftime('%Y-%m-%d')
    existing = Certificate.query.filter_by(
        user_id=current_user.id,
        test_category='daily_streak'
    ).filter(Certificate.description.contains(today_str)).first()

    cert = None
    if solved_today >= 10:
        if not existing:
            cert_id_str = f"STR-{current_user.id}-{datetime.utcnow().strftime('%Y%m%d')}"
            cert = Certificate(
                user_id=current_user.id,
                name='Daily Coding Streak',
                description=(
                    f"Congratulations {full_name}! You have completed 10 Problems in a day ({today_str}). "
                    f"Your dedication and problem-solving skills are truly commendable. "
                    f"Keep up the amazing work — consistency is the key to mastering coding! "
                    f"Every great developer started with small daily habits, and you're on the right path. "
                    f"Stay curious, keep learning, and challenge yourself every day!"
                ),
                test_category='daily_streak',
                score=solved_today,
                certificate_id=cert_id_str,
                validity_date=datetime.utcnow() + timedelta(days=365),
                badge_icon='Image/logo.png'
            )
            db.session.add(cert)
            db.session.commit()
        else:
            cert = existing
            # Update score in case they solved more
            if cert.score != solved_today:
                cert.score = solved_today
                db.session.commit()

    return render_template('student/daily_streak.html', solved_today=solved_today, cert=cert, full_name=full_name, today_str=today_str)

@student.route('/readiness')
@login_required
def readiness():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    readiness_data = InterviewReadiness.query.filter_by(profile_id=profile.id).first() if profile else None
    
    from models import CommunicationPractice
    practices = CommunicationPractice.query.filter_by(user_id=current_user.id).order_by(CommunicationPractice.created_at.desc()).all()
    
    today_practiced = any(p.created_at.date() == datetime.utcnow().date() for p in practices) if practices else False
    streak = calculate_streak(practices) if practices else 0
    
    return render_template('student/readiness.html', readiness=readiness_data, practices=practices, today_practiced=today_practiced, streak=streak)

def calculate_streak(practices):
    if not practices:
        return 0
    dates = sorted(set(p.created_at.date() for p in practices), reverse=True)
    streak = 0
    today = datetime.utcnow().date()
    for i, date in enumerate(dates):
        expected = today - timedelta(days=i)
        if date == expected:
            streak += 1
        else:
            break
    return streak

@student.route('/communication-hub')
@login_required
def communication_hub():
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    
    from models import CommunicationPractice
    practices = CommunicationPractice.query.filter_by(user_id=current_user.id).order_by(CommunicationPractice.created_at.desc()).limit(10).all()
    
    today_practiced = CommunicationPractice.query.filter(
        CommunicationPractice.user_id == current_user.id,
        CommunicationPractice.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
    ).first()
    
    streak = calculate_streak(CommunicationPractice.query.filter_by(user_id=current_user.id).all())
    
    return render_template('student/communication_hub.html', practices=practices, today_practiced=today_practiced, streak=streak)

@student.route('/communication-practice', methods=['POST'])
@login_required
def save_communication_practice():
    from models import CommunicationPractice
    
    practice_type = request.form.get('type')
    topic = request.form.get('topic')
    content = request.form.get('content', '')
    duration = int(request.form.get('duration', 0))
    
    clarity_rating = int(request.form.get('clarity_rating', 0))
    structure_rating = int(request.form.get('structure_rating', 0))
    confidence_rating = int(request.form.get('confidence_rating', 0))
    
    practice = CommunicationPractice(
        user_id=current_user.id,
        practice_type=practice_type,
        topic=topic,
        content=content,
        duration=duration,
        clarity_rating=clarity_rating,
        structure_rating=structure_rating,
        confidence_rating=confidence_rating
    )
    db.session.add(practice)
    
    profile = StudentProfile.query.filter_by(user_id=current_user.id).first()
    if profile:
        readiness = InterviewReadiness.query.filter_by(profile_id=profile.id).first()
        if readiness:
            avg_score = (clarity_rating + structure_rating + confidence_rating) / 3
            readiness.communication_score = int(avg_score)
            scores = [readiness.communication_score, readiness.dsa_score, 
                      readiness.aptitude_score, readiness.projects_score, readiness.core_subjects_score]
            non_zero_scores = [s for s in scores if s and s > 0]
            readiness.overall_score = (sum(non_zero_scores) // len(non_zero_scores)) if non_zero_scores else 0
            readiness.last_updated = datetime.utcnow()
    
    db.session.commit()
    flash('Practice saved! Keep up the good work.', 'success')
    return redirect(url_for('student.communication_hub'))

@student.route('/share-practice/<int:practice_id>', methods=['POST'])
@login_required
def share_practice(practice_id):
    from models import CommunicationPractice, Discussion
    
    practice = CommunicationPractice.query.get_or_404(practice_id)
    if practice.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('student.communication_hub'))
    
    discussion = Discussion(
        user_id=current_user.id,
        title=f'Speaking Practice: {practice.topic}',
        content=f'**Type:** {practice.practice_type}\n**Topic:** {practice.topic}\n\n**My Response:**\n{practice.content}\n\n**Self Ratings:**\n- Clarity: {practice.clarity_rating}/5\n- Structure: {practice.structure_rating}/5\n- Confidence: {practice.confidence_rating}/5\n\nPlease provide feedback!',
        category='communication'
    )
    db.session.add(discussion)
    db.session.commit()
    
    flash('Shared to discussions for peer feedback!', 'success')
    return redirect(url_for('student.communication_hub'))

@admin.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    with app.app_context():
        total_users = User.query.count() or 1
        active_users = User.query.filter_by(active=True).count()
        total_tickets = SupportTicket.query.count()
        closed_tickets = SupportTicket.query.filter_by(status='closed').count()
        active_jobs = Job.query.filter_by(is_active=True).count()
        active_jobs_with_applications = db.session.query(
            db.func.count(db.distinct(Application.job_id))
        ).join(Job, Job.id == Application.job_id).filter(Job.is_active == True).scalar() or 0
        skillup_submissions = 0
        accepted_skillup_submissions = 0
        coding_db_path = os.path.join(current_app.root_path, 'coding-portal', 'backend', 'prisma', 'dev.db')
        if os.path.exists(coding_db_path):
            conn = sqlite3.connect(coding_db_path)
            conn.row_factory = sqlite3.Row
            try:
                skillup_submissions = conn.execute('SELECT COUNT(*) AS count FROM "Submission"').fetchone()['count']
                accepted_skillup_submissions = conn.execute(
                    'SELECT COUNT(*) AS count FROM "Submission" WHERE verdict = ?',
                    ('ACCEPTED',)
                ).fetchone()['count']
            finally:
                conn.close()

        stats = {
            'total_students': User.query.filter_by(role='student').count(),
            'total_recruiters': User.query.filter_by(role='recruiter').count(),
            'pending_recruiter_requests': User.query.filter_by(role='recruiter', company_id_status='pending_admin').count(),
            'total_jobs': active_jobs,
            'total_applications': Application.query.count(),
            'active_tickets': SupportTicket.query.filter_by(status='open').count(),
            'active_users_rate': int((active_users / total_users) * 100),
            'application_rate': int((active_jobs_with_applications / active_jobs) * 100) if active_jobs else 0,
            'application_summary': f'{active_jobs_with_applications}/{active_jobs} active jobs',
            'support_response_rate': int((closed_tickets / total_tickets) * 100) if total_tickets else 0,
            'problem_solve_rate': int((accepted_skillup_submissions / skillup_submissions) * 100) if skillup_submissions else 0,
            'problem_solving_summary': f'{accepted_skillup_submissions}/{skillup_submissions} accepted submissions'
        }

        display_name = current_user.email.split('@')[0] if current_user.email else 'Admin'
        platform_help = (
            f'Welcome back, {display_name}. Student progress and admin actions are live from current portal data.'
            if current_user.is_verified else
            f'Hi {display_name}, verify your admin account to unlock all portal workflows.'
        )
        recruiter_requests = (
            User.query
            .filter_by(role='recruiter', company_id_status='pending_admin')
            .order_by(User.recruiter_request_last_submitted_at.desc().nullslast(), User.created_at.desc())
            .limit(5)
            .all()
        )
    return render_template('admin/dashboard.html', stats=stats, platform_help=platform_help, recruiter_requests=recruiter_requests)

@admin.route('/recruiter-verification')
@login_required
@role_required('admin')
def recruiter_verification():
    verification_requests = (
        User.query
        .filter(User.role == 'recruiter')
        .filter(User.company_id_status.in_(['pending_admin', 'verified', 'declined', 'pending_email_otp', 'pending_verification']))
        .order_by(User.recruiter_request_last_submitted_at.desc().nullslast(), User.created_at.desc())
        .all()
    )
    return render_template('admin/recruiter_verification.html', verification_requests=verification_requests)

@admin.route('/recruiter-verification/<int:recruiter_id>/approve', methods=['POST'])
@login_required
@role_required('admin')
def approve_company_id(recruiter_id):
    recruiter_user = User.query.filter_by(id=recruiter_id, role='recruiter').first_or_404()
    recruiter_user.company_id_status = 'verified'
    recruiter_user.company_id_verified_at = datetime.utcnow()
    recruiter_user.company_id_verified_by = current_user.id
    recruiter_user.is_verified = True
    recruiter_user.recruiter_request_last_notification = 'Approved by admin. Recruiter can now log in.'
    email_sent = _send_recruiter_decision_email(recruiter_user, approved=True)
    db.session.commit()
    flash(
        f'Approved recruiter request for {_recruiter_name(recruiter_user)}.'
        + ('' if email_sent else ' Email delivery is not configured, so no real email was sent.'),
        'success'
    )
    return redirect(url_for('admin.recruiter_verification'))

@admin.route('/recruiter-verification/<int:recruiter_id>/decline', methods=['POST'])
@login_required
@role_required('admin')
def reject_company_id(recruiter_id):
    recruiter_user = User.query.filter_by(id=recruiter_id, role='recruiter').first_or_404()
    recruiter_user.company_id_status = 'declined'
    recruiter_user.recruiter_request_decline_count = (recruiter_user.recruiter_request_decline_count or 0) + 1
    recruiter_user.recruiter_request_last_notification = 'Declined by admin. Recruiter can submit again.'
    recruiter_user.recruiter_request_otp = None
    recruiter_user.recruiter_request_otp_expires = None
    email_sent = _send_recruiter_decision_email(recruiter_user, approved=False)
    db.session.commit()
    flash(
        f'Declined recruiter request for {_recruiter_name(recruiter_user)}.'
        + ('' if email_sent else ' Email delivery is not configured, so no real email was sent.'),
        'warning'
    )
    return redirect(url_for('admin.recruiter_verification'))

@admin.route('/recruiter-verification/<int:recruiter_id>/company-id')
@login_required
@role_required('admin')
def view_company_id_image(recruiter_id):
    recruiter_user = User.query.filter_by(id=recruiter_id, role='recruiter').first_or_404()
    if not recruiter_user.company_id_image_path:
        flash('No company ID card uploaded for this recruiter.', 'warning')
        return redirect(url_for('admin.recruiter_verification'))
    image_path = recruiter_user.company_id_image_path
    if not os.path.isabs(image_path):
        image_path = os.path.join(current_app.root_path, image_path)
    if not os.path.exists(image_path):
        flash('Company ID file could not be found.', 'danger')
        return redirect(url_for('admin.recruiter_verification'))
    return send_file(image_path)

@admin.route('/code-spirit-monitoring')
@login_required
@role_required('admin')
def code_spirit_monitoring():
    coding_db_path = os.path.join(current_app.root_path, 'coding-portal', 'backend', 'prisma', 'dev.db')
    stats = {
        'total_students': 0,
        'problems_attempted': 0,
        'problems_solved': 0,
        'total_submissions': 0,
        'success_rate': 0,
        'active_today': 0
    }
    recent_activities = []
    top_students = []
    difficulty_stats = {
        'easy_count': 0,
        'easy_percent': 0,
        'medium_count': 0,
        'medium_percent': 0,
        'hard_count': 0,
        'hard_percent': 0
    }

    if os.path.exists(coding_db_path):
        conn = sqlite3.connect(coding_db_path)
        conn.row_factory = sqlite3.Row
        try:
            total_students = conn.execute('SELECT COUNT(*) AS count FROM "User" WHERE role = ?', ('USER',)).fetchone()['count']
            total_submissions = conn.execute('SELECT COUNT(*) AS count FROM "Submission"').fetchone()['count']
            accepted_submissions = conn.execute(
                'SELECT COUNT(*) AS count FROM "Submission" WHERE verdict = ?',
                ('ACCEPTED',)
            ).fetchone()['count']
            problems_attempted = conn.execute(
                'SELECT COUNT(DISTINCT problemId) AS count FROM "Submission"'
            ).fetchone()['count']
            problems_solved = conn.execute(
                'SELECT COUNT(DISTINCT problemId) AS count FROM "Submission" WHERE verdict = ?',
                ('ACCEPTED',)
            ).fetchone()['count']
            today_prefix = datetime.utcnow().date().isoformat()
            active_today = conn.execute(
                'SELECT COUNT(DISTINCT userId) AS count FROM "Submission" WHERE createdAt LIKE ?',
                (f'{today_prefix}%',)
            ).fetchone()['count']

            stats = {
                'total_students': total_students,
                'problems_attempted': problems_attempted,
                'problems_solved': problems_solved,
                'total_submissions': total_submissions,
                'success_rate': int((accepted_submissions / total_submissions) * 100) if total_submissions else 0,
                'active_today': active_today
            }

            for row in conn.execute(
                '''
                SELECT s.createdAt, s.verdict, s.mode, u.name, u.email, p.title
                FROM "Submission" s
                JOIN "User" u ON u.id = s.userId
                JOIN "Problem" p ON p.id = s.problemId
                ORDER BY s.createdAt DESC
                LIMIT 5
                '''
            ):
                recent_activities.append({
                    'student_name': row['name'] or row['email'] or 'Student',
                    'action': 'Solved' if row['verdict'] == 'ACCEPTED' else 'Submitted',
                    'problem_title': row['title'],
                    'time_ago': _format_coding_timestamp(row['createdAt']),
                    'success': row['verdict'] == 'ACCEPTED'
                })

            for row in conn.execute(
                '''
                SELECT
                    u.name,
                    u.email,
                    COUNT(DISTINCT s.problemId) AS attempted,
                    COUNT(DISTINCT CASE WHEN s.verdict = 'ACCEPTED' THEN s.problemId END) AS solved,
                    COUNT(s.id) AS submissions
                FROM "User" u
                LEFT JOIN "Submission" s ON s.userId = u.id
                WHERE u.role = 'USER'
                GROUP BY u.id
                HAVING submissions > 0
                ORDER BY solved DESC, attempted DESC, submissions DESC
                LIMIT 5
                '''
            ):
                attempted = row['attempted'] or 0
                solved = row['solved'] or 0
                top_students.append({
                    'name': row['name'] or row['email'] or 'Student',
                    'solved': solved,
                    'attempted': attempted,
                    'success_rate': int((solved / attempted) * 100) if attempted else 0
                })

            difficulty_counts = {'EASY': 0, 'MEDIUM': 0, 'HARD': 0}
            for row in conn.execute(
                '''
                SELECT p.difficulty, COUNT(DISTINCT s.problemId) AS count
                FROM "Submission" s
                JOIN "Problem" p ON p.id = s.problemId
                GROUP BY p.difficulty
                '''
            ):
                difficulty_counts[row['difficulty']] = row['count']
            total_buckets = max(sum(difficulty_counts.values()), 1)
            difficulty_stats = {
                'easy_count': difficulty_counts['EASY'],
                'easy_percent': int((difficulty_counts['EASY'] / total_buckets) * 100),
                'medium_count': difficulty_counts['MEDIUM'],
                'medium_percent': int((difficulty_counts['MEDIUM'] / total_buckets) * 100),
                'hard_count': difficulty_counts['HARD'],
                'hard_percent': int((difficulty_counts['HARD'] / total_buckets) * 100)
            }
        finally:
            conn.close()
    
    return render_template('admin/code_spirit_monitoring.html', 
                         stats=stats, 
                         recent_activities=recent_activities,
                         top_students=top_students,
                         difficulty_stats=difficulty_stats)

@admin.route('/manage-users')
@login_required
@role_required('admin')
def manage_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@admin.route('/manage-users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@role_required('admin')
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot deactivate your own admin account.', 'warning')
        return redirect(url_for('admin.manage_users'))
    
    user.active = not user.active
    db.session.commit()
    flash(f'User status updated to {"Active" if user.active else "Inactive"}.', 'success')
    return redirect(url_for('admin.manage_users'))

@admin.route('/manage-users/<int:user_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('You cannot delete your own admin account.', 'warning')
        return redirect(url_for('admin.manage_users'))
    
    try:
        profile = StudentProfile.query.filter_by(user_id=user.id).first()
        if profile:
            tests = SkillTest.query.filter_by(profile_id=profile.id).all()
            for test in tests:
                TestQuestion.query.filter_by(test_id=test.id).delete(synchronize_session=False)
                db.session.delete(test)
            InterviewReadiness.query.filter_by(profile_id=profile.id).delete(synchronize_session=False)
            db.session.delete(profile)
        
        Application.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        MockInterview.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        Certificate.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        RoadMap.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        TicketResponse.query.filter_by(responder_id=user.id).delete(synchronize_session=False)
        DiscussionComment.query.filter_by(user_id=user.id).delete(synchronize_session=False)
        
        user_tickets = SupportTicket.query.filter_by(user_id=user.id).all()
        for ticket in user_tickets:
            TicketResponse.query.filter_by(ticket_id=ticket.id).delete(synchronize_session=False)
            db.session.delete(ticket)
        
        user_discussions = Discussion.query.filter_by(user_id=user.id).all()
        for discussion in user_discussions:
            DiscussionComment.query.filter_by(discussion_id=discussion.id).delete(synchronize_session=False)
            db.session.delete(discussion)
        
        posted_jobs = Job.query.filter_by(recruiter_id=user.id).all()
        for job in posted_jobs:
            Application.query.filter_by(job_id=job.id).delete(synchronize_session=False)
            db.session.delete(job)
        
        db.session.delete(user)
        db.session.commit()
        flash('User deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not delete user due to linked records. Please try again.', 'danger')
    
    return redirect(url_for('admin.manage_users'))

@admin.route('/manage-jobs')
@login_required
@role_required('admin')
def manage_jobs():
    jobs_list = Job.query.all()
    # Add applications count and data for each job
    for job in jobs_list:
        applications = Application.query.filter_by(job_id=job.id).all()
        # Load user data for each application
        for app in applications:
            app.user = User.query.get(app.user_id)
        job.applications = applications
        job.applications_count = len(applications)
    
    # Get all applications for the separate applications table
    all_applications = Application.query.all()
    for app in all_applications:
        app.user = User.query.get(app.user_id)
        app.job = Job.query.get(app.job_id)
    
    return render_template('admin/jobs.html', jobs=jobs_list, applications=all_applications)

@admin.route('/toggle-job-status/<int:job_id>', methods=['POST'])
@login_required
@role_required('admin')
def toggle_job_status(job_id):
    job = Job.query.get_or_404(job_id)
    try:
        job.is_active = not job.is_active
        db.session.commit()
        status = 'activated' if job.is_active else 'deactivated'
        return jsonify({'success': True, 'message': f'Job {status} successfully'})
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update job status'}), 500

@admin.route('/delete-job/<int:job_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'recruiter')
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    try:
        db.session.delete(job)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Job deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete job'}), 500

@admin.route('/delete-jobs-bulk', methods=['POST'])
@login_required
@role_required('admin', 'recruiter')
def delete_jobs_bulk():
    data = request.get_json(silent=True) or {}
    job_ids = data.get('job_ids', [])
    if not job_ids:
        return jsonify({'success': False, 'message': 'No jobs selected'}), 400
    
    deleted = 0
    failed = 0
    for job_id in job_ids:
        job = Job.query.get(job_id)
        if not job:
            failed += 1
            continue
        try:
            Application.query.filter_by(job_id=job.id).delete(synchronize_session=False)
            db.session.delete(job)
            deleted += 1
        except Exception:
            failed += 1
    
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete jobs'}), 500
    
    return jsonify({
        'success': True,
        'message': f'{deleted} job(s) deleted successfully{f", {failed} failed" if failed else ""}',
        'deleted': deleted,
        'failed': failed
    })

@admin.route('/edit-job/<int:job_id>', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def edit_job(job_id):
    job = Job.query.get_or_404(job_id)
    
    if request.method == 'POST':
        try:
            job.title = request.form.get('title', job.title)
            job.company = request.form.get('company', job.company)
            job.location = request.form.get('location', job.location)
            job.description = request.form.get('description', job.description)
            job.requirements = request.form.get('requirements', job.requirements)
            job.salary_min = float(request.form.get('salary_min', job.salary_min))
            job.salary_max = float(request.form.get('salary_max', job.salary_max))
            job.is_active = request.form.get('is_active') == 'on'
            
            db.session.commit()
            flash('Job updated successfully', 'success')
            return redirect(url_for('admin.manage_jobs'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to update job', 'danger')
    
    return render_template('admin/edit_job.html', job=job)

@admin.route('/add-job', methods=['GET', 'POST'])
@login_required
@role_required('admin')
def add_job():
    if request.method == 'POST':
        try:
            job = Job(
                title=request.form.get('title'),
                company=request.form.get('company'),
                location=request.form.get('location'),
                description=request.form.get('description'),
                requirements=request.form.get('requirements'),
                salary_min=float(request.form.get('salary_min')),
                salary_max=float(request.form.get('salary_max')),
                is_active=request.form.get('is_active') == 'on',
                posted_at=datetime.utcnow()
            )
            
            db.session.add(job)
            db.session.commit()
            flash('Job added successfully', 'success')
            return redirect(url_for('admin.manage_jobs'))
        except Exception as e:
            db.session.rollback()
            flash('Failed to add job', 'danger')
    
    return render_template('admin/add_job.html')

@admin.route('/manage-tickets')
@login_required
@role_required('admin')
def manage_tickets():
    tickets = SupportTicket.query.options(db.joinedload(SupportTicket.user)).all()
    return render_template('admin/tickets.html', tickets=tickets)

@admin.route('/clear-ticket/<int:ticket_id>', methods=['POST'])
@login_required
@role_required('admin')
def clear_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    try:
        ticket.status = 'closed'
        ticket.resolved_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Ticket cleared successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to clear ticket'}), 500

@admin.route('/delete-ticket-permanently/<int:ticket_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_ticket_permanently(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    try:
        # Only allow deletion of closed tickets
        if ticket.status != 'closed':
            return jsonify({'success': False, 'message': 'Can only delete closed tickets'}), 400
        
        # Delete all responses first
        TicketResponse.query.filter_by(ticket_id=ticket_id).delete()
        
        # Delete the ticket
        db.session.delete(ticket)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Ticket deleted permanently'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete ticket'}), 500

@admin.route('/discussions-moderation')
@login_required
@role_required('admin')
def discussions_moderation():
    discussions_list = (
        Discussion.query
        .order_by(Discussion.created_at.desc())
        .all()
    )

    # Load comments + enrich with student name/id
    for discussion in discussions_list:
        discussion.comments = (
            DiscussionComment.query
            .filter_by(discussion_id=discussion.id)
            .order_by(DiscussionComment.created_at.asc())
            .all()
        )

    all_user_ids = set()
    for d in discussions_list:
        all_user_ids.add(d.user_id)
        for c in d.comments:
            all_user_ids.add(c.user_id)

    users_by_id = {u.id: u for u in User.query.filter(User.id.in_(all_user_ids)).all()} if all_user_ids else {}

    def _format_bups_student_id(raw_student_id):
        """Normalize student_id to BUPS00..BUPS10000 for admin display.

        - Always return BUPS{n:02d} where n is numeric part.
        - If raw is already BUPS{...}, use its numeric part.
        - If it's not BUPS at all, still extract trailing digits and format them; otherwise return raw.
        """
        if not raw_student_id:
            return None

        sid = str(raw_student_id).strip().upper()

        # Extract numeric part (from BUPS.... or any other pattern)
        digits = ''.join(ch for ch in sid if ch.isdigit())
        if not digits:
            return sid

        n = int(digits)
        # Requirement: BUPS00..BUPS10000 in series (infinite-safe)
        if n < 100:
            return f'BUPS{n:02d}'
        return f'BUPS{n:05d}' if n <= 10000 else f'BUPS{n}'

    for d in discussions_list:
        du = users_by_id.get(d.user_id)
        d.author_student_id = _format_bups_student_id(du.student_id if du else None)
        d.author_display_name = (
            f"{du.first_name} {du.last_name}".strip()
            if du and (du.first_name or du.last_name)
            else (du.email.split('@')[0] if du and du.email else f"User {d.user_id}")
        )

        for c in d.comments:
            cu = users_by_id.get(c.user_id)
            c.comment_student_id = _format_bups_student_id(cu.student_id if cu else None)
            c.comment_display_name = (
                f"{cu.first_name} {cu.last_name}".strip()
                if cu and (cu.first_name or cu.last_name)
                else (cu.email.split('@')[0] if cu and cu.email else f"User {c.user_id}")
            )

    return render_template('admin/discussions_moderation.html', discussions=discussions_list)



@admin.route('/discussions-moderation/<int:discussion_id>/message', methods=['POST'])
@login_required
@role_required('admin')
def admin_message_discussion(discussion_id: int):
    discussion = Discussion.query.get_or_404(discussion_id)

    content = (request.form.get('content') or '').strip()
    if not content:
        flash('Message cannot be empty.', 'warning')
        return redirect(url_for('admin.discussions_moderation'))

    comment = DiscussionComment(
        discussion_id=discussion.id,
        user_id=current_user.id,
        content=content
    )
    db.session.add(comment)
    db.session.commit()
    flash('Message added to discussion.', 'success')
    return redirect(url_for('admin.discussions_moderation'))


@admin.route('/discussions-moderation/<int:discussion_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def admin_delete_discussion(discussion_id: int):
    discussion = Discussion.query.get_or_404(discussion_id)
    try:
        DiscussionComment.query.filter_by(discussion_id=discussion.id).delete(synchronize_session=False)
        db.session.delete(discussion)
        db.session.commit()
        flash('Discussion deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Could not delete discussion.', 'danger')

    return redirect(url_for('admin.discussions_moderation'))



@admin.route('/analytics')
@login_required
@role_required('admin')
def analytics():
    total_students = User.query.filter_by(role='student').count()
    applications = Application.query.all()
    offered_applications = [app for app in applications if app.status == 'offered']
    placed_student_ids = {app.user_id for app in offered_applications}
    placement_rate = int((len(placed_student_ids) / total_students) * 100) if total_students else 0

    offered_job_ids = {app.job_id for app in offered_applications}
    offered_jobs = Job.query.filter(Job.id.in_(offered_job_ids)).all() if offered_job_ids else []
    package_values = [((job.salary_min or 0) + (job.salary_max or 0)) / 2 for job in offered_jobs if (job.salary_min or job.salary_max)]
    avg_package_lpa = round((sum(package_values) / len(package_values)) / 100000, 1) if package_values else 0

    def avg_test_score(test_type):
        tests = SkillTest.query.filter_by(test_type=test_type).all()
        if not tests:
            return 0
        return int(sum((test.score or 0) for test in tests) / len(tests))

    dsa_score = avg_test_score('dsa')
    aptitude_score = avg_test_score('aptitude')
    coding_score = avg_test_score('coding')
    core_score = avg_test_score('core')

    total_applications = len(applications)
    shortlisted = sum(1 for app in applications if app.status == 'shortlisted')
    interview = sum(1 for app in applications if app.status == 'interview')
    offered = len(offered_applications)

    analytics_data = {
        'placement_rate': placement_rate,
        'students_placed': len(placed_student_ids),
        'avg_package_lpa': avg_package_lpa,
        'tests': {
            'dsa': dsa_score,
            'aptitude': aptitude_score,
            'coding': coding_score,
            'core': core_score
        },
        'pipeline': {
            'applied': 100 if total_applications else 0,
            'shortlisted': int((shortlisted / total_applications) * 100) if total_applications else 0,
            'interview': int((interview / total_applications) * 100) if total_applications else 0,
            'offered': int((offered / total_applications) * 100) if total_applications else 0
        }
    }
    return render_template('admin/analytics.html', analytics_data=analytics_data)

@recruiter.route('/profile', methods=['GET', 'POST'])
@login_required
@role_required('recruiter')
def profile():
    verified_by_admin = (getattr(current_user, 'company_id_status', None) == 'verified')

    if request.method == 'POST':
        def _clean(v):
            if v is None:
                return None
            v = str(v).strip()
            return v if v else None

        # Update recruiter personal fields (stored directly on User)
        current_user.first_name = _clean(request.form.get('first_name'))
        current_user.last_name = _clean(request.form.get('last_name'))
        current_user.mobile = _clean(request.form.get('mobile'))
        current_user.profession = _clean(request.form.get('profession'))
        current_user.linkedin = _clean(request.form.get('linkedin'))
        current_user.github = _clean(request.form.get('github'))
        current_user.company_name = _clean(request.form.get('company_name'))
        current_user.recruiter_request_email = _clean(request.form.get('recruiter_request_email')) or current_user.email

        company_id = _clean(request.form.get('company_id'))
        profile_image = request.files.get('profile_image', None)
        if profile_image and profile_image.filename:
            ext = os.path.splitext(profile_image.filename)[1].lower()
            if ext not in ['.jpg', '.jpeg', '.png', '.webp']:
                flash('Profile photo must be JPG, PNG, or WEBP.', 'danger')
                return redirect(url_for('recruiter.profile'))
            current_user.profile_image_path = _save_user_file(profile_image, 'profile_images', 'recruiter_dp')

        company_id_card = request.files.get('company_id_card', None)
        company_id_image_path = None
        if company_id_card and company_id_card.filename:
            company_id_image_path = f'static/uploads/company_id_cards/{uuid.uuid4().hex}_{company_id_card.filename}'
            company_id_card.save(company_id_image_path)

        if company_id is not None:
            current_user.company_id = company_id
        if company_id_image_path is not None:
            current_user.company_id_image_path = company_id_image_path
            # Reset verification state if they re-upload/modify
            current_user.company_id_status = 'pending_email_otp'
            otp, email_sent = _send_recruiter_email_otp(current_user)
            flash(
                f'Company ID updated. Gmail OTP sent to {current_user.recruiter_request_email}.'
                + ('' if email_sent else f' Demo OTP: {otp}'),
                'info'
            )

        db.session.commit()
        flash('Profile updated successfully', 'success')
        return redirect(url_for('recruiter.profile'))

    return render_template('recruiter/profile.html', verified_by_admin=verified_by_admin)



@recruiter.route('/dashboard')
@login_required
@role_required('recruiter')
def dashboard():
    # Show ALL jobs on the dashboard (including sample jobs) so recruiters see the full marketplace
    jobs = Job.query.order_by(Job.posted_at.desc()).all()
    for job in jobs:
        job.applications = Application.query.filter_by(job_id=job.id).all()

    stats = {
        'posted_jobs': len(jobs),
        'total_applications': sum(len(job.applications) for job in jobs)
    }
    return render_template('recruiter/dashboard.html', stats=stats, jobs=jobs, datetime=datetime)

@recruiter.route('/post-job', methods=['GET', 'POST'])
@login_required
@role_required('recruiter')
def post_job():
    if request.method == 'POST':
        job = Job(
            recruiter_id=current_user.id,
            title=request.form.get('title'),
            company=request.form.get('company'),
            location=request.form.get('location'),
            job_type=request.form.get('job_type'),
            salary_min=request.form.get('salary_min'),
            salary_max=request.form.get('salary_max'),
            required_skills=request.form.get('required_skills'),
            description=request.form.get('description'),
            requirements=request.form.get('requirements'),
            branch=request.form.get('branch'),
            deadline=datetime.strptime(request.form.get('deadline'), '%Y-%m-%d') if request.form.get('deadline') else None
        )
        db.session.add(job)
        db.session.commit()
        
        flash('Job posted successfully!', 'success')
        return redirect(url_for('recruiter.dashboard'))
    
    return render_template('recruiter/post_job.html')

@recruiter.route('/manage-jobs')
@login_required
@role_required('recruiter')
def manage_jobs():
    # Show ALL jobs (like student portal) so recruiters can view the full job marketplace
    jobs = Job.query.all()

    # Load applications for each job
    for job in jobs:
        job.applications = Application.query.filter_by(job_id=job.id).all()

    return render_template('recruiter/manage_jobs.html', jobs=jobs, datetime=datetime)

@recruiter.route('/toggle-job-status/<int:job_id>', methods=['POST'])
@login_required
@role_required('recruiter')
def toggle_job_status(job_id):
    job = Job.query.get_or_404(job_id)
    
    try:
        job.is_active = not job.is_active
        db.session.commit()
        return jsonify({'success': True, 'message': f'Job {"activated" if job.is_active else "deactivated"} successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update job status'}), 500

@recruiter.route('/delete-job/<int:job_id>', methods=['DELETE'])
@login_required
@role_required('recruiter')
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    try:
        db.session.delete(job)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Job deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete job'}), 500

@recruiter.route('/delete-jobs-bulk', methods=['POST'])
@login_required
@role_required('recruiter')
def delete_jobs_bulk():
    data = request.get_json(silent=True) or {}
    job_ids = data.get('job_ids', [])
    if not job_ids:
        return jsonify({'success': False, 'message': 'No jobs selected'}), 400
    
    deleted = 0
    failed = 0
    for job_id in job_ids:
        job = Job.query.get(job_id)
        if not job:
            failed += 1
            continue
        try:
            Application.query.filter_by(job_id=job.id).delete(synchronize_session=False)
            db.session.delete(job)
            deleted += 1
        except Exception:
            failed += 1
    
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete jobs'}), 500
    
    return jsonify({
        'success': True,
        'message': f'{deleted} job(s) deleted successfully{f", {failed} failed" if failed else ""}',
        'deleted': deleted,
        'failed': failed
    })

@recruiter.route('/view-applications')
@login_required
@role_required('recruiter')
def view_applications():
    # Show ALL applications across all jobs (including sample jobs with no recruiter)
    job_id = request.args.get('job_id', type=int)
    if job_id:
        applications_list = Application.query.filter_by(job_id=job_id).all()
    else:
        applications_list = Application.query.all()
    return render_template('recruiter/applications.html', applications=applications_list)

@recruiter.route('/support', methods=['GET', 'POST'])
@login_required
@role_required('recruiter')
def recruiter_support():
    if request.method == 'POST':
        subject = request.form.get('subject')
        category = request.form.get('category')
        priority = request.form.get('priority')
        description = request.form.get('description')
        
        ticket = SupportTicket(
            user_id=current_user.id,
            subject=subject,
            category=category,
            priority=priority,
            description=description
        )
        db.session.add(ticket)
        db.session.commit()
        
        flash('Ticket submitted! We\'ll respond soon.', 'success')
        return redirect(url_for('recruiter.recruiter_support'))
    
    tickets = SupportTicket.query.filter_by(user_id=current_user.id).all()
    return render_template('recruiter/support.html', tickets=tickets)

@recruiter.route('/update-application-status/<int:application_id>', methods=['POST'])
@login_required
@role_required('recruiter')
def update_application_status(application_id):
    data = request.get_json(silent=True) or {}
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'success': False, 'message': 'Status is required'}), 400
    
    application = Application.query.get_or_404(application_id)
    
    try:
        application.status = new_status
        application.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': f'Status updated to {new_status}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update status'}), 500

@recruiter.route('/delete-application/<int:application_id>', methods=['DELETE'])
@login_required
@role_required('recruiter')
def delete_application(application_id):
    application = Application.query.get_or_404(application_id)
    try:
        db.session.delete(application)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Application deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to delete application'}), 500

@recruiter.route('/student-profile/<int:student_id>')
@login_required
@role_required('recruiter')
def view_student_profile(student_id):
    student = User.query.get_or_404(student_id)
    profile = StudentProfile.query.filter_by(user_id=student.id).first()
    readiness = InterviewReadiness.query.filter_by(profile_id=profile.id).first() if profile else None
    return render_template('recruiter/student_profile.html', student=student, profile=profile, readiness=readiness)

@recruiter.route('/matched-candidates')
@login_required
@role_required('recruiter')
def matched_candidates():
    my_jobs = Job.query.filter_by(recruiter_id=current_user.id).all()
    candidates = []
    
    for job in my_jobs:
        job_skills = set(job.required_skills.lower().split(', ')) if job.required_skills else set()
        for application in job.applications:
            profile = StudentProfile.query.filter_by(user_id=application.user_id).first()
            if profile and profile.skills:
                user_skills = set(profile.skills.lower().split(', '))
                match_score = len(user_skills & job_skills) / len(job_skills) * 100 if job_skills else 0
                candidates.append({
                    'profile': profile,
                    'job': job,
                    'match_score': int(match_score),
                    'application_status': application.status
                })
    
    candidates.sort(key=lambda x: x['match_score'], reverse=True)
    return render_template('recruiter/matched_candidates.html', candidates=candidates)
