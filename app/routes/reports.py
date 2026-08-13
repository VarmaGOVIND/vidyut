from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.sale import Sale, SaleItem
from app.models.product import Product
from app.models.return_sale import SaleReturn, SaleReturnItem
from app.models.expense import Expense
from app.models.purchase import PurchaseReturn, PurchaseReturnItem
from app.models.supplier import Supplier
from sqlalchemy import func
from datetime import datetime, timedelta
from app.decorators import admin_required

bp = Blueprint('reports', __name__)

@bp.route('/')
@login_required
@admin_required
def reports_list():
    shop_id = current_user.shop_id
    
    if current_user.is_super_admin:
        total_revenue = db.session.query(func.sum(Sale.total_amount)).scalar() or 0.0
        total_profit = db.session.query(func.sum(Sale.profit)).scalar() or 0.0
        total_orders = db.session.query(func.count(Sale.id)).scalar() or 0
        total_returns_revenue = db.session.query(func.sum(SaleReturn.total_refund_amount)).scalar() or 0.0
        return_items = SaleReturnItem.query.all()
        total_returns_profit = 0.0
        for ret_item in return_items:
            product = Product.query.get(ret_item.product_id)
            if product:
                total_returns_profit += (ret_item.refund_amount - (product.cost_price or 0)) * ret_item.quantity
        net_revenue = total_revenue - total_returns_revenue
        net_profit = total_profit - total_returns_profit
        sales = Sale.query.order_by(Sale.created_at.desc()).all()
    else:
        if shop_id is None:
            return redirect(url_for('shop.create_shop'))
        total_revenue = db.session.query(func.sum(Sale.total_amount)).filter(Sale.shop_id == shop_id).scalar() or 0.0
        total_profit = db.session.query(func.sum(Sale.profit)).filter(Sale.shop_id == shop_id).scalar() or 0.0
        total_orders = db.session.query(func.count(Sale.id)).filter(Sale.shop_id == shop_id).scalar() or 0
        total_returns_revenue = db.session.query(func.sum(SaleReturn.total_refund_amount)).filter(SaleReturn.shop_id == shop_id).scalar() or 0.0
        return_items = SaleReturnItem.query.join(SaleReturn).filter(SaleReturn.shop_id == shop_id).all()
        total_returns_profit = 0.0
        for ret_item in return_items:
            product = Product.query.get(ret_item.product_id)
            if product:
                total_returns_profit += (ret_item.refund_amount - (product.cost_price or 0)) * ret_item.quantity
        net_revenue = total_revenue - total_returns_revenue
        net_profit = total_profit - total_returns_profit
        sales = Sale.query.filter_by(shop_id=shop_id).order_by(Sale.created_at.desc()).all()

    return render_template('reports/list.html', 
                           total_revenue=net_revenue, 
                           total_profit=net_profit, 
                           total_orders=total_orders, 
                           sales=sales)

@bp.route('/daily-profit', methods=['GET', 'POST'])
@login_required
@admin_required
def daily_profit():
    shop_id = current_user.shop_id
    
    if request.method == 'POST':
        from_date = request.form.get('from_date')
        to_date = request.form.get('to_date')
    else:
        today = datetime.utcnow().date()
        from_date = today.replace(day=1).strftime('%Y-%m-%d')
        to_date = today.strftime('%Y-%m-%d')

    from_dt = datetime.strptime(from_date, '%Y-%m-%d')
    to_dt = datetime.strptime(to_date, '%Y-%m-%d') + timedelta(days=1)

    if current_user.is_super_admin:
        sales = Sale.query.filter(Sale.created_at >= from_dt, Sale.created_at < to_dt).order_by(Sale.created_at.desc()).all()
        returns = SaleReturn.query.filter(SaleReturn.return_date >= from_dt, SaleReturn.return_date < to_dt).all()
        expenses = Expense.query.filter(Expense.expense_date >= from_dt, Expense.expense_date < to_dt).all()
    else:
        if shop_id is None:
            return redirect(url_for('shop.create_shop'))
        sales = Sale.query.filter(Sale.shop_id == shop_id, Sale.created_at >= from_dt, Sale.created_at < to_dt).order_by(Sale.created_at.desc()).all()
        returns = SaleReturn.query.filter(SaleReturn.shop_id == shop_id, SaleReturn.return_date >= from_dt, SaleReturn.return_date < to_dt).all()
        expenses = Expense.query.filter(Expense.shop_id == shop_id, Expense.expense_date >= from_dt, Expense.expense_date < to_dt).all()

    timeline = []
    
    for sale in sales:
        timeline.append({
            'datetime': sale.created_at,
            'type': 'sale',
            'invoice': sale.invoice_no,
            'amount': sale.total_amount,
            'profit': sale.profit or 0.0,
            'customer': sale.customer_name or 'Walk-in'
        })
    
    for ret in returns:
        ret_items = SaleReturnItem.query.filter_by(return_id=ret.id).all()
        for ret_item in ret_items:
            product = Product.query.get(ret_item.product_id)
            timeline.append({
                'datetime': ret.return_date,
                'type': 'return',
                'invoice': ret.original_sale.invoice_no if ret.original_sale else 'N/A',
                'product': product.name if product else 'Unknown',
                'amount': ret_item.refund_amount,
                'reason': ret.reason or 'N/A'
            })
    
    for exp in expenses:
        timeline.append({
            'datetime': exp.expense_date,
            'type': 'expense',
            'category': exp.category,
            'amount': exp.amount,
            'description': exp.description or 'N/A'
        })
    
    timeline.sort(key=lambda x: x['datetime'], reverse=True)

    total_sales_revenue = sum(t['amount'] for t in timeline if t['type'] == 'sale')
    total_returns = sum(t['amount'] for t in timeline if t['type'] == 'return')
    total_expenses = sum(t['amount'] for t in timeline if t['type'] == 'expense')
    net_revenue = total_sales_revenue - total_returns - total_expenses

    return render_template('reports/daily_profit.html',
        timeline=timeline,
        total_sales_revenue=total_sales_revenue,
        total_returns=total_returns,
        total_expenses=total_expenses,
        net_revenue=net_revenue,
        from_date=from_date,
        to_date=to_date
    )

