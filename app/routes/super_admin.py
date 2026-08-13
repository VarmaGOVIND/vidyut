from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.shop import Shop
from app.models.sale import Sale, SaleItem
from app.models.purchase import Purchase, PurchaseItem
from app.models.product import Product
from app.models.return_sale import SaleReturn
from app.models.purchase import PurchaseReturn
from sqlalchemy import func
from datetime import datetime
from app.models.audit import AuditLog
from app.utils.excel_utils import create_excel_from_data

bp = Blueprint('super_admin', __name__, url_prefix='/super-admin')

@bp.route('/register', methods=['GET', 'POST'])
def register_super_admin():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        secret_key = request.form.get('secret_key')
        
        expected_secret = current_app.config.get('SUPER_ADMIN_SECRET_KEY', 'VIDYUT_SUPER_SECRET_2026')
        
        if secret_key != expected_secret:
            flash('Invalid secret key!', 'danger')
            return render_template('super_admin/register.html')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered.', 'danger')
            return render_template('super_admin/register.html')
        
        user = User(
            username=username,
            email=email,
            shop_name='Super Admin',
            is_admin=True,
            is_super_admin=True,
            shop_id=None,
            is_active=True
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash('Super Admin account created successfully! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('super_admin/register.html')

@bp.route('/shops')
@login_required
def all_shops():
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    shops = Shop.query.all()
    return render_template('super_admin/shops.html', shops=shops)

@bp.route('/shop/<int:shop_id>')
@login_required
def shop_detail(shop_id):
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    shop = Shop.query.get_or_404(shop_id)
    users = User.query.filter_by(shop_id=shop_id).all()
    sales = Sale.query.filter_by(shop_id=shop_id).order_by(Sale.created_at.desc()).limit(20).all()
    
    total_sales = db.session.query(func.sum(Sale.total_amount)).filter(Sale.shop_id == shop_id).scalar() or 0.0
    total_orders = db.session.query(func.count(Sale.id)).filter(Sale.shop_id == shop_id).scalar() or 0
    
    return render_template('super_admin/shop_detail.html',
                           shop=shop,
                           users=users,
                           sales=sales,
                           total_sales=total_sales,
                           total_orders=total_orders)


@bp.route('/shop/<int:shop_id>/block', methods=['POST'])
@login_required
def block_shop(shop_id):
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    shop = Shop.query.get_or_404(shop_id)
    reason = request.form.get('reason', '').strip()
    
    shop.is_blocked = True
    shop.block_reason = reason
    shop.blocked_by = current_user.id
    shop.blocked_at = datetime.utcnow()
    db.session.commit()
    
    audit = AuditLog(
        user_id=current_user.id,
        shop_id=shop.id,
        action='Shop Blocked',
        details=f'Shop "{shop.shop_name}" blocked by {current_user.username}. Reason: {reason or "No reason"}'
    )
    db.session.add(audit)
    db.session.commit()
    
    flash(f'Shop "{shop.shop_name}" has been blocked.', 'success')
    return redirect(url_for('super_admin.shop_detail', shop_id=shop_id))

@bp.route('/shop/<int:shop_id>/unblock', methods=['POST'])
@login_required
def unblock_shop(shop_id):
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    shop = Shop.query.get_or_404(shop_id)
    
    shop.is_blocked = False
    shop.block_reason = None
    shop.blocked_by = None
    shop.blocked_at = None
    db.session.commit()
    
    audit = AuditLog(
        user_id=current_user.id,
        shop_id=shop.id,
        action='Shop Unblocked',
        details=f'Shop "{shop.shop_name}" unblocked by {current_user.username}'
    )
    db.session.add(audit)
    db.session.commit()
    
    flash(f'Shop "{shop.shop_name}" has been unblocked.', 'success')
    return redirect(url_for('super_admin.shop_detail', shop_id=shop_id))


@bp.route('/export/sales')
@login_required
def export_all_sales():
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    sales = Sale.query.order_by(Sale.created_at.desc()).all()
    data = []
    for sale in sales:
        items = SaleItem.query.filter_by(sale_id=sale.id).all()
        item_names = ', '.join([item.product.name if item.product else 'Unknown' for item in items])
        shop_name = sale.shop.shop_name if sale.shop else 'N/A'
        data.append([
            sale.invoice_no,
            shop_name,
            sale.created_at.strftime('%d %b %Y, %I:%M %p'),
            sale.customer_name or 'Walk-in',
            sale.total_amount,
            sale.profit or 0.0,
            item_names,
            sale.status
        ])
    
    columns = ['Invoice No', 'Shop', 'Date', 'Customer', 'Amount', 'Profit', 'Items', 'Status']
    filename = f'all_sales_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return create_excel_from_data(data, columns, filename)

@bp.route('/shop/<int:shop_id>/maintenance', methods=['POST'])
@login_required
def toggle_maintenance(shop_id):
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    shop = Shop.query.get_or_404(shop_id)
    shop.is_maintenance = not shop.is_maintenance
    db.session.commit()
    
    status = "enabled" if shop.is_maintenance else "disabled"
    flash(f'Maintenance mode {status} for "{shop.shop_name}".', 'success')
    return redirect(url_for('super_admin.shop_detail', shop_id=shop_id))

@bp.route('/users')
@login_required
def all_users():
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    users = User.query.all()
    return render_template('super_admin/users.html', users=users)

@bp.route('/staff')
@login_required
def all_staff():
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    staff = User.query.filter_by(is_admin=False, is_super_admin=False).all()
    return render_template('super_admin/staff.html', staff=staff)

@bp.route('/products')
@login_required
def all_products():
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    products = Product.query.all()
    return render_template('super_admin/products.html', products=products)

@bp.route('/sales')
@login_required
def all_sales():
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    sales = Sale.query.order_by(Sale.created_at.desc()).limit(100).all()
    total_revenue = db.session.query(func.sum(Sale.total_amount)).scalar() or 0.0
    total_orders = db.session.query(func.count(Sale.id)).scalar() or 0
    
    return render_template('super_admin/sales.html',
                           sales=sales,
                           total_revenue=total_revenue,
                           total_orders=total_orders)

@bp.route('/purchases')
@login_required
def all_purchases():
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    purchases = Purchase.query.order_by(Purchase.created_at.desc()).limit(100).all()
    total_purchases = db.session.query(func.sum(Purchase.total_amount)).scalar() or 0.0
    
    return render_template('super_admin/purchases.html',
                           purchases=purchases,
                           total_purchases=total_purchases)

@bp.route('/returns')
@login_required
def all_returns():
    if not current_user.is_super_admin:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    sale_returns = SaleReturn.query.order_by(SaleReturn.return_date.desc()).limit(50).all()
    purchase_returns = PurchaseReturn.query.order_by(PurchaseReturn.created_at.desc()).limit(50).all()
    
    return render_template('super_admin/returns.html',
                           sale_returns=sale_returns,
                           purchase_returns=purchase_returns)