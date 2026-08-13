from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.supplier import Supplier
from app.models.purchase import Purchase
from app.models.supplier_payment import SupplierPayment
from sqlalchemy import func
from datetime import datetime

bp = Blueprint('ledger', __name__, url_prefix='/ledger')

@bp.route('/')
@login_required
def ledger_dashboard():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    suppliers = Supplier.query.filter_by(shop_id=shop_id, is_active=True).all()
    supplier_data = []
    
    for s in suppliers:
        total_purchased = db.session.query(func.sum(Purchase.total_amount)).filter(
            Purchase.shop_id == shop_id,
            Purchase.supplier_id == s.id,
            Purchase.payment_status != 'Cancelled'
        ).scalar() or 0.0
        
        paid_via_purchase = db.session.query(func.sum(Purchase.total_amount)).filter(
            Purchase.shop_id == shop_id,
            Purchase.supplier_id == s.id,
            db.func.lower(Purchase.payment_status) == 'paid'
        ).scalar() or 0.0
        
        manual_payments = db.session.query(func.sum(SupplierPayment.amount)).filter(
            SupplierPayment.shop_id == shop_id,
            SupplierPayment.supplier_id == s.id,
            SupplierPayment.type == 'Payment'
        ).scalar() or 0.0
        
        manual_refunds = db.session.query(func.sum(SupplierPayment.amount)).filter(
            SupplierPayment.shop_id == shop_id,
            SupplierPayment.supplier_id == s.id,
            SupplierPayment.type == 'Refund'
        ).scalar() or 0.0
        
        total_paid = (paid_via_purchase + manual_payments) - manual_refunds
        pending = total_purchased - total_paid
        
        supplier_data.append({
            'supplier': s,
            'total_purchased': total_purchased,
            'total_paid': total_paid,
            'pending': pending
        })
        
    return render_template('ledger/dashboard.html', supplier_data=supplier_data)

@bp.route('/supplier/<int:supplier_id>')
@login_required
def supplier_statement(supplier_id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    supplier = Supplier.query.filter_by(shop_id=shop_id, id=supplier_id).first_or_404()
    
    purchases = Purchase.query.filter_by(shop_id=shop_id, supplier_id=supplier_id).order_by(Purchase.purchase_date.asc()).all()
    payments = SupplierPayment.query.filter_by(shop_id=shop_id, supplier_id=supplier_id).order_by(SupplierPayment.payment_date.asc()).all()
    
    transactions = []
    for p in purchases:
        transactions.append({
            'date': p.purchase_date,
            'type': 'Purchase',
            'ref': p.invoice_no or f"#{p.id}",
            'debit': p.total_amount,
            'credit': 0.0
        })
        
    for pay in payments:
        is_refund = (pay.type == 'Refund')
        transactions.append({
            'date': pay.payment_date,
            'type': 'Refund' if is_refund else 'Payment',
            'ref': pay.method,
            'debit': pay.amount if is_refund else 0.0,
            'credit': pay.amount if not is_refund else 0.0
        })
        
    transactions.sort(key=lambda x: x['date'] or datetime(1900, 1, 1))
    
    total_debit = sum(t['debit'] for t in transactions)
    total_credit = sum(t['credit'] for t in transactions)
    current_balance = total_debit - total_credit
    
    return render_template('ledger/statement.html', 
                           supplier=supplier, 
                           transactions=transactions, 
                           total_debit=total_debit, 
                           total_credit=total_credit, 
                           current_balance=current_balance)

@bp.route('/add_payment', methods=['GET', 'POST'])
@login_required
def add_payment():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    
    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id')
        amount = float(request.form.get('amount'))
        payment_date_str = request.form.get('payment_date')
        method = request.form.get('method')
        note = request.form.get('note')
        
        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d') if payment_date_str else datetime.utcnow()
        
        payment = SupplierPayment(
            shop_id=shop_id,
            supplier_id=supplier_id, 
            amount=amount, 
            payment_date=payment_date,
            method=method, 
            note=note, 
            created_by=current_user.id, 
            type='Payment'
        )
        db.session.add(payment)
        db.session.commit()
        flash('Payment recorded successfully!', 'success')
        return redirect(url_for('ledger.ledger_dashboard'))
        
    suppliers = Supplier.query.filter_by(shop_id=shop_id, is_active=True).order_by(Supplier.name).all()
    return render_template('ledger/add_payment.html', suppliers=suppliers)

@bp.route('/add_refund', methods=['GET', 'POST'])
@login_required
def add_refund():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    
    if request.method == 'POST':
        supplier_id = request.form.get('supplier_id')
        amount = float(request.form.get('amount'))
        payment_date_str = request.form.get('payment_date')
        method = request.form.get('method')
        note = request.form.get('note')
        
        payment_date = datetime.strptime(payment_date_str, '%Y-%m-%d') if payment_date_str else datetime.utcnow()
        
        refund = SupplierPayment(
            shop_id=shop_id,
            supplier_id=supplier_id, 
            amount=amount, 
            payment_date=payment_date,
            method=method, 
            note=note, 
            created_by=current_user.id, 
            type='Refund'
        )
        db.session.add(refund)
        db.session.commit()
        flash('Supplier Refund recorded successfully! Balance updated.', 'success')
        return redirect(url_for('ledger.ledger_dashboard'))
        
    suppliers = Supplier.query.filter_by(shop_id=shop_id, is_active=True).order_by(Supplier.name).all()
    return render_template('ledger/add_refund.html', suppliers=suppliers)

@bp.route('/api/supplier_refund_balance/<int:supplier_id>')
@login_required
def get_supplier_refund_balance(supplier_id):
    if current_user.shop_id is None:
        return jsonify({'error': 'No shop'}), 400
    
    shop_id = current_user.shop_id
    supplier = Supplier.query.filter_by(shop_id=shop_id, id=supplier_id).first_or_404()
    
    total_purchased = db.session.query(func.sum(Purchase.total_amount)).filter(
        Purchase.shop_id == shop_id,
        Purchase.supplier_id == supplier_id,
        Purchase.payment_status != 'Cancelled'
    ).scalar() or 0.0
    
    paid_via_purchase = db.session.query(func.sum(Purchase.total_amount)).filter(
        Purchase.shop_id == shop_id,
        Purchase.supplier_id == supplier_id,
        db.func.lower(Purchase.payment_status) == 'paid'
    ).scalar() or 0.0
    
    manual_payments = db.session.query(func.sum(SupplierPayment.amount)).filter(
        SupplierPayment.shop_id == shop_id,
        SupplierPayment.supplier_id == supplier_id,
        SupplierPayment.type == 'Payment'
    ).scalar() or 0.0
    
    manual_refunds = db.session.query(func.sum(SupplierPayment.amount)).filter(
        SupplierPayment.shop_id == shop_id,
        SupplierPayment.supplier_id == supplier_id,
        SupplierPayment.type == 'Refund'
    ).scalar() or 0.0
    
    total_paid = (paid_via_purchase + manual_payments) - manual_refunds
    pending_balance = total_purchased - total_paid
    
    refund_due = abs(pending_balance) if pending_balance < 0 else 0.0
    
    return jsonify({
        'supplier_name': supplier.name,
        'pending_balance': pending_balance,
        'refund_due': refund_due
    })

@bp.route('/history')
@login_required
def payment_history():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    transactions = SupplierPayment.query.filter_by(shop_id=shop_id).order_by(SupplierPayment.payment_date.desc()).all()
    return render_template('ledger/payment_history.html', transactions=transactions)