@bp.route('/sale-details/<filter_type>')
@login_required
@admin_required
def sale_details(filter_type):
    shop_id = current_user.shop_id
    
    if filter_type == 'today':
        today = datetime.utcnow().date()
        if current_user.is_super_admin:
            sales = Sale.query.filter(func.date(Sale.created_at) == today).order_by(Sale.created_at.desc()).all()
        else:
            if shop_id is None:
                return redirect(url_for('shop.create_shop'))
            sales = Sale.query.filter(Sale.shop_id == shop_id, func.date(Sale.created_at) == today).order_by(Sale.created_at.desc()).all()
        title = "Today's Sales Details"
        total_amount = sum(s.total_amount for s in sales)
    else:
        if current_user.is_super_admin:
            sales = Sale.query.order_by(Sale.created_at.desc()).all()
        else:
            if shop_id is None:
                return redirect(url_for('shop.create_shop'))
            sales = Sale.query.filter_by(shop_id=shop_id).order_by(Sale.created_at.desc()).all()
        title = "All Sales Details"
        total_amount = sum(s.total_amount for s in sales)
    
    return render_template('reports/sale_details.html', 
                           sales=sales, 
                           title=title, 
                           total_amount=total_amount,
                           filter_type=filter_type)

@bp.route('/profit-details/<filter_type>')
@login_required
@admin_required
def profit_details(filter_type):
    shop_id = current_user.shop_id
    
    if filter_type == 'today':
        today = datetime.utcnow().date()
        if current_user.is_super_admin:
            sales = Sale.query.filter(func.date(Sale.created_at) == today).order_by(Sale.created_at.desc()).all()
        else:
            if shop_id is None:
                return redirect(url_for('shop.create_shop'))
            sales = Sale.query.filter(Sale.shop_id == shop_id, func.date(Sale.created_at) == today).order_by(Sale.created_at.desc()).all()
        title = "Today's Profit Details"
    else:
        if current_user.is_super_admin:
            sales = Sale.query.order_by(Sale.created_at.desc()).all()
        else:
            if shop_id is None:
                return redirect(url_for('shop.create_shop'))
            sales = Sale.query.filter_by(shop_id=shop_id).order_by(Sale.created_at.desc()).all()
        title = "All Profit Details"
    
    profit_data = []
    total_profit = 0.0
    
    for sale in sales:
        sale_items = SaleItem.query.filter_by(sale_id=sale.id).all()
        for item in sale_items:
            item_profit = (item.price - (item.cost_price or 0)) * item.quantity
            profit_data.append({
                'date': sale.created_at.strftime('%d %b %Y, %I:%M %p'),
                'invoice': sale.invoice_no,
                'product': item.product.name if item.product else 'Unknown',
                'qty': item.quantity,
                'cost_price': item.cost_price or 0,
                'sell_price': item.price,
                'profit': item_profit
            })
            total_profit += item_profit
    
    return render_template('reports/profit_details.html',
                           profit_data=profit_data,
                           title=title,
                           total_profit=total_profit,
                           filter_type=filter_type)

@bp.route('/invoice-search', methods=['GET', 'POST'])
@login_required
@admin_required
def invoice_search():
    shop_id = current_user.shop_id
    invoice = None
    items = []
    returns = []
    error = None
    
    if request.method == 'POST':
        invoice_no = request.form.get('invoice_no', '').strip()
        if invoice_no:
            if current_user.is_super_admin:
                invoice = Sale.query.filter_by(invoice_no=invoice_no).first()
            else:
                if shop_id is None:
                    return redirect(url_for('shop.create_shop'))
                invoice = Sale.query.filter_by(shop_id=shop_id, invoice_no=invoice_no).first()
            if invoice:
                items = SaleItem.query.filter_by(sale_id=invoice.id).all()
                if current_user.is_super_admin:
                    returns = SaleReturn.query.filter_by(original_sale_id=invoice.id).all()
                else:
                    returns = SaleReturn.query.filter_by(shop_id=shop_id, original_sale_id=invoice.id).all()
            else:
                error = f'Invoice {invoice_no} not found'
    
    return render_template('reports/invoice_search.html', 
                           invoice=invoice, 
                           items=items, 
                           returns=returns,
                           error=error)