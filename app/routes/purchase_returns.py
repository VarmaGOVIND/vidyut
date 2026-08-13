from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.supplier import Supplier
from app.models.batch import InventoryBatch
from app.models.product import Product
from app.models.purchase import PurchaseReturn, PurchaseReturnItem
from app.models.audit import AuditLog
from app.decorators import admin_required

bp = Blueprint('purchase_returns', __name__, url_prefix='/purchase-returns')

@bp.route('/')
@login_required
def return_list():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    returns = PurchaseReturn.query.filter_by(shop_id=shop_id).order_by(PurchaseReturn.created_at.desc()).all()
    return render_template('purchase_returns/list.html', returns=returns)

@bp.route('/process', methods=['GET', 'POST'])
@login_required
def process_return():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    
    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id')
        reason = request.form.get('reason')
        items_json = request.form.get('return_items')

        if not supplier_id or not items_json:
            flash('Supplier and at least one item are required.', 'danger')
            return redirect(url_for('purchase_returns.process_return'))

        try:
            import json
            items_data = json.loads(items_json)
        except:
            flash('Invalid return data.', 'danger')
            return redirect(url_for('purchase_returns.process_return'))

        return_items = []
        total_amount = 0.0

        for item_data in items_data:
            if item_data['return_qty'] > 0:
                batch = InventoryBatch.query.get(item_data['batch_id'])
                if not batch:
                    continue
                if item_data['return_qty'] > batch.qty_remaining:
                    flash(f"Return quantity cannot exceed remaining stock for batch.", 'danger')
                    return redirect(url_for('purchase_returns.process_return', supplier_id=supplier_id))

                credit_amt = item_data['return_qty'] * item_data['return_rate']
                return_items.append({
                    'batch_id': batch.id,
                    'quantity': item_data['return_qty'],
                    'return_rate': item_data['return_rate'],
                    'credit_amount': credit_amt
                })
                total_amount += credit_amt

                batch.qty_remaining -= item_data['return_qty']

                product = Product.query.get(batch.product_id)
                if product:
                    product.stock -= item_data['return_qty']

        if not return_items:
            flash('Please enter return quantity for at least one item.', 'warning')
            return redirect(url_for('purchase_returns.process_return', supplier_id=supplier_id))

        purchase_return = PurchaseReturn(
            shop_id=shop_id,
            supplier_id=supplier_id,
            total_amount=total_amount,
            reason=reason,
            created_by=current_user.id
        )
        db.session.add(purchase_return)
        db.session.flush()

        for r_item in return_items:
            db.session.add(PurchaseReturnItem(
                shop_id=shop_id,
                return_id=purchase_return.id,
                inventory_batch_id=r_item['batch_id'],
                quantity=r_item['quantity'],
                return_rate=r_item['return_rate']
            ))

        db.session.commit()
        flash('Purchase Return processed successfully. Stock and Supplier Ledger adjusted.', 'success')
        return redirect(url_for('purchase_returns.return_list'))

    supplier_id = request.args.get('supplier_id')
    suppliers = Supplier.query.filter_by(shop_id=shop_id, is_active=True).order_by(Supplier.name).all()
    batches = []
    selected_supplier = None

    if supplier_id:
        selected_supplier = Supplier.query.get(int(supplier_id))
        batches = InventoryBatch.query.filter_by(supplier_id=int(supplier_id)).filter(InventoryBatch.qty_remaining > 0).all()

    return render_template('purchase_returns/process.html',
                           suppliers=suppliers,
                           batches=batches,
                           selected_supplier=selected_supplier)

@bp.route('/api/batches/<int:supplier_id>')
@login_required
def get_batches(supplier_id):
    if current_user.shop_id is None:
        return jsonify([])
    
    shop_id = current_user.shop_id
    supplier = Supplier.query.filter_by(shop_id=shop_id, id=supplier_id).first()
    if not supplier:
        return jsonify([])
    
    batches = InventoryBatch.query.filter_by(supplier_id=supplier_id).filter(InventoryBatch.qty_remaining > 0).all()
    results = []
    for b in batches:
        product = Product.query.get(b.product_id)
        results.append({
            'batch_id': b.id,
            'product_name': product.name if product else 'Unknown',
            'qty_remaining': b.qty_remaining,
            'purchase_rate': b.purchase_rate,
            'purchase_date': b.created_at.strftime('%d %b %Y') if b.created_at else 'N/A'
        })
    return jsonify(results)