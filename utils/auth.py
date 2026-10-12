import jwt
import datetime
import hashlib
import re
from flask import session, request, redirect, url_for, flash
from functools import wraps
import os
from dotenv import load_dotenv
import sys

# Try to load .env with error handling
try:
    # Check if .env exists
    if os.path.exists('.env'):
        # Try reading with different encodings
        try:
            load_dotenv()
        except UnicodeDecodeError:
            # If UTF-8 fails, try reading as latin-1 or cp1252
            with open('.env', 'r', encoding='latin-1') as f:
                content = f.read()
            # Write back as UTF-8 without BOM
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(content)
            load_dotenv()
except Exception as e:
    print(f"Warning: Could not load .env file: {e}")
    print("Using default values...")

SECRET_KEY = os.getenv('SECRET_KEY', 'medicoapp_super_secret_key_2024')
JWT_SECRET = os.getenv('JWT_SECRET_KEY', 'medicoapp_jwt_secret_key_2024')

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    """Verify password against hash"""
    return hash_password(password) == hashed

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    return True, "Password is valid"

def generate_jwt_token(user_id, email, role):
    """Generate JWT token with expiry"""
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def decode_jwt_token(token):
    """Decode JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def login_required(f):
    """Decorator for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get('jwt_token')
        if not token:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login'))
        
        payload = decode_jwt_token(token)
        if not payload:
            session.clear()
            flash('Session expired. Please login again.', 'warning')
            return redirect(url_for('login'))
        
        # Update session with user info
        session['user_id'] = payload.get('user_id')
        session['user_email'] = payload.get('email')
        session['user_role'] = payload.get('role')
        
        # Refresh token if more than 4 minutes have passed
        exp_time = datetime.datetime.fromtimestamp(payload.get('exp'))
        if datetime.datetime.utcnow() > exp_time - datetime.timedelta(minutes=1):
            new_token = generate_jwt_token(
                payload.get('user_id'),
                payload.get('email'),
                payload.get('role')
            )
            session['jwt_token'] = new_token
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator for admin-only routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function