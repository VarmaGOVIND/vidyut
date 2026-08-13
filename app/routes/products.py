from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.product import Product
from app.models.audit import AuditLog
from app.models.batch import InventoryBatch
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.decorators import admin_required
from datetime import datetime, date, timedelta

bp = Blueprint('products', __name__)

@bp.route('/')
@bp.route('/list')
@login_required
@admin_required
def product_list():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    category_filter = request.args.get('category')
    today = date.today()
    expiry_soon = today + timedelta(days=7)
    
    if not category_filter:
        categories = db.session.query(func.trim(Product.category)).distinct().filter(Product.shop_id == shop_id).all()
        category_stats = []
        for (cat,) in categories:
            if cat:
                cat = cat.strip()
                count = Product.query.filter_by(shop_id=shop_id).filter(func.trim(Product.category) == cat).count()
                low_stock_count = Product.query.filter_by(shop_id=shop_id).filter(func.trim(Product.category) == cat, Product.stock <= Product.min_stock).count()
                first_product = Product.query.filter_by(shop_id=shop_id).filter(func.trim(Product.category) == cat).first()
                category_stats.append({
                    'name': cat,
                    'code': first_product.category_code if first_product else 'N/A',
                    'count': count,
                    'low_stock': low_stock_count
                })
        return render_template('products/categories.html', categories=category_stats)
    
    products = Product.query.filter_by(shop_id=shop_id, category=category_filter).all()
    return render_template('products/list.html', 
                           products=products, 
                           current_category=category_filter, 
                           today=today,
                           expiry_soon=expiry_soon)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required 
def add_product():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    category = request.args.get('category')
    category_code = request.args.get('category_code')
    product_name = request.args.get('name')
    
    if not category and product_name:
        existing = Product.query.filter(Product.shop_id == shop_id, Product.name.ilike(f'%{product_name}%')).first()
        if existing:
            category = existing.category
            category_code = existing.category_code
    
    if request.method == 'POST':
        name = (request.form.get('name') or '').strip()
        category = (request.form.get('category') or '').strip()
        category_code = (request.form.get('category_code') or '').strip()
        selling_price = float(request.form.get('selling_price'))
        cost_price = float(request.form.get('cost_price'))
        stock = int(request.form.get('stock', 0))
        min_stock = int(request.form.get('min_stock', 5))
        expiry_date_str = request.form.get('expiry_date')
        expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None
        
        existing_product = Product.query.filter_by(shop_id=shop_id, name=name).first()
        if existing_product:
            flash(f'Product "{name}" already exists!', 'danger')
            return render_template('products/add.html', category=category, category_code=category_code, page_title="Add New Product", product_name=name)
        
        last_product = Product.query.filter_by(shop_id=shop_id, category_code=category_code).order_by(Product.id.desc()).first()
        next_number = 1
        if last_product and last_product.sku:
            try:
                last_number = int(last_product.sku.split('-')[-1])
                next_number = last_number + 1
            except (ValueError, IndexError):
                existing_count = Product.query.filter_by(shop_id=shop_id, category_code=category_code).count()
                next_number = existing_count + 1
        new_sku = f"{category_code}-{str(next_number).zfill(3)}"
        
        product = Product(
            shop_id=shop_id,
            name=name,
            sku=new_sku,
            category=category,
            category_code=category_code,
            selling_price=selling_price,
            cost_price=cost_price,
            stock=stock,
            min_stock=min_stock,
            expiry_date=expiry_date
        )
        db.session.add(product)
        db.session.commit()
        
        audit = AuditLog(user_id=current_user.id, shop_id=shop_id, action=f"Added product {name} with SKU {new_sku}")
        db.session.add(audit)
        db.session.commit()
        
        flash('Product added successfully', 'success')
        return redirect(url_for('products.product_list', category=category))
        
    if category and not category_code:
        existing = Product.query.filter_by(shop_id=shop_id, category=category).first()
        if existing and existing.category_code:
            category_code = existing.category_code

    if category:
        page_title = f"Add New Product in {category}"
    else:
        page_title = "Add New Product"
        
    return render_template('products/add.html', category=category, category_code=category_code, page_title=page_title, product_name=product_name)

