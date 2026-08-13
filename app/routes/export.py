from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.sale import Sale, SaleItem
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.purchase import Purchase
from app.models.expense import Expense
from app.utils.excel_utils import create_excel_from_data
from app.decorators import admin_required
from datetime import datetime  

bp = Blueprint('export', __name__, url_prefix='/export')

@bp.route('/sales')
@login_required
@admin_required
def export_sales():
    if current_user.shop_id is None:
        flash('No shop found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    shop_id = current_user.shop_id
    sales = Sale.query.filter_by(shop_id=shop_id).order_by(Sale.created_at.desc()).all()
    
    data = []
    for sale in sales:
        items = SaleItem.query.filter_by(sale_id=sale.id).all()
        item_names = ', '.join([item.product.name if item.product else 'Unknown' for item in items])
        data.append([
            sale.invoice_no,
            sale.created_at.strftime('%d %b %Y, %I:%M %p'),
            sale.customer_name or 'Walk-in',
            sale.total_amount,
            sale.profit or 0.0,
            item_names,
            sale.status
        ])
    
    columns = ['Invoice No', 'Date', 'Customer', 'Amount', 'Profit', 'Items', 'Status']
    filename = f'sales_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return create_excel_from_data(data, columns, filename)

@bp.route('/products')
@login_required
@admin_required
def export_products():
    if current_user.shop_id is None:
        flash('No shop found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    shop_id = current_user.shop_id
    products = Product.query.filter_by(shop_id=shop_id).all()
    
    data = [[
        p.name,
        p.sku,
        p.category,
        p.cost_price,
        p.selling_price,
        p.stock,
        p.min_stock,
        p.expiry_date.strftime('%Y-%m-%d') if p.expiry_date else 'N/A'
    ] for p in products]
    
    columns = ['Name', 'SKU', 'Category', 'Cost Price', 'Selling Price', 'Stock', 'Min Stock', 'Expiry Date']
    filename = f'products_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return create_excel_from_data(data, columns, filename)

@bp.route('/suppliers')
@login_required
@admin_required
def export_suppliers():
    if current_user.shop_id is None:
        flash('No shop found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    shop_id = current_user.shop_id
    suppliers = Supplier.query.filter_by(shop_id=shop_id).all()
    
    data = [[
        s.name,
        s.phone or 'N/A',
        s.email or 'N/A',
        s.address or 'N/A',
        s.gstin or 'N/A',
        'Active' if s.is_active else 'Inactive'
    ] for s in suppliers]
    
    columns = ['Name', 'Phone', 'Email', 'Address', 'GSTIN', 'Status']
    filename = f'suppliers_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.xlsx'
    
    return create_excel_from_data(data, columns, filename)