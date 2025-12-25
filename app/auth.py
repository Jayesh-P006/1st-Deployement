from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from functools import wraps
from . import db
from .models import User
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in to access this page.', 'error')
                return redirect(url_for('auth.login'))
            user = User.query.get(session['user_id'])
            if not user or user.role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('collab.drafts'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('collab.drafts'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account is pending approval by the Admin. You will be able to access the portal once approved.', 'error')
                return redirect(url_for('auth.login'))

            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name

            user.last_login = datetime.utcnow()
            db.session.commit()

            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            return redirect(url_for('collab.drafts'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile')
@login_required
def profile():
    user = get_current_user()
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        full_name = request.form.get('full_name', '').strip()
        vertical = request.form.get('vertical', '').strip()
        position = request.form.get('position', '').strip()

        # Validate passwords match
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return redirect(url_for('auth.register'))

        if not username or not email or not password:
            flash('Please fill in all required fields.', 'error')
            return redirect(url_for('auth.register'))

        if not vertical or not position:
            flash('Please select your vertical and position.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.register'))

        if User.query.filter_by(email=email).first():
            flash('Email already exists.', 'error')
            return redirect(url_for('auth.register'))

        # First user is admin and active
        if User.query.count() == 0:
            role = 'admin'
            is_active = True
        else:
            # For compatibility, set a default role based on position
            role = 'approver' if position in ['Lead', 'Co-Lead'] else 'creative'
            is_active = False

        user = User(
            username=username, 
            email=email, 
            full_name=full_name, 
            role=role, 
            vertical=vertical, 
            position=position, 
            is_active=is_active
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        if User.query.count() == 1:
            # Auto-login first user
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['full_name'] = user.full_name
            flash(f'Account created successfully for {username}!', 'success')
            return redirect(url_for('collab.drafts'))

        flash("You will be able to access the portal when your request is approved by the Admin.", 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

def get_current_user():
    if 'user_id' in session:
        return User.query.get(session['user_id'])
    return None
