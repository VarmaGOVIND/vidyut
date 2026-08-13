from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.customer import Customer, CustomerTransaction
from app.models.sale import Sale
from app.decorators import admin_required
from sqlalchemy import func
from datetime import datetime

bp = Blueprint('customers', __name__, url_prefix='/customers')

@bp.route('/')
@login_required
def customer_list():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    customers = Customer.query.filter_by(shop_id=shop_id, is_active=True).order_by(Customer.name).all()
    return render_template('customers/list.html', customers=customers)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add_customer():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        opening_balance = float(request.form.get('opening_balance', 0))
        
        existing = Customer.query.filter_by(shop_id=shop_id, phone=phone).first()
        if existing:
            flash('Customer with this phone already exists.', 'danger')
            return redirect(url_for('customers.add_customer'))
        
        customer = Customer(
            shop_id=shop_id,
            name=name,
            phone=phone,
            email=email,
            address=address,
            opening_balance=opening_balance
        )
        db.session.add(customer)
        db.session.flush()
        
        if opening_balance > 0:
            transaction = CustomerTransaction(
                shop_id=shop_id,
                customer_id=customer.id,
                amount=opening_balance,
                type='Opening',
                note='Opening balance',
                created_by=current_user.id
            )
            db.session.add(transaction)
        
        db.session.commit()
        flash('Customer added successfully!', 'success')
        return redirect(url_for('customers.customer_list'))
    
    return render_template('customers/add.html')

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_customer(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    customer = Customer.query.filter_by(shop_id=shop_id, id=id).first_or_404()
    
    if request.method == 'POST':
        customer.name = request.form.get('name')
        customer.phone = request.form.get('phone')
        customer.email = request.form.get('email')
        customer.address = request.form.get('address')
        db.session.commit()
        flash('Customer updated successfully!', 'success')
        return redirect(url_for('customers.customer_list'))
    return render_template('customers/edit.html', customer=customer)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_customer(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    customer = Customer.query.filter_by(shop_id=shop_id, id=id).first_or_404()
    sales_count = Sale.query.filter_by(shop_id=shop_id, customer_id=id).count()
    transactions_count = CustomerTransaction.query.filter_by(shop_id=shop_id, customer_id=id).count()
    
    if sales_count > 0 or transactions_count > 0:
        customer.is_active = False
        db.session.commit()
        flash('Customer marked as inactive. Has past sales or transaction records.', 'warning')
    else:
        db.session.delete(customer)
        db.session.commit()
        flash('Customer deleted successfully.', 'success')
    return redirect(url_for('customers.customer_list'))

@bp.route('/ledger/<int:id>')
@login_required
def customer_ledger(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    customer = Customer.query.filter_by(shop_id=shop_id, id=id).first_or_404()
    transactions = CustomerTransaction.query.filter_by(shop_id=shop_id, customer_id=id).order_by(CustomerTransaction.date.desc()).all()
    
    total_sales = sum(t.amount for t in transactions if t.type == 'Sale')
    total_payments = sum(t.amount for t in transactions if t.type == 'Payment')
    total_returns = sum(t.amount for t in transactions if t.type == 'Return')
    balance = customer.opening_balance + total_sales - total_payments - total_returns
    
    return render_template('customers/ledger.html', 
                           customer=customer, 
                           transactions=transactions,
                           balance=balance,
                           total_sales=total_sales,
                           total_payments=total_payments,
                           total_returns=total_returns)

@bp.route('/add_payment/<int:id>', methods=['POST'])
@login_required
def add_payment(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    customer = Customer.query.filter_by(shop_id=shop_id, id=id).first_or_404()
    amount = float(request.form.get('amount'))
    note = request.form.get('note', '')
    
    transaction = CustomerTransaction(
        shop_id=shop_id,
        customer_id=customer.id,
        amount=amount,
        type='Payment',
        note=note,
        created_by=current_user.id
    )
    db.session.add(transaction)
    db.session.commit()
    
    flash(f'Payment of ₹{amount} received from {customer.name}', 'success')
    return redirect(url_for('customers.customer_ledger', id=customer.id))

@bp.route('/api/search')
@login_required
def search_customers():
    if current_user.shop_id is None:
        return jsonify([])
    
    shop_id = current_user.shop_id
    query = request.args.get('q', '')
    customers = Customer.query.filter(
        Customer.shop_id == shop_id,
        Customer.name.ilike(f'%{query}%'),
        Customer.is_active == True
    ).limit(10).all()
    return jsonify([{'id': c.id, 'name': c.name, 'phone': c.phone} for c in customers])