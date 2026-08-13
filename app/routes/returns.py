from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.sale import Sale, SaleItem
from app.models.product import Product
from app.models.return_sale import SaleReturn, SaleReturnItem
from datetime import datetime

bp = Blueprint('returns', __name__, url_prefix='/returns')

@bp.route('/')
@login_required
def return_list():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    returns = SaleReturn.query.filter_by(shop_id=shop_id).order_by(SaleReturn.return_date.desc()).all()
    return render_template('returns/list.html', returns=returns)

@bp.route('/process', methods=['GET', 'POST'])
@login_required
def process_return():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    
    if request.method == 'POST':
        sale_id = request.form.get('sale_id')
        reason = request.form.get('reason')
        items_json = request.form.get('return_items')
        
        sale = Sale.query.filter_by(shop_id=shop_id, id=sale_id).first_or_404()
        return_items = []
        total_refund = 0.0
        
        try:
            items_data = eval(items_json) 
        except:
            flash('Invalid return data.', 'danger')
            return redirect(url_for('returns.process_return'))

        for item_data in items_data:
            if item_data['return_qty'] > 0:
                product = Product.query.get(item_data['product_id'])
                refund_amt = item_data['return_qty'] * item_data['price']
                
                return_items.append({
                    'product_id': product.id,
                    'quantity': item_data['return_qty'],
                    'refund_amount': refund_amt
                })
                total_refund += refund_amt
                
                product.stock += item_data['return_qty']

        if not return_items:
            flash('Please select at least one item to return.', 'warning')
            return redirect(url_for('returns.process_return', sale_id=sale_id))

        sale_return = SaleReturn(
            shop_id=shop_id,
            original_sale_id=sale.id,
            total_refund_amount=total_refund,
            reason=reason,
            processed_by=current_user.id
        )
        db.session.add(sale_return)
        db.session.flush()

        for r_item in return_items:
            db.session.add(SaleReturnItem(
                shop_id=shop_id,
                return_id=sale_return.id,
                product_id=r_item['product_id'],
                quantity=r_item['quantity'],
                refund_amount=r_item['refund_amount']
            ))

        db.session.commit()
        flash('Return processed successfully. Stock and profit adjusted.', 'success')
        return redirect(url_for('returns.return_list'))

    sale_id = request.args.get('sale_id')
    sale = Sale.query.filter_by(shop_id=shop_id, id=sale_id).first_or_404() if sale_id else None
    sale_items = SaleItem.query.filter_by(sale_id=sale.id).all() if sale else []
    
    return render_template('returns/process.html', sale=sale, sale_items=sale_items)

@bp.route('/api/sale/<int:sale_id>')
@login_required
def get_sale_items(sale_id):
    if current_user.shop_id is None:
        return jsonify([])
    
    shop_id = current_user.shop_id
    sale = Sale.query.filter_by(shop_id=shop_id, id=sale_id).first_or_404()
    items = SaleItem.query.filter_by(sale_id=sale_id).all()
    results = [{
        'id': item.id,
        'product_id': item.product_id,
        'name': item.product.name if item.product else 'Unknown',
        'qty': item.quantity,
        'price': item.price
    } for item in items]
    return jsonify(results)