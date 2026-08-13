from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.sale import Sale, SaleItem
from app.models.product import Product
from app.models.shop import Shop
from app.decorators import admin_required
from sqlalchemy import func
from datetime import datetime, timedelta

bp = Blueprint('gst_reports', __name__, url_prefix='/gst-reports')

@bp.route('/')
@login_required
@admin_required
def gst_dashboard():
    if current_user.shop_id is None:
        flash('No shop found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    shop_id = current_user.shop_id
    today = datetime.utcnow().date()
    month_start = today.replace(day=1)
    
    # Monthly GST sales
    monthly_sales = db.session.query(
        func.sum(Sale.total_amount).label('total'),
        func.count(Sale.id).label('count')
    ).filter(
        Sale.shop_id == shop_id,
        Sale.created_at >= month_start,
        Sale.created_at < today + timedelta(days=1)
    ).first()
    
    # GST-wise breakdown
    products = Product.query.filter_by(shop_id=shop_id).all()
    gst_rates = {}
    for p in products:
        rate = 0
        if p.selling_price > 1000:
            rate = 18
        elif p.selling_price > 500:
            rate = 12
        elif p.selling_price > 100:
            rate = 5
        else:
            rate = 0
        
        gst_rates[rate] = gst_rates.get(rate, 0) + 1
    
    return render_template('gst_reports/dashboard.html',
                           monthly_sales=monthly_sales,
                           gst_rates=gst_rates)

@bp.route('/gst-return')
@login_required
@admin_required
def gst_return():
    if current_user.shop_id is None:
        flash('No shop found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    shop_id = current_user.shop_id
    today = datetime.utcnow().date()
    month_start = today.replace(day=1)
    
    # Sales for GST return
    sales = Sale.query.filter(
        Sale.shop_id == shop_id,
        Sale.created_at >= month_start,
        Sale.created_at < today + timedelta(days=1)
    ).all()
    
    gst_data = []
    total_taxable = 0
    total_gst = 0
    
    for sale in sales:
        items = SaleItem.query.filter_by(sale_id=sale.id).all()
        for item in items:
            product = Product.query.get(item.product_id)
            if product:
                rate = 0
                if product.selling_price > 1000:
                    rate = 18
                elif product.selling_price > 500:
                    rate = 12
                elif product.selling_price > 100:
                    rate = 5
                
                taxable = item.price * item.quantity
                gst = taxable * rate / 100
                total_taxable += taxable
                total_gst += gst
                
                gst_data.append({
                    'invoice': sale.invoice_no,
                    'product': product.name,
                    'qty': item.quantity,
                    'rate': rate,
                    'taxable': taxable,
                    'gst': gst
                })
    
    return render_template('gst_reports/return.html',
                           gst_data=gst_data,
                           total_taxable=total_taxable,
                           total_gst=total_gst)