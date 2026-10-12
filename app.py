import sqlite3
import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import os
import time

# ========== ENVIRONMENT VARIABLES HANDLING ==========jxvf dzyh ouhn tuib
def load_env_file():
    """Manually load .env file with proper encoding"""
    env_vars = {}
    env_file = '.env'
    
    if os.path.exists(env_file):
        try:
            # Try UTF-8 first
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                # Try latin-1
                with open(env_file, 'r', encoding='latin-1') as f:
                    content = f.read()
            except:
                # Try cp1252 (Windows)
                with open(env_file, 'r', encoding='cp1252') as f:
                    content = f.read()
        
        # Parse lines
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
                    env_vars[key.strip()] = value.strip()
    
    return env_vars

# Load environment variables
env_vars = load_env_file()

# Get config values
SECRET_KEY = os.getenv('SECRET_KEY') or env_vars.get('SECRET_KEY') or 'medicoapp_super_secret_key_2024'
EMAIL_USER = os.getenv('EMAIL_USER') or env_vars.get('EMAIL_USER') or 'your_email@gmail.com'
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD') or env_vars.get('EMAIL_PASSWORD') or ''
JWT_SECRET = os.getenv('JWT_SECRET_KEY') or env_vars.get('JWT_SECRET_KEY') or 'medicoapp_jwt_secret_key_2024'

# ========== AUTH FUNCTIONS ==========
import jwt
import hashlib
import re
from functools import wraps

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
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
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')

def decode_jwt_token(token):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except:
        return None

