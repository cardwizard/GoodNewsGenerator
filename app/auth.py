from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from app.models import db, User

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


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

        if len(password) < 8:
            flash('Password must be at least 8 characters', 'error')
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
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('Login successful!', 'success')
            return redirect(url_for('news.feed'))
        else:
            flash('Invalid username or password', 'error')
            return render_template('login.html')

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))
