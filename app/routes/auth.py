from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy import or_
from app import db
from app.models.user import User
from app.models.shop import Shop
from app.models.audit import AuditLog
from app.forms.auth_forms import LoginForm, RegisterForm
from app.utils.email import send_reset_email
from itsdangerous import URLSafeTimedSerializer
from datetime import datetime, timedelta

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    
    if form.validate_on_submit():
        login_id = form.email.data.strip()
        password = form.password.data
        
        user = User.query.filter(
            or_(User.email == login_id, User.username == login_id)
        ).first()
        
        if user is None:
            flash('No account found with this email or username', 'danger')
        elif not user.check_password(password):
            flash('Incorrect password', 'danger')
        else:
            if not user.is_active:
                user.is_active = True
                db.session.commit()
                flash('Your account was inactive and has been reactivated. Welcome back!', 'success')
            
            login_user(user, remember=form.remember_me.data)
            session.permanent = True
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('billing.pos') if not user.is_admin else url_for('main.dashboard')
            return redirect(next_page)
            
    return render_template('auth/login.html', form=form)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        is_first_user = User.query.first() is None
        
        user = User(
            username=form.username.data.strip(),
            email=form.email.data.strip(),
            shop_name=form.shop_name.data.strip(),
            is_admin=is_first_user,
            is_super_admin=is_first_user,
            shop_id=None
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        if is_first_user:
            flash('Super Admin account created! Please login.', 'success')
        else:
            flash('Account created successfully! Please login.', 'success')
        
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        for field, errors in form.errors.items():
            for error in errors:
                field_name = field.replace('_', ' ').title()
                flash(f'{field_name}: {error}', 'danger')
    
    return render_template('auth/register.html', form=form)

@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    logout_user()
    session.clear()
    resp = redirect(url_for('auth.login'))
    resp.delete_cookie('remember_token')
    return resp

def generate_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')

def verify_reset_token(token, expires_sec=3600):
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=expires_sec)
    except:
        return None
    return email

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        user = User.query.filter_by(email=email).first()
        
        if user:
            token = generate_reset_token(email)
            user.reset_token = token
            user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()
            
            try:
                send_reset_email(user)
                flash('Password reset link has been sent to your email.', 'success')
            except Exception as e:
                flash('Error sending email. Please try again.', 'danger')
        else:
            flash('No account found with that email.', 'danger')
        
        return redirect(url_for('auth.forgot_password'))
    
    return render_template('auth/forgot_password.html')

@bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    email = verify_reset_token(token)
    if not email:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    user = User.query.filter_by(email=email).first()
    if not user or user.reset_token != token:
        flash('Invalid reset link.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if user.reset_token_expiry and user.reset_token_expiry < datetime.utcnow():
        flash('The reset link has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            user.set_password(password)
            user.reset_token = None
            user.reset_token_expiry = None
            db.session.commit()
            flash('Your password has been updated! Please login.', 'success')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', token=token)