def login_required(f):
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
        
        session['user_id'] = payload.get('user_id')
        session['user_email'] = payload.get('email')
        session['user_role'] = payload.get('role')
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user_role') != 'admin':
            flash('Admin access required', 'danger')
            return redirect(url_for('user_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ========== EMAIL FUNCTIONS ==========
import smtplib
import random
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def send_otp_email(recipient_email, otp):
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            print("Email credentials not configured. OTP would be:", otp)
            return True
        
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = recipient_email
        msg['Subject'] = 'SmileCare Clinic - Password Reset OTP'
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f8fafc;">
            <div style="background: linear-gradient(135deg, #07628f 0%, #5e06c2 90%); padding: 30px; border-radius: 16px; color: white; text-align: center;">
                <h2 style="margin: 0;">SmileCare Clinic</h2>
                <p style="margin: 5px 0 0;">Password Reset Verification</p>
            </div>
            <div style="background: white; padding: 30px; border-radius: 0 0 16px 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <h3 style="color: #1e293b;">Hello,</h3>
                <p style="color: #475569; line-height: 1.6;">
                    You requested to reset your password. Use the following OTP to complete the process:
                </p>
                <div style="background: #f1f5f9; padding: 20px; border-radius: 12px; text-align: center; margin: 20px 0;">
                    <h1 style="font-size: 42px; letter-spacing: 10px; color: #07628f; font-weight: bold; margin: 0;">
                        {otp}
                    </h1>
                </div>
                <p style="color: #475569; font-size: 14px;">
                    This OTP is valid for <strong>10 minutes</strong>.
                </p>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"Email error: {str(e)}")
        return False

# ========== FLASK APP ==========
app = Flask(__name__)
app.secret_key = SECRET_KEY
db_name = "database.db"

# ========== DATABASE FUNCTIONS ==========
def get_connect():
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connect()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            full_name TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Doctors table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors(
            did INTEGER PRIMARY KEY AUTOINCREMENT,
            dname TEXT NOT NULL,
            contact INTEGER NOT NULL UNIQUE,
            wardno INTEGER NOT NULL DEFAULT 0,
            specialization TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # OP Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS op(
            pid INTEGER PRIMARY KEY AUTOINCREMENT,
            pname TEXT NOT NULL,
            age INTEGER NOT NULL,
            email TEXT NOT NULL,
            aadhaar TEXT NOT NULL,
            disease TEXT NOT NULL,
            since TEXT NOT NULL,
            symptoms TEXT,
            did INTEGER NOT NULL,
            SlDate TEXT NOT NULL,
            SlTime TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            user_id INTEGER,
            FOREIGN KEY (did) REFERENCES doctors (did) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
        )
    ''')
    
    # Health Metrics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS health_metrics(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            height REAL,
            weight REAL,
            blood_pressure_systolic INTEGER,
            blood_pressure_diastolic INTEGER,
            blood_sugar REAL,
            thyroid_tsh REAL,
            thyroid_t3 REAL,
            thyroid_t4 REAL,
            other_metrics TEXT,
            recorded_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    
    # Staff table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            phone TEXT NOT NULL,
            department TEXT,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # Collaborations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collaborations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_name TEXT NOT NULL,
            org_type TEXT NOT NULL,
            contact_person TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            partnership_type TEXT,
            description TEXT,
            joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    # OTP table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS otp_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_used INTEGER DEFAULT 0
        )
    ''')
    
    # Seed Admin User
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
    if cursor.fetchone()[0] == 0:
        admin_password = hash_password('Admin@123')
        cursor.execute('''
            INSERT INTO users (username, email, password, role, full_name, phone)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin@smilecare.com', admin_password, 'admin', 'System Administrator', '9876543210'))
    
    # Seed Doctors
    cursor.execute('SELECT COUNT(*) FROM doctors')
    if cursor.fetchone()[0] == 0:
        initial_doctors = [
            ('Dr. Sarah Jenkins', 9876543210, 101, 'General Surgery'),
            ('Dr. Rajesh Kumar', 9876543211, 204, 'Critical Care & Accident'),
            ('Dr. Emily Chen', 9876543212, 302, 'Neurology'),
            ('Dr. Michael Brown', 9876543213, 105, 'ENT Specialist'),
            ('Dr. Priya Nair', 9876543214, 401, 'Pediatric Care')
        ]
        cursor.executemany('''
            INSERT INTO doctors (dname, contact, wardno, specialization)
            VALUES (?, ?, ?, ?)
        ''', initial_doctors)
    
    conn.commit()
    conn.close()

# ========== AUTH ROUTES ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_connect()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and verify_password(password, user['password']):
            if not user['is_active']:
                flash('Account is deactivated. Contact admin.', 'danger')
                return render_template('login.html')
            
            token = generate_jwt_token(user['id'], user['email'], user['role'])
            session['jwt_token'] = token
            session['user_id'] = user['id']
            session['user_email'] = user['email']
            session['user_role'] = user['role']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['login_time'] = time.time()
            
            flash(f'Welcome back, {user["full_name"] or user["username"]}!', 'success')
            
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
        
        flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        
        if not validate_email(email):
            flash('Invalid email format', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        is_valid, msg = validate_password(password)
        if not is_valid:
            flash(msg, 'danger')
            return render_template('register.html')
        
        try:
            conn = get_connect()
            cursor = conn.cursor()
            hashed = hash_password(password)
            cursor.execute('''
                INSERT INTO users (username, email, password, full_name, phone, role)
                VALUES (?, ?, ?, ?, ?, 'user')
            ''', (username, email, hashed, full_name, phone))
            conn.commit()
            conn.close()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists', 'danger')
    
    return render_template('register.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        
        conn = get_connect()
        cursor = conn.cursor()
        user = cursor.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user:
            otp = generate_otp()
            cursor.execute('''
                INSERT INTO otp_requests (email, otp)
                VALUES (?, ?)
            ''', (email, otp))
            conn.commit()
            
            if send_otp_email(email, otp):
                flash('OTP sent to your email.', 'success')
                return redirect(url_for('reset_password', email=email))
            else:
                flash('Failed to send OTP. Please try again.', 'danger')
        else:
            flash('Email not found in our system.', 'danger')
        
        conn.close()
    
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    email = request.args.get('email')
    
    if not email:
        flash('Invalid request', 'danger')
        return redirect(url_for('forgot_password'))
    
    if request.method == 'POST':
        otp = request.form.get('otp')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        conn = get_connect()
        cursor = conn.cursor()
        record = cursor.execute('''
            SELECT * FROM otp_requests 
            WHERE email = ? AND otp = ? AND is_used = 0 
            ORDER BY created_at DESC LIMIT 1
        ''', (email, otp)).fetchone()
        
        if not record:
            flash('Invalid OTP', 'danger')
            conn.close()
            return render_template('reset_password.html', email=email)
        
        created_at = datetime.datetime.strptime(record['created_at'], '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.now() - created_at > datetime.timedelta(minutes=10):
            flash('OTP has expired.', 'danger')
            conn.close()
            return render_template('reset_password.html', email=email)
        
        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            conn.close()
            return render_template('reset_password.html', email=email)
        
        is_valid, msg = validate_password(new_password)
        if not is_valid:
            flash(msg, 'danger')
            conn.close()
            return render_template('reset_password.html', email=email)
        
        hashed = hash_password(new_password)
        cursor.execute('UPDATE users SET password = ? WHERE email = ?', (hashed, email))
        cursor.execute('UPDATE otp_requests SET is_used = 1 WHERE id = ?', (record['id'],))
        conn.commit()
        conn.close()
        
        flash('Password reset successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', email=email)

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully', 'info')
    return redirect(url_for('login'))

# ========== PROTECTED ROUTES ==========
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/dashboard')
@login_required
def dashboard():
    if session.get('user_role') == 'admin':
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('user_dashboard'))

@app.route('/admin_dashboard')
@login_required
@admin_required
def admin_dashboard():
    conn = get_connect()
    cursor = conn.cursor()
    
    total_users = cursor.execute('SELECT COUNT(*) FROM users WHERE role = "user"').fetchone()[0]
    total_bookings = cursor.execute('SELECT COUNT(*) FROM op').fetchone()[0]
    pending_bookings = cursor.execute('SELECT COUNT(*) FROM op WHERE status = "pending"').fetchone()[0]
    total_doctors = cursor.execute('SELECT COUNT(*) FROM doctors').fetchone()[0]
    total_staff = cursor.execute('SELECT COUNT(*) FROM staff').fetchone()[0]
    
    recent_bookings = cursor.execute('''
        SELECT op.*, doctors.dname 
        FROM op 
        JOIN doctors ON op.did = doctors.did 
        ORDER BY op.pid DESC LIMIT 5
    ''').fetchall()
    
    recent_users = cursor.execute('''
        SELECT * FROM users WHERE role = "user" 
        ORDER BY created_at DESC LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html',
        total_users=total_users,
        total_bookings=total_bookings,
        pending_bookings=pending_bookings,
        total_doctors=total_doctors,
        total_staff=total_staff,
        recent_bookings=recent_bookings,
        recent_users=recent_users
    )

@app.route('/user_dashboard')
@login_required
def user_dashboard():
    user_id = session.get('user_id')
    conn = get_connect()
    cursor = conn.cursor()
    
    bookings = cursor.execute('''
        SELECT op.*, doctors.dname, doctors.specialization 
        FROM op 
        JOIN doctors ON op.did = doctors.did 
        WHERE op.user_id = ? 
        ORDER BY op.pid DESC
    ''', (user_id,)).fetchall()
    
    metrics = cursor.execute('''
        SELECT * FROM health_metrics 
        WHERE user_id = ? 
        ORDER BY recorded_date DESC LIMIT 1
    ''', (user_id,)).fetchone()
    
    conn.close()
    
    return render_template('user_dashboard.html', bookings=bookings, metrics=metrics)

@app.route('/op_booking')
@login_required
def op_booking():
    conn = get_connect()
    cursor = conn.cursor()
    doctors = cursor.execute('SELECT did, dname, specialization FROM doctors WHERE is_active = 1').fetchall()
    bookings = cursor.execute('''
        SELECT op.*, doctors.dname, doctors.specialization 
        FROM op 
        JOIN doctors ON op.did = doctors.did 
        ORDER BY op.pid DESC
    ''').fetchall()
    conn.close()
    return render_template('op_booking.html', doctors=doctors, bookings=bookings)

@app.route('/book_op', methods=['POST'])
@login_required
def book_op():
    pid = request.form.get('bookingId')
    pname = request.form.get('patientName')
    age = request.form.get('age')
    email = request.form.get('email')
    aadhaar = request.form.get('aadhar')
    disease = request.form.get('disease')
    since = request.form.get('sufferedSince')
    symptoms = request.form.get('symptoms')
    did = request.form.get('did')
    sl_date = request.form.get('bookingDate')
    sl_time = request.form.get('bookingTime')
    user_id = session.get('user_id')
    
    try:
        conn = get_connect()
        cursor = conn.cursor()
        
        if pid:
            cursor.execute('''
                UPDATE op 
                SET pname=?, age=?, email=?, aadhaar=?, disease=?, since=?, symptoms=?, did=?, SlDate=?, SlTime=?
                WHERE pid=? AND user_id=?
            ''', (pname, age, email, aadhaar, disease, since, symptoms, did, sl_date, sl_time, pid, user_id))
            flash('OP Booking updated successfully!', 'success')
        else:
            cursor.execute('''
                INSERT INTO op (pname, age, email, aadhaar, disease, since, symptoms, did, SlDate, SlTime, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (pname, age, email, aadhaar, disease, since, symptoms, did, sl_date, sl_time, user_id))
            flash('New OP Registration created successfully!', 'success')
        
        conn.commit()
        conn.close()
    except sqlite3.Error as err:
        flash(f'Database operation failed: {str(err)}', 'danger')
    
    return redirect(url_for('op_booking'))

@app.route('/delete_op/<int:pid>', methods=['POST'])
@login_required
def delete_op(pid):
    try:
        conn = get_connect()
        cursor = conn.cursor()
        if session.get('user_role') == 'admin':
            cursor.execute('DELETE FROM op WHERE pid = ?', (pid,))
        else:
            cursor.execute('DELETE FROM op WHERE pid = ? AND user_id = ?', (pid, session.get('user_id')))
        conn.commit()
        conn.close()
        flash('OP Booking deleted successfully.', 'warning')
    except sqlite3.Error as err:
        flash(f'Failed to delete record: {str(err)}', 'danger')
    
    return redirect(url_for('op_booking'))

@app.route('/update_op_status/<int:pid>', methods=['POST'])
@login_required
@admin_required
def update_op_status(pid):
    status = request.form.get('status')
    try:
        conn = get_connect()
        cursor = conn.cursor()
        cursor.execute('UPDATE op SET status = ? WHERE pid = ?', (status, pid))
        conn.commit()
        conn.close()
        flash(f'Booking status updated to {status}', 'success')
    except sqlite3.Error as err:
        flash(f'Failed to update status: {str(err)}', 'danger')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/health_metrics', methods=['GET', 'POST'])
@login_required
@admin_required
def health_metrics():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        height = request.form.get('height')
        weight = request.form.get('weight')
        bp_systolic = request.form.get('bp_systolic')
        bp_diastolic = request.form.get('bp_diastolic')
        blood_sugar = request.form.get('blood_sugar')
        thyroid_tsh = request.form.get('thyroid_tsh')
        thyroid_t3 = request.form.get('thyroid_t3')
        thyroid_t4 = request.form.get('thyroid_t4')
        other_metrics = request.form.get('other_metrics')
        
        try:
            conn = get_connect()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO health_metrics 
                (user_id, height, weight, blood_pressure_systolic, blood_pressure_diastolic, 
                 blood_sugar, thyroid_tsh, thyroid_t3, thyroid_t4, other_metrics)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, height, weight, bp_systolic, bp_diastolic, blood_sugar, 
                  thyroid_tsh, thyroid_t3, thyroid_t4, other_metrics))
            conn.commit()
            conn.close()
            flash('Health metrics added successfully!', 'success')
        except sqlite3.Error as err:
            flash(f'Failed to add metrics: {str(err)}', 'danger')
        
        return redirect(url_for('health_metrics'))
    
    conn = get_connect()
    cursor = conn.cursor()
    users = cursor.execute('SELECT id, username, full_name, email FROM users WHERE role = "user"').fetchall()
    all_metrics = cursor.execute('''
        SELECT hm.*, u.username, u.full_name 
        FROM health_metrics hm
        JOIN users u ON hm.user_id = u.id
        ORDER BY hm.recorded_date DESC
    ''').fetchall()
    conn.close()
    return render_template('health_metrics.html', users=users, metrics=all_metrics)

@app.route('/staff_management', methods=['GET', 'POST'])
@login_required
@admin_required
def staff_management():
    if request.method == 'POST':
        name = request.form.get('name')
        role = request.form.get('role')
        email = request.form.get('email')
        phone = request.form.get('phone')
        department = request.form.get('department')
        
        try:
            conn = get_connect()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO staff (name, role, email, phone, department)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, role, email, phone, department))
            conn.commit()
            conn.close()
            flash('Staff member added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Email already exists', 'danger')
        except sqlite3.Error as err:
            flash(f'Failed to add staff: {str(err)}', 'danger')
        
        return redirect(url_for('staff_management'))
    
    conn = get_connect()
    cursor = conn.cursor()
    staff_list = cursor.execute('SELECT * FROM staff ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('staff_management.html', staff_list=staff_list)

@app.route('/delete_staff/<int:staff_id>', methods=['POST'])
@login_required
@admin_required
def delete_staff(staff_id):
    try:
        conn = get_connect()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM staff WHERE id = ?', (staff_id,))
        conn.commit()
        conn.close()
        flash('Staff member removed successfully.', 'warning')
    except sqlite3.Error as err:
        flash(f'Failed to delete staff: {str(err)}', 'danger')
    return redirect(url_for('staff_management'))

@app.route('/collaborations')
def collaborations():
    conn = get_connect()
    cursor = conn.cursor()
    collabs = cursor.execute('''
        SELECT * FROM collaborations 
        WHERE is_active = 1 
        ORDER BY joined_date DESC
    ''').fetchall()
    conn.close()
    return render_template('collaborations.html', collaborations=collabs)

@app.route('/add_collaboration', methods=['POST'])
@login_required
@admin_required
def add_collaboration():
    org_name = request.form.get('org_name')
    org_type = request.form.get('org_type')
    contact_person = request.form.get('contact_person')
    email = request.form.get('email')
    phone = request.form.get('phone')
    partnership_type = request.form.get('partnership_type')
    description = request.form.get('description')
    
    try:
        conn = get_connect()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO collaborations (org_name, org_type, contact_person, email, phone, partnership_type, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (org_name, org_type, contact_person, email, phone, partnership_type, description))
        conn.commit()
        conn.close()
        flash('Collaboration added successfully!', 'success')
    except sqlite3.Error as err:
        flash(f'Failed to add collaboration: {str(err)}', 'danger')
    return redirect(url_for('collaborations'))

@app.route('/user_management')
@login_required
@admin_required
def user_management():
    conn = get_connect()
    cursor = conn.cursor()
    users = cursor.execute('''
        SELECT id, username, email, full_name, phone, role, created_at, is_active 
        FROM users 
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('user_management.html', users=users)

@app.route('/toggle_user_status/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    try:
        conn = get_connect()
        cursor = conn.cursor()
        user = cursor.execute('SELECT is_active FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            new_status = 0 if user['is_active'] else 1
            cursor.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
            conn.commit()
            flash(f'User status updated successfully', 'success')
        conn.close()
    except sqlite3.Error as err:
        flash(f'Failed to update user: {str(err)}', 'danger')
    return redirect(url_for('user_management'))

@app.route('/profile')
@login_required
def profile():
    conn = get_connect()
    cursor = conn.cursor()
    user = cursor.execute('SELECT * FROM users WHERE id = ?', (session.get('user_id'),)).fetchone()
    conn.close()
    return render_template('profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    full_name = request.form.get('full_name')
    phone = request.form.get('phone')
    
    try:
        conn = get_connect()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users 
            SET full_name = ?, phone = ? 
            WHERE id = ?
        ''', (full_name, phone, session.get('user_id')))
        conn.commit()
        conn.close()
        session['full_name'] = full_name
        flash('Profile updated successfully!', 'success')
    except sqlite3.Error as err:
        flash(f'Failed to update profile: {str(err)}', 'danger')
    return redirect(url_for('profile'))

@app.route('/op_scheduler')
@login_required
@admin_required
def op_scheduler():
    return render_template('op_scheduler.html', now=datetime.datetime.now())

@app.route('/reports')
@login_required
@admin_required
def reports():
    conn = get_connect()
    cursor = conn.cursor()
    doctors = cursor.execute('SELECT did, dname FROM doctors').fetchall()
    
    stats = {
        'total_bookings': cursor.execute('SELECT COUNT(*) FROM op').fetchone()[0],
        'completed': cursor.execute('SELECT COUNT(*) FROM op WHERE status = "completed"').fetchone()[0],
        'pending': cursor.execute('SELECT COUNT(*) FROM op WHERE status = "pending"').fetchone()[0],
        'total_patients': cursor.execute('SELECT COUNT(DISTINCT email) FROM op').fetchone()[0]
    }
    
    report_data = cursor.execute('''
        SELECT op.*, doctors.dname 
        FROM op 
        JOIN doctors ON op.did = doctors.did 
        ORDER BY op.SlDate DESC LIMIT 100
    ''').fetchall()
    
    conn.close()
    return render_template('reports.html', 
        stats=stats, 
        report_data=report_data, 
        doctors=doctors,
        from_date=datetime.datetime.now().strftime('%Y-%m-%d'),
        to_date=datetime.datetime.now().strftime('%Y-%m-%d')
    )

@app.route('/api/schedule/<date>')
@login_required
@admin_required
def api_schedule(date):
    conn = get_connect()
    cursor = conn.cursor()
    bookings = cursor.execute('''
        SELECT op.*, doctors.dname 
        FROM op 
        JOIN doctors ON op.did = doctors.did 
        WHERE op.SlDate = ?
        ORDER BY op.SlTime
    ''', (date,)).fetchall()
    conn.close()
    return jsonify([dict(b) for b in bookings])

# ========== SESSION TIMER CONTEXT ==========
@app.context_processor
def inject_session_time():
    login_time = session.get('login_time')
    if login_time:
        elapsed = int(time.time() - login_time)
        remaining = max(0, 300 - elapsed)
        minutes = remaining // 60
        seconds = remaining % 60
        time_left = f"{minutes:02d}:{seconds:02d}"
        return {'session_time_left': time_left, 'is_logged_in': 'user_id' in session}
    return {'session_time_left': '00:00', 'is_logged_in': False}

# ========== MAIN ==========
if __name__ == '__main__':
    init_db()
    print("=" * 50)
    print("SmileCare Clinic - MedicoApp")
    print("=" * 50)
    print(f"Server running at: http://localhost:3500")
    print(f"Admin Login: admin@smilecare.com / Admin@123")
    print("=" * 50)
    app.run(debug=True, port=3500)