from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from datetime import datetime, timedelta
from app.models import db, User, LoginAttempt
from app.config import Config
from app import limiter
import re

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def is_strong_password(password):
    """Validate password strength"""
    if len(password) < Config.MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, ""


def is_account_locked(username):
    """Check if account is locked due to failed login attempts"""
    cutoff_time = datetime.utcnow() - timedelta(seconds=Config.ACCOUNT_LOCKOUT_DURATION)
    recent_attempts = LoginAttempt.query.filter(
        LoginAttempt.username == username,
        LoginAttempt.attempted_at >= cutoff_time,
        LoginAttempt.successful == False
    ).count()
    return recent_attempts >= Config.MAX_LOGIN_ATTEMPTS


def record_login_attempt(username, successful, ip_address=None):
    """Record a login attempt in the database"""
    attempt = LoginAttempt(
        username=username,
        successful=successful,
        ip_address=ip_address
    )
    db.session.add(attempt)
    db.session.commit()


def cleanup_old_login_attempts():
    """Remove login attempts older than lockout duration"""
    cutoff_time = datetime.utcnow() - timedelta(seconds=Config.ACCOUNT_LOCKOUT_DURATION)
    LoginAttempt.query.filter(LoginAttempt.attempted_at < cutoff_time).delete()
    db.session.commit()


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('register.html')

        if len(username) < 3 or len(username) > 20:
            flash('Username must be between 3 and 20 characters', 'error')
            return render_template('register.html')

        # Validate password strength
        is_valid, error_message = is_strong_password(password)
        if not is_valid:
            flash(error_message, 'error')
            return render_template('register.html')

        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('register.html')

        # Check if username exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists', 'error')
            return render_template('register.html')

        # Create new user
        try:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            # Auto-login
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Registration successful!', 'success')
            return redirect(url_for('news.feed'))

        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration', 'error')
            return render_template('register.html')

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login():
    """User login with rate limiting and account lockout"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        ip_address = request.remote_addr

        # Clean up old login attempts periodically
        cleanup_old_login_attempts()

        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')

        # Check if account is locked
        if is_account_locked(username):
            lockout_minutes = Config.ACCOUNT_LOCKOUT_DURATION // 60
            flash(f'Account temporarily locked due to multiple failed login attempts. Please try again in {lockout_minutes} minutes.', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            # Successful login
            record_login_attempt(username, successful=True, ip_address=ip_address)
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('news.feed'))
        else:
            # Failed login
            record_login_attempt(username, successful=False, ip_address=ip_address)

            # Check how many attempts are left before lockout
            cutoff_time = datetime.utcnow() - timedelta(seconds=Config.ACCOUNT_LOCKOUT_DURATION)
            recent_failed = LoginAttempt.query.filter(
                LoginAttempt.username == username,
                LoginAttempt.attempted_at >= cutoff_time,
                LoginAttempt.successful == False
            ).count()

            attempts_left = Config.MAX_LOGIN_ATTEMPTS - recent_failed
            if attempts_left > 0:
                flash(f'Invalid username or password. {attempts_left} attempt(s) remaining.', 'error')
            else:
                lockout_minutes = Config.ACCOUNT_LOCKOUT_DURATION // 60
                flash(f'Account locked due to multiple failed attempts. Try again in {lockout_minutes} minutes.', 'error')

            return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))
