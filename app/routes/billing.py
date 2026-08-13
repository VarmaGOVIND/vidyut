from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.audit import AuditLog
from app.models.batch import InventoryBatch
from app.models.supplier import Supplier
from app.models.settings import ShopSettings
from app.models.customer import Customer, CustomerTransaction
from datetime import datetime,date
import uuid

bp = Blueprint('billing', __name__)

@bp.route('/pos')
@login_required
def pos():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_settings = ShopSettings.query.first()
    return render_template('billing/pos.html', shop_settings=shop_settings)

@bp.route('/api/products/search')
@login_required
def search_products():
    if current_user.shop_id is None:
        return jsonify([])
    
    shop_id = current_user.shop_id
    query = request.args.get('q', '').strip()
    if not query:
        return jsonify([])

    products = Product.query.filter(
        Product.shop_id == shop_id,
        (Product.name.ilike(f'%{query}%')) | (Product.sku.ilike(f'%{query}%'))
    ).all()

    results = []
    today = date.today()
    for p in products:
        batches = InventoryBatch.query.filter_by(product_id=p.id).all()

        if not batches:
            is_expired = p.expiry_date and p.expiry_date < today
            results.append({
                'batch_id': None,
                'product_id': p.id,
                'sku': p.sku,
                'name': p.name,
                'supplier': 'N/A',
                'price': p.selling_price,
                'cost_price': p.cost_price,
                'stock': 0,
                'expiry_date': p.expiry_date.strftime('%Y-%m-%d') if p.expiry_date else None,
                'is_expired': is_expired
            })
        else:
            for batch in batches:
                is_expired = p.expiry_date and p.expiry_date < today
                results.append({
                    'batch_id': batch.id,
                    'product_id': p.id,
                    'sku': p.sku,
                    'name': p.name,
                    'supplier': batch.supplier.name if batch.supplier else 'N/A',
                    'price': batch.selling_price or p.selling_price or 0,
                    'cost_price': batch.purchase_rate,
                    'stock': batch.qty_remaining,
                    'expiry_date': p.expiry_date.strftime('%Y-%m-%d') if p.expiry_date else None,
                    'is_expired': is_expired
                })

    return jsonify(results)

@bp.route('/api/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json()
    batch_id = data.get('batch_id')
    product_id = data.get('product_id')
    
    batch = InventoryBatch.query.get(batch_id)
    if not batch or batch.qty_remaining <= 0:
        return jsonify({'error': 'Batch not found or out of stock'}), 400
    
    product = Product.query.get(product_id)
    if product and product.shop_id != current_user.shop_id:
        return jsonify({'error': 'Product does not belong to your shop'}), 403

    cart = session.get('cart', [])
    found = False
    
    for item in cart:
        if item['batch_id'] == batch_id:
            if item['qty'] < batch.qty_remaining:
                item['qty'] += 1
            found = True
            break
            
    if not found:
        cart.append({
            'batch_id': batch.id,
            'id': product_id,
            'name': batch.product.name,
            'price': batch.product.selling_price, 
            'cost_price': batch.purchase_rate,
            'qty': 1, 
            'stock': batch.qty_remaining
        })
        
    session['cart'] = cart
    session.modified = True
    return jsonify({'cart': cart, 'total': sum(i['price'] * i['qty'] for i in cart)})

@bp.route('/api/cart/update', methods=['POST'])
@login_required
def update_cart():
    data = request.get_json()
    action = data.get('action')
    
    if action == 'clear_all':
        session.pop('cart', None)
        session.modified = True
        return jsonify({'cart': [], 'total': 0.0})

    batch_id = data.get('batch_id')
    cart = session.get('cart', [])

    for item in cart:
        if batch_id and item['batch_id'] == batch_id:
            max_stock = item.get('stock', 9999)
            if action == 'increase' and item['qty'] < max_stock:
                item['qty'] += 1
            elif action == 'decrease' and item['qty'] > 1:
                item['qty'] -= 1
            elif action == 'remove':
                cart.remove(item)
            break
            
    session['cart'] = cart
    session.modified = True
    return jsonify({'cart': cart, 'total': sum(i['price'] * i['qty'] for i in cart)})

@bp.route('/api/checkout', methods=['POST'])
@login_required
def checkout():
    if current_user.shop_id is None:
        return jsonify({'error': 'No shop found'}), 400
    
    shop_id = current_user.shop_id
    
    try:
        cart = session.get('cart', [])
        if not cart:
            return jsonify({'error': 'Cart is empty'}), 400

        data = request.get_json()
        discount_amount = float(data.get('discount', 0))
        tax_amount = float(data.get('tax', 0))
        customer_id = data.get('customer_id')
        today = date.today()
        
        for item in cart:
            product = Product.query.filter_by(shop_id=shop_id, id=item['id']).first()
            if product and product.expiry_date and product.expiry_date < today:
                return jsonify({'error': f'"{product.name}" is expired and cannot be sold.'}), 400

        invoice_no = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        subtotal = sum(item['price'] * item['qty'] for item in cart)
        total_amount = subtotal - discount_amount + tax_amount
        
        total_profit = sum((item['price'] - item.get('cost_price', 0)) * item['qty'] for item in cart)

        customer = None
        if customer_id:
            customer = Customer.query.filter_by(shop_id=shop_id, id=customer_id).first()
        
        sale = Sale(
            shop_id=shop_id,
            invoice_no=invoice_no, 
            total_amount=total_amount, 
            profit=total_profit,
            customer_id=customer_id,
            customer_name=customer.name if customer else 'Walk-in Customer',
            discount=discount_amount,
            tax=tax_amount
        )
        db.session.add(sale)
        db.session.flush()
        
        if customer_id and customer:
            transaction = CustomerTransaction(
                shop_id=shop_id,
                customer_id=customer.id,
                sale_id=sale.id,
                amount=total_amount,
                type='Sale',
                note=f'Invoice: {invoice_no}',
                created_by=current_user.id
            )
            db.session.add(transaction)

        for item in cart:
            batch = InventoryBatch.query.get(item['batch_id'])
            if not batch:
                db.session.rollback()
                return jsonify({'error': f"Batch not found for {item['name']}"}), 400
                
            if batch.qty_remaining < item['qty']:
                db.session.rollback()
                return jsonify({'error': f"Insufficient stock for {item['name']}"}), 400

            sale_item = SaleItem(
                shop_id=shop_id,
                sale_id=sale.id,
                product_id=item['id'],
                quantity=item['qty'],
                price=item['price'],
                cost_price=item.get('cost_price', 0)
            )
            db.session.add(sale_item)
            
            batch.qty_remaining -= item['qty']
            
            product = Product.query.filter_by(shop_id=shop_id, id=item['id']).first()
            if product:
                product.stock -= item['qty']

        session['cart'] = []
        session.modified = True
        db.session.commit()

        return jsonify({'success': True, 'invoice': invoice_no, 'sale_id': sale.id})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/invoice/<invoice_id>')
@login_required
def view_invoice(invoice_id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    sale = Sale.query.filter_by(shop_id=shop_id, invoice_no=invoice_id).first()
    if not sale:
        try:
            sale = Sale.query.get(int(invoice_id))
            if sale and sale.shop_id != shop_id:
                sale = None
        except (ValueError, TypeError):
            sale = None
    
    if not sale:
        flash('Invoice not found', 'danger')
        return redirect(url_for('billing.pos'))
        
    items = SaleItem.query.filter_by(shop_id=shop_id, sale_id=sale.id).all()
    shop = ShopSettings.query.first()
    
    return render_template('billing/invoice.html', sale=sale, items=items, shop=shop)

@bp.route('/api/sale_by_invoice')
@login_required
def get_sale_by_invoice():
    if current_user.shop_id is None:
        return jsonify({'error': 'No shop'}), 400
    
    shop_id = current_user.shop_id
    invoice_no = request.args.get('invoice', '')
    sale = Sale.query.filter_by(shop_id=shop_id, invoice_no=invoice_no).first()
    
    if not sale:
        return jsonify({'error': 'Invoice not found'})
    
    items = SaleItem.query.filter_by(shop_id=shop_id, sale_id=sale.id).all()
    return jsonify({
        'id': sale.id,
        'invoice_no': sale.invoice_no,
        'date': sale.created_at.strftime('%d %b %Y'),
        'items': [{
            'product_id': item.product_id,
            'name': item.product.name if item.product else 'Unknown',
            'qty': item.quantity,
            'price': item.price
        } for item in items]
    })