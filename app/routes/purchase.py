from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models.purchase import Purchase, PurchaseItem
from app.models.batch import InventoryBatch
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.audit import AuditLog
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import json
from app.decorators import admin_required

bp = Blueprint('purchase', __name__, url_prefix='/purchase')

@bp.route('/list')
@login_required
@admin_required
def purchase_list():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    purchases = Purchase.query.filter_by(shop_id=shop_id).order_by(Purchase.created_at.desc()).all()
    return render_template('purchase/list.html', purchases=purchases)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_purchase():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    
    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id')
        invoice_no = request.form.get('invoice_no')
        purchase_date_str = request.form.get('purchase_date')
        payment_status = request.form.get('payment_status')
        notes = request.form.get('notes')
        items_json = request.form.get('cart_items')

        if not supplier_id:
            suppliers = Supplier.query.filter_by(shop_id=shop_id, is_active=True).order_by(Supplier.name).all()
            categories = [row[0] for row in db.session.query(Product.category).distinct().filter(Product.shop_id == shop_id, Product.category.isnot(None)).all()]
            flash('Please select a supplier.', 'danger')
            return render_template('purchase/add.html', suppliers=suppliers, categories=categories, datetime=datetime)

        if not items_json:
            suppliers = Supplier.query.filter_by(shop_id=shop_id, is_active=True).order_by(Supplier.name).all()
            categories = [row[0] for row in db.session.query(Product.category).distinct().filter(Product.shop_id == shop_id, Product.category.isnot(None)).all()]
            flash('Please add at least one product to cart.', 'danger')
            return render_template('purchase/add.html', suppliers=suppliers, categories=categories, datetime=datetime)

        try:
            items = json.loads(items_json)
        except:
            suppliers = Supplier.query.filter_by(shop_id=shop_id, is_active=True).order_by(Supplier.name).all()
            categories = [row[0] for row in db.session.query(Product.category).distinct().filter(Product.shop_id == shop_id, Product.category.isnot(None)).all()]
            flash('Invalid cart data.', 'danger')
            return render_template('purchase/add.html', suppliers=suppliers, categories=categories, datetime=datetime)

        purchase_date = datetime.strptime(purchase_date_str, '%Y-%m-%d') if purchase_date_str else datetime.utcnow()
        total_amount = sum(float(item['total']) for item in items)

        purchase = Purchase(
            shop_id=shop_id,
            supplier_id=supplier_id,
            invoice_no=invoice_no,
            purchase_date=purchase_date,
            total_amount=total_amount,
            payment_status=payment_status,
            notes=notes,
            created_by=current_user.id
        )
        db.session.add(purchase)
        db.session.flush()

        for item in items:
            if item.get('is_new'):
                product_name = item.get('name')
                category_name = item.get('category', 'Uncategorized')
                rate = float(item.get('rate'))
                
                product = Product.query.filter_by(shop_id=shop_id, name=product_name).first()
                if not product:
                    existing_count = Product.query.filter_by(shop_id=shop_id, category=category_name).count()
                    category_code = category_name[:3].upper() if len(category_name) >= 3 else 'UNC'
                    new_sku = f"{category_code}-{str(existing_count + 1).zfill(3)}"
                    
                    product = Product(
                        shop_id=shop_id,
                        name=product_name,
                        sku=new_sku,
                        category=category_name,
                        category_code=category_code,
                        selling_price=rate,
                        cost_price=rate,
                        stock=0,
                        min_stock=5
                    )
                    db.session.add(product)
                    db.session.flush()
            else:
                product = Product.query.filter_by(shop_id=shop_id, id=item['id']).first()
                if not product:
                    continue

            expiry_date = None
            if item.get('expiry_date'):
                try:
                    expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d').date()
                except:
                    pass

            purchase_item = PurchaseItem(
                shop_id=shop_id,
                purchase_id=purchase.id,
                product_id=product.id,
                quantity=int(item['qty']),
                unit_cost=float(item['rate']),
                tax=float(item.get('tax', 0)),
                discount=float(item.get('discount', 0))
            )
            db.session.add(purchase_item)
            db.session.flush()

            batch = InventoryBatch(
                product_id=product.id,
                supplier_id=supplier_id,
                purchase_item_id=purchase_item.id,
                purchase_rate=float(item['rate']),
                selling_price=product.selling_price,
                qty_purchased=int(item['qty']),
                qty_remaining=int(item['qty']),
                expiry_date=expiry_date
            )
            db.session.add(batch)
            
            product.stock += int(item['qty'])
            
            old_stock = product.stock - int(item['qty'])
            old_value = (product.cost_price or 0) * old_stock
            new_value = old_value + (int(item['qty']) * float(item['rate']))
            product.cost_price = new_value / product.stock if product.stock > 0 else float(item['rate'])

        supplier = Supplier.query.filter_by(shop_id=shop_id, id=supplier_id).first()
        supplier_name = supplier.name if supplier else 'Unknown'
        audit = AuditLog(
            user_id=current_user.id, 
            shop_id=shop_id,
            action=f"Purchase created: Invoice {invoice_no}",
            details=f"Supplier: {supplier_name}, Total: ₹{total_amount}"
        )
        db.session.add(audit)
        db.session.commit()

        flash('Purchase completed and stock updated successfully.', 'success')
        return redirect(url_for('purchase.purchase_list'))

    suppliers = Supplier.query.filter_by(shop_id=shop_id, is_active=True).order_by(Supplier.name).all()
    categories = [row[0] for row in db.session.query(Product.category).distinct().filter(Product.shop_id == shop_id, Product.category.isnot(None)).all()]
    return render_template('purchase/add.html', suppliers=suppliers, categories=categories, datetime=datetime)

@bp.route('/api/products/search')
@login_required
@admin_required
def search_products():
    if current_user.shop_id is None:
        return jsonify([])
    
    shop_id = current_user.shop_id
    query = request.args.get('q', '')
    
    products = Product.query.filter(Product.shop_id == shop_id, Product.name.ilike(f'%{query}%')).limit(10).all()
    results = [{'id': p.id, 'name': p.name, 'sku': p.sku, 'stock': p.stock, 'price': p.selling_price, 'type': 'product'} for p in products]
    
    categories = Product.query.filter(Product.shop_id == shop_id, Product.category.ilike(f'%{query}%')).distinct().all()
    for cat in categories:
        if cat.category:
            results.append({
                'id': None,
                'name': cat.category,
                'type': 'category',
                'product_count': Product.query.filter_by(shop_id=shop_id, category=cat.category).count()
            })
    
    return jsonify(results)

@bp.route('/api/suppliers/search')
@login_required
@admin_required
def search_suppliers():
    if current_user.shop_id is None:
        return jsonify([])
    
    shop_id = current_user.shop_id
    query = request.args.get('q', '')
    suppliers = Supplier.query.filter(Supplier.shop_id == shop_id, Supplier.name.ilike(f'%{query}%')).limit(10).all()
    results = [{'id': s.id, 'name': s.name} for s in suppliers]
    return jsonify(results)

@bp.route('/update-status/<int:id>', methods=['POST'])
@login_required
@admin_required
def update_purchase_status(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    purchase = Purchase.query.filter_by(shop_id=shop_id, id=id).first_or_404()
    new_status = request.form.get('status')
    if new_status in ['Paid', 'Partial', 'Unpaid', 'Cancelled']:
        purchase.payment_status = new_status
        db.session.commit()
        flash(f'Purchase status updated to {new_status}', 'success')
    return redirect(url_for('purchase.purchase_list'))