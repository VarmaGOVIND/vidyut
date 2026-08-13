from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.audit import AuditLog
from app.decorators import admin_required

bp = Blueprint('staff', __name__, url_prefix='/staff')

@bp.route('/list')
@login_required
@admin_required
def staff_list():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    staff = User.query.filter_by(
        shop_id=shop_id,
        is_admin=False,
        is_super_admin=False
    ).all()
    return render_template('staff/list.html', staff=staff)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_staff():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return render_template('staff/add.html')
        
        staff = User(
            username=username,
            email=email,
            shop_name=current_user.shop_name,
            shop_id=shop_id,
            is_admin=False,
            is_super_admin=False,
            created_by=current_user.id,
            is_active=True
        )
        staff.set_password(password)
        db.session.add(staff)
        db.session.commit()
        
        flash('Staff added successfully!', 'success')
        return redirect(url_for('staff.staff_list'))
    
    return render_template('staff/add.html')

@bp.route('/audit-logs')
@login_required
@admin_required
def audit_logs():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    
    if current_user.is_super_admin:
        logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    else:
        logs = AuditLog.query.filter_by(shop_id=shop_id).order_by(AuditLog.created_at.desc()).limit(100).all()
    
    return render_template('staff/audit_logs.html', logs=logs)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_staff(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    staff = User.query.filter_by(shop_id=shop_id, id=id, is_admin=False, is_super_admin=False).first_or_404()
    
    if staff.id == current_user.id:
        flash('You cannot delete yourself.', 'danger')
        return redirect(url_for('staff.staff_list'))
    
    db.session.delete(staff)
    db.session.commit()
    flash('Staff member deleted.', 'success')
    return redirect(url_for('staff.staff_list'))