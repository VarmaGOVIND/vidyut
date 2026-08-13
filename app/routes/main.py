from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.sale import Sale
from app.models.product import Product
from app.models.expense import Expense
from app.models.customer import Customer
from app.models.shop import Shop
from app.models.audit import AuditLog
from app.models.user import User
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('main', __name__)

@bp.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_super_admin:
        total_shops = Shop.query.filter_by(is_active=True).count()
        total_users = User.query.count()
        total_staff = User.query.filter_by(is_admin=False, is_super_admin=False).count()
        total_billing = db.session.query(func.sum(Sale.total_amount)).scalar() or 0.0
        all_shops = Shop.query.filter_by(is_active=True).all()
        recent_logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
        
        return render_template(
            'super_admin/dashboard.html',
            total_shops=total_shops,
            total_users=total_users,
            total_staff=total_staff,
            total_billing=total_billing,
            all_shops=all_shops,
            recent_logs=recent_logs
        )
    
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop = Shop.query.get(current_user.shop_id)
    if not shop:
        flash('Shop not found.', 'danger')
        return redirect(url_for('auth.logout'))
    
    if shop.is_blocked:
        return render_template('blocked.html', shop=shop)
    
    if shop.is_maintenance and not current_user.is_admin and not current_user.is_super_admin:
        return render_template('maintenance.html', shop=shop)
    
    shop_id = current_user.shop_id
    today = datetime.utcnow().date()
    
    from_date_str = request.args.get('from_date')
    to_date_str = request.args.get('to_date')
    
    if from_date_str and to_date_str:
        try:
            from_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            to_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
            if from_date > to_date:
                flash('From date cannot be after To date.', 'danger')
                from_date = today - timedelta(days=6)
                to_date = today
            filter_type = 'custom'
        except ValueError:
            from_date = today - timedelta(days=6)
            to_date = today
            filter_type = 'week'
    else:
        filter_type = request.args.get('filter', 'week')
        
        if filter_type == 'today':
            from_date = today
            to_date = today
        elif filter_type == 'week':
            from_date = today - timedelta(days=6)
            to_date = today
        elif filter_type == 'month':
            from_date = today.replace(day=1)
            to_date = today
        elif filter_type == 'all':
            from_date = datetime(2020, 1, 1).date()
            to_date = today
        else:
            from_date = today - timedelta(days=6)
            to_date = today
            filter_type = 'week'
    
    today_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.shop_id == shop_id,
        func.date(Sale.created_at) == today
    ).scalar() or 0.0
    
    today_profit = db.session.query(func.sum(Sale.profit)).filter(
        Sale.shop_id == shop_id,
        func.date(Sale.created_at) == today
    ).scalar() or 0.0
    if today_profit is None or today_profit < 0:
        today_profit = 0.0
    
    today_orders = db.session.query(func.count(Sale.id)).filter(
        Sale.shop_id == shop_id,
        func.date(Sale.created_at) == today
    ).scalar() or 0
    
    total_revenue = db.session.query(func.sum(Sale.total_amount)).filter(
        Sale.shop_id == shop_id
    ).scalar() or 0.0
    
    total_profit = db.session.query(func.sum(Sale.profit)).filter(
        Sale.shop_id == shop_id
    ).scalar() or 0.0
    if total_profit is None or total_profit < 0:
        total_profit = 0.0
    
    today_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.shop_id == shop_id,
        func.date(Expense.expense_date) == today
    ).scalar() or 0.0
    
    net_profit = today_profit - today_expenses
    
    low_stock_count = db.session.query(func.count(Product.id)).filter(
        Product.shop_id == shop_id,
        Product.stock <= Product.min_stock
    ).scalar() or 0
    
    total_customers = db.session.query(func.count(Customer.id)).filter(
        Customer.shop_id == shop_id,
        Customer.is_active == True
    ).scalar() or 0
    
    recent_sales = Sale.query.filter_by(shop_id=shop_id).order_by(Sale.created_at.desc()).limit(5).all()
    
    chart_labels = []
    chart_revenue = []
    chart_orders = []
    
    if filter_type == 'all':
        monthly_sales = db.session.query(
            func.date_trunc('month', Sale.created_at).label('month'),
            func.sum(Sale.total_amount).label('revenue'),
            func.count(Sale.id).label('orders')
        ).filter(
            Sale.shop_id == shop_id,
            func.date(Sale.created_at) >= from_date,
            func.date(Sale.created_at) <= to_date
        ).group_by(func.date_trunc('month', Sale.created_at)).order_by(func.date_trunc('month', Sale.created_at)).all()
        
        for s in monthly_sales:
            chart_labels.append(s.month.strftime('%b %Y'))
            chart_revenue.append(s.revenue)
            chart_orders.append(s.orders)
        
        if not monthly_sales:
            chart_labels = ['No Data']
            chart_revenue = [0]
            chart_orders = [0]
    
    else:
        daily_sales = db.session.query(
            func.date(Sale.created_at).label('date'),
            func.sum(Sale.total_amount).label('revenue'),
            func.count(Sale.id).label('orders')
        ).filter(
            Sale.shop_id == shop_id,
            func.date(Sale.created_at) >= from_date,
            func.date(Sale.created_at) <= to_date
        ).group_by(func.date(Sale.created_at)).all()
        
        date_range = (to_date - from_date).days + 1
        
        if daily_sales:
            sales_dict = {s.date: (s.revenue, s.orders) for s in daily_sales}
            for i in range(date_range):
                check_date = from_date + timedelta(days=i)
                chart_labels.append(check_date.strftime('%d %b'))
                if check_date in sales_dict:
                    chart_revenue.append(sales_dict[check_date][0])
                    chart_orders.append(sales_dict[check_date][1])
                else:
                    chart_revenue.append(0.0)
                    chart_orders.append(0)
        else:
            for i in range(date_range):
                check_date = from_date + timedelta(days=i)
                chart_labels.append(check_date.strftime('%d %b'))
                chart_revenue.append(0.0)
                chart_orders.append(0)

    return render_template(
        'dashboard.html',
        today_revenue=today_revenue,
        today_profit=today_profit,
        total_revenue=total_revenue,
        total_profit=total_profit,
        today_orders=today_orders,
        today_expenses=today_expenses,
        net_profit=net_profit,
        low_stock_count=low_stock_count,
        total_customers=total_customers,
        recent_sales=recent_sales,
        chart_labels=chart_labels,
        chart_revenue=chart_revenue,
        chart_orders=chart_orders,
        filter_type=filter_type,
        from_date=from_date.strftime('%Y-%m-%d'),
        to_date=to_date.strftime('%Y-%m-%d')
    )