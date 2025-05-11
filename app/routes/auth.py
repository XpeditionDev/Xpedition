from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, UserSettings
from app import db
import re
import traceback

auth_bp = Blueprint('auth', __name__)

def is_valid_password(password):
    # Check length
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    # Check for uppercase
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    # Check for number
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"
    
    # Check for special character
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Check username length
        if len(username) < 6:
            flash('Username must be at least 6 characters long')
            return render_template('auth/register.html')
        
        # Check if username contains only allowed characters
        if not username.isalnum():
            flash('Username can only contain letters and numbers')
            return render_template('auth/register.html')
        
        # Check if username exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('auth/register.html')
        
        # Check if email is valid
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash('Please enter a valid email address')
            return render_template('auth/register.html')
            
        # Check if email exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('auth/register.html')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match')
            return render_template('auth/register.html')
        
        # Validate password
        is_valid, message = is_valid_password(password)
        if not is_valid:
            flash(message)
            return render_template('auth/register.html')
            
        # Create new user
        try:
            user = User(username=username, email=email)
            user.set_password(password)
            db.session.add(user)
            
            # Create user settings
            settings = UserSettings(user=user)
            db.session.add(settings)
            
            db.session.commit()
            flash('Registration successful! Please login.')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {str(e)}")
            print(traceback.format_exc())
            flash('An error occurred during registration. Please try again.')
            return render_template('auth/register.html')
        
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
            
        flash('Invalid username or password')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))