@bp.route('/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required 
def edit_product(product_id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    product = Product.query.filter_by(shop_id=shop_id, id=product_id).first_or_404()
    
    if request.method == 'POST':
        product.name = (request.form.get('name') or '').strip()
        product.category = (request.form.get('category') or '').strip()
        product.category_code = (request.form.get('category_code') or '').strip()
        product.selling_price = float(request.form.get('selling_price'))
        product.cost_price = float(request.form.get('cost_price'))
        product.stock = int(request.form.get('stock', 0))
        product.min_stock = int(request.form.get('min_stock', 5))
        expiry_date_str = request.form.get('expiry_date')
        product.expiry_date = datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None
        
        db.session.commit()
        
        audit = AuditLog(user_id=current_user.id, shop_id=shop_id, action=f"Updated product {product.name}")
        db.session.add(audit)
        db.session.commit()
        
        flash('Product updated successfully', 'success')
        return redirect(url_for('products.product_list', category=product.category))
        
    return render_template('products/edit.html', product=product)

@bp.route('/delete/<int:product_id>', methods=['POST'])
@login_required
@admin_required
def delete_product(product_id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    product = Product.query.filter_by(shop_id=shop_id, id=product_id).first_or_404()
    category = product.category
    
    try:
        db.session.delete(product)
        db.session.commit()
        
        audit = AuditLog(user_id=current_user.id, shop_id=shop_id, action=f"Deleted product {product.name}")
        db.session.add(audit)
        db.session.commit()
        
        flash('Product deleted successfully', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('Cannot delete this product because it is linked to past sales records. Please set its stock to 0 instead.', 'danger')
        
    return redirect(url_for('products.product_list', category=category))

@bp.route('/view')
@login_required
def staff_product_view():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    category_filter = request.args.get('category')
    today = date.today()
    expiry_soon = today + timedelta(days=7)
    
    if not category_filter:
        categories = db.session.query(func.trim(Product.category)).distinct().filter(Product.shop_id == shop_id).all()
        category_stats = []
        for (cat,) in categories:
            if cat:
                cat = cat.strip()
                count = Product.query.filter_by(shop_id=shop_id).filter(func.trim(Product.category) == cat).count()
                low_stock_count = Product.query.filter_by(shop_id=shop_id).filter(func.trim(Product.category) == cat, Product.stock <= Product.min_stock).count()
                category_stats.append({
                    'name': cat,
                    'count': count,
                    'low_stock': low_stock_count
                })
        return render_template('products/staff_view.html', categories=category_stats, mode='categories')
    
    products = Product.query.filter_by(shop_id=shop_id, category=category_filter).order_by(Product.name).all()
    return render_template('products/staff_view.html', 
                           products=products, 
                           current_category=category_filter, 
                           today=today,
                           expiry_soon=expiry_soon,
                           mode='products')

@bp.route('/sync-stock', methods=['POST'])
@login_required
@admin_required
def sync_stock():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    products = Product.query.filter_by(shop_id=shop_id).all()
    synced = 0
    
    for product in products:
        batches = InventoryBatch.query.filter_by(product_id=product.id).all()
        total_remaining = sum(b.qty_remaining for b in batches)
        
        if product.stock != total_remaining:
            product.stock = total_remaining
            synced += 1
    
    db.session.commit()
    flash(f'Stock synced for {synced} products.', 'success')
    return redirect(url_for('products.product_list'))

@bp.route('/delete-category/<category_name>', methods=['POST'])
@login_required
@admin_required
def delete_category(category_name):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    products = Product.query.filter_by(shop_id=shop_id).filter(func.trim(Product.category) == category_name.strip()).all()
    
    try:
        for product in products:
            db.session.delete(product)
        
        db.session.commit()
        
        audit = AuditLog(user_id=current_user.id, shop_id=shop_id, action=f"Deleted entire category: {category_name}")
        db.session.add(audit)
        db.session.commit()
        
        flash(f'Category "{category_name}" and all its products have been deleted successfully.', 'success')
        
    except IntegrityError:
        db.session.rollback()
        flash(f'Cannot delete category "{category_name}" because one or more of its products are linked to past sales records. Please resolve those products first.', 'danger')
        
    return redirect(url_for('products.product_list'))

@bp.route('/<int:id>/batches/update', methods=['POST'])
@login_required
@admin_required
def update_batch(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    batch = InventoryBatch.query.join(Product).filter(Product.shop_id == shop_id, InventoryBatch.id == id).first_or_404()
    
    selling_price = request.form.get('selling_price')
    purchase_rate = request.form.get('purchase_rate')
    
    if selling_price:
        batch.selling_price = float(selling_price)
        batch.product.selling_price = float(selling_price)
        
    if purchase_rate:
        batch.purchase_rate = float(purchase_rate)
        batch.product.cost_price = float(purchase_rate)
    
    db.session.commit()
    flash('Batch and Product prices updated successfully', 'success')
    return redirect(url_for('products.view_batches', id=batch.product_id))

@bp.route('/<int:id>/batches')
@login_required
@admin_required
def view_batches(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    product = Product.query.filter_by(shop_id=shop_id, id=id).first_or_404()
    batches = InventoryBatch.query.filter_by(product_id=id).all()

    total_cost = sum(b.purchase_rate * b.qty_remaining for b in batches)
    total_qty = sum(b.qty_remaining for b in batches)
    
    if total_qty > 0:
        true_avg_cost = total_cost / total_qty
    else:
        true_avg_cost = product.cost_price

    return render_template('products/batches.html', 
                           product=product, 
                           batches=batches, 
                           true_avg_cost=true_avg_cost)

@bp.route('/api/check-product')
@login_required
def check_product():
    if current_user.shop_id is None:
        return jsonify({'exists': False})
    
    shop_id = current_user.shop_id
    name = request.args.get('name', '')
    if not name:
        return jsonify({'exists': False})
    
    product = Product.query.filter(Product.shop_id == shop_id, Product.name.ilike(f'%{name}%')).first()
    if product:
        return jsonify({
            'exists': True,
            'category': product.category,
            'category_code': product.category_code
        })
    return jsonify({'exists': False})