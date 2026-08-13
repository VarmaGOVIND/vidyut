from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.shop import Shop
from app.models.audit import AuditLog

bp = Blueprint('shop', __name__, url_prefix='/shop')

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_shop():
    if current_user.shop_id is not None:
        flash('You already have a shop.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    if current_user.is_super_admin:
        flash('Super Admin does not need a shop.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        address = request.form.get('address', '').strip()
        phone = request.form.get('phone', '').strip()
        gst_number = request.form.get('gst_number', '').strip()
        
        if not shop_name:
            flash('Shop name is required.', 'danger')
            return render_template('auth/create_shop.html')
        
        shop = Shop(
            shop_name=shop_name,
            owner_id=current_user.id,
            address=address,
            phone=phone,
            gst_number=gst_number,
            is_active=True
        )
        db.session.add(shop)
        db.session.flush()
        
        current_user.shop_id = shop.id
        current_user.is_admin = True
        db.session.commit()
        
        audit = AuditLog(
            user_id=current_user.id,
            shop_id=shop.id,
            action='Shop Created',
            details=f'Shop "{shop_name}" created by {current_user.username}'
        )
        db.session.add(audit)
        db.session.commit()
        
        flash('Shop created successfully! Welcome to VIDYUT.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/create_shop.html')