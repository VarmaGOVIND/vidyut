from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.product import Product
from app.models.audit import AuditLog
from app.utils.excel_utils import read_products_from_excel
from app.decorators import admin_required
from datetime import datetime
import os

bp = Blueprint('import_products', __name__, url_prefix='/import-products')

@bp.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def import_products():
    if current_user.shop_id is None:
        flash('No shop found.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    shop_id = current_user.shop_id
    
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected.', 'danger')
            return redirect(url_for('import_products.import_products'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'danger')
            return redirect(url_for('import_products.import_products'))
        
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            flash('Please upload Excel or CSV file.', 'danger')
            return redirect(url_for('import_products.import_products'))
        
        try:
            products_data = read_products_from_excel(file)
        except Exception as e:
            flash(f'Error reading file: {str(e)}', 'danger')
            return redirect(url_for('import_products.import_products'))
        
        added = 0
        errors = []
        
        for idx, row in enumerate(products_data, start=2):
            try:
                name = row.get('name', '').strip()
                category = row.get('category', 'Uncategorized').strip()
                cost_price = float(row.get('cost_price', 0))
                selling_price = float(row.get('selling_price', 0))
                stock = int(row.get('stock', 0))
                min_stock = int(row.get('min_stock', 5))
                expiry_date_str = row.get('expiry_date')
                expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None
                
                if not name:
                    errors.append(f'Row {idx}: Name is required')
                    continue
                
                existing = Product.query.filter_by(shop_id=shop_id, name=name).first()
                if existing:
                    existing.cost_price = cost_price
                    existing.selling_price = selling_price
                    existing.stock = stock
                    existing.min_stock = min_stock
                    existing.expiry_date = expiry_date
                    existing.category = category
                else:
                    category_code = category[:3].upper() if len(category) >= 3 else 'UNC'
                    existing_count = Product.query.filter_by(shop_id=shop_id, category_code=category_code).count()
                    sku = f"{category_code}-{str(existing_count + 1).zfill(3)}"
                    
                    product = Product(
                        shop_id=shop_id,
                        name=name,
                        sku=sku,
                        category=category,
                        category_code=category_code,
                        cost_price=cost_price,
                        selling_price=selling_price,
                        stock=stock,
                        min_stock=min_stock,
                        expiry_date=expiry_date
                    )
                    db.session.add(product)
                
                added += 1
                
            except Exception as e:
                errors.append(f'Row {idx}: {str(e)}')
        
        db.session.commit()
        
        audit = AuditLog(
            user_id=current_user.id,
            shop_id=shop_id,
            action='Import Products',
            details=f'Imported {added} products via Excel'
        )
        db.session.add(audit)
        db.session.commit()
        
        flash(f'Successfully imported {added} products!', 'success')
        if errors:
            flash(f'Errors: {"; ".join(errors)}', 'warning')
        
        return redirect(url_for('import_products.import_products'))
    
    return render_template('import_products/import.html')

@bp.route('/template')
@login_required
def download_template():
    from io import BytesIO
    import pandas as pd
    from flask import send_file
    
    df = pd.DataFrame({
        'name': ['Product 1', 'Product 2'],
        'category': ['Category 1', 'Category 2'],
        'cost_price': [100.0, 200.0],
        'selling_price': [120.0, 250.0],
        'stock': [10, 20],
        'min_stock': [5, 10],
        'expiry_date': ['2025-12-31', '']
    })
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Products')
    output.seek(0)
    
    return send_file(output, download_name='product_import_template.xlsx', as_attachment=True)