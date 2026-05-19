from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, role_required
from models import User, StudentProfile, SkillTest, Application, Job, db
from datetime import datetime, timedelta
import json

club = Blueprint('club', __name__, url_prefix='/club')

@club.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    """Club/Manager dashboard with real-time student details"""
    
    # Get real-time student statistics
    total_students = User.query.filter_by(role='student').count()
    active_students = User.query.filter_by(role='student', active=True).count()
    
    # Students with profiles
    students_with_profiles = db.session.query(
        db.func.count(StudentProfile.id)
    ).join(User, StudentProfile.user_id == User.id).filter(User.role == 'student').scalar() or 0
    
    # Students with skill tests
    students_with_tests = db.session.query(
        db.func.count(db.distinct(SkillTest.user_id))
    ).join(User, SkillTest.user_id == User.id).filter(User.role == 'student').scalar() or 0
    
    # Students with job applications
    students_with_applications = db.session.query(
        db.func.count(db.distinct(Application.user_id))
    ).join(User, Application.user_id == User.id).filter(User.role == 'student').scalar() or 0
    
    # Average skill test scores
    avg_score = db.session.query(
        db.func.avg(SkillTest.score)
    ).join(User, SkillTest.user_id == User.id).filter(User.role == 'student').scalar() or 0
    
    # Recent student activity (last 7 days)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    recent_activity = User.query.filter(
        User.role == 'student',
        User.last_login_at >= seven_days_ago
    ).count()
    
    # Top performing students
    top_students = db.session.query(
        User.email,
        db.func.avg(SkillTest.score).label('avg_score'),
        db.func.count(SkillTest.id).label('test_count')
    ).join(SkillTest, User.id == SkillTest.user_id).filter(
        User.role == 'student'
    ).group_by(User.id, User.email).order_by(
        db.func.avg(SkillTest.score).desc()
    ).limit(10).all()
    
    # Students by skill level
    skill_levels = db.session.query(
        SkillTest.score,
        db.func.count(SkillTest.id).label('count')
    ).join(User, SkillTest.user_id == User.id).filter(
        User.role == 'student'
    ).group_by(
        db.case(
            (SkillTest.score >= 90, 'Expert'),
            (SkillTest.score >= 70, 'Advanced'),
            (SkillTest.score >= 50, 'Intermediate'),
            else_='Beginner'
        )
    ).all()
    
    # Job application statistics
    total_applications = Application.query.join(User).filter(User.role == 'student').count()
    pending_applications = Application.query.join(User).filter(
        User.role == 'student',
        Application.status == 'pending'
    ).count()
    accepted_applications = Application.query.join(User).filter(
        User.role == 'student',
        Application.status == 'accepted'
    ).count()
    
    stats = {
        'total_students': total_students,
        'active_students': active_students,
        'students_with_profiles': students_with_profiles,
        'students_with_tests': students_with_tests,
        'students_with_applications': students_with_applications,
        'avg_score': round(avg_score, 1),
        'recent_activity': recent_activity,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'accepted_applications': accepted_applications,
        'application_success_rate': round((accepted_applications / total_applications) * 100, 1) if total_applications > 0 else 0
    }
    
    return render_template('club/dashboard.html', 
                         stats=stats, 
                         top_students=top_students,
                         skill_levels=skill_levels)

@club.route('/students')
@login_required
@role_required('admin')
def students():
    """Detailed student list with real-time data"""
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    students_query = User.query.filter_by(role='student').order_by(User.created_at.desc())
    students = students_query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Enrich student data with additional information
    enriched_students = []
    for student in students.items:
        profile = StudentProfile.query.filter_by(user_id=student.id).first()
        latest_test = SkillTest.query.filter_by(user_id=student.id).order_by(SkillTest.created_at.desc()).first()
        application_count = Application.query.filter_by(user_id=student.id).count()
        
        enriched_students.append({
            'id': student.id,
            'email': student.email,
            'mobile': student.mobile,
            'created_at': student.created_at,
            'last_login_at': student.last_login_at,
            'is_active': student.active,
            'aadhaar_verified': student.aadhaar_verification_status == 'verified',
            'has_profile': profile is not None,
            'latest_test_score': latest_test.score if latest_test else None,
            'latest_test_date': latest_test.created_at if latest_test else None,
            'application_count': application_count,
            'profile': profile
        })
    
    return render_template('club/students.html', 
                         students=enriched_students,
                         pagination=students)

@club.route('/student/<int:student_id>')
@login_required
@role_required('admin')
def student_detail(student_id):
    """Detailed student information"""
    
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return jsonify({'error': 'Student not found'}), 404
    
    # Get comprehensive student data
    profile = StudentProfile.query.filter_by(user_id=student.id).first()
    skill_tests = SkillTest.query.filter_by(user_id=student.id).order_by(SkillTest.created_at.desc()).all()
    applications = Application.query.filter_by(user_id=student.id).order_by(Application.created_at.desc()).all()
    
    # Calculate statistics
    avg_score = sum(test.score for test in skill_tests) / len(skill_tests) if skill_tests else 0
    total_tests = len(skill_tests)
    passed_tests = sum(1 for test in skill_tests if test.score >= 70)
    
    student_data = {
        'id': student.id,
        'email': student.email,
        'mobile': student.mobile,
        'created_at': student.created_at,
        'last_login_at': student.last_login_at,
        'is_active': student.active,
        'aadhaar_verified': student.aadhaar_verification_status == 'verified',
        'aadhaar_verification_id': student.aadhaar_verification_id,
        'profile': profile,
        'stats': {
            'avg_score': round(avg_score, 1),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'pass_rate': round((passed_tests / total_tests) * 100, 1) if total_tests > 0 else 0,
            'total_applications': len(applications),
            'pending_applications': sum(1 for app in applications if app.status == 'pending'),
            'accepted_applications': sum(1 for app in applications if app.status == 'accepted')
        },
        'skill_tests': skill_tests,
        'applications': applications
    }
    
    return render_template('club/student_detail.html', student=student_data)

@club.route('/api/student-stats')
@login_required
@role_required('admin')
def api_student_stats():
    """API endpoint for real-time student statistics"""
    
    # Real-time statistics
    total_students = User.query.filter_by(role='student').count()
    active_students = User.query.filter_by(role='student', active=True).count()
    
    # Last 24 hours activity
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_logins = User.query.filter(
        User.role == 'student',
        User.last_login_at >= yesterday
    ).count()
    
    # Recent registrations
    recent_registrations = User.query.filter(
        User.role == 'student',
        User.created_at >= yesterday
    ).count()
    
    # Skill test activity
    recent_tests = SkillTest.query.filter(
        SkillTest.created_at >= yesterday
    ).count()
    
    return jsonify({
        'total_students': total_students,
        'active_students': active_students,
        'recent_logins': recent_logins,
        'recent_registrations': recent_registrations,
        'recent_tests': recent_tests,
        'timestamp': datetime.utcnow().isoformat()
    })

@club.route('/api/search-students')
@login_required
@role_required('admin')
def api_search_students():
    """API endpoint for searching students"""
    
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify({'students': []})
    
    students = User.query.filter(
        User.role == 'student',
        db.or_(
            User.email.ilike(f'%{query}%'),
            User.mobile.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = []
    for student in students:
        profile = StudentProfile.query.filter_by(user_id=student.id).first()
        results.append({
            'id': student.id,
            'email': student.email,
            'mobile': student.mobile,
            'name': profile.name if profile else student.email.split('@')[0],
            'is_active': student.active,
            'aadhaar_verified': student.aadhaar_verification_status == 'verified'
        })
    
    return jsonify({'students': results})
