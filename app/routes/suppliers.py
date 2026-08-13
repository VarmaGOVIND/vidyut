from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.supplier import Supplier
from app.models.purchase import Purchase
from app.decorators import admin_required

bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

@bp.route('/list')
@login_required
@admin_required
def supplier_list():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    suppliers = Supplier.query.filter_by(shop_id=shop_id).order_by(Supplier.name).all()
    return render_template('suppliers/list.html', suppliers=suppliers)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_supplier():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        gstin = request.form.get('gstin')
        
        supplier = Supplier(
            shop_id=shop_id,
            name=name,
            phone=phone,
            email=email,
            address=address,
            gstin=gstin
        )
        db.session.add(supplier)
        db.session.commit()
        
        flash('Supplier added successfully', 'success')
        return redirect(url_for('suppliers.supplier_list'))
    
    return render_template('suppliers/form.html', supplier=None)

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_supplier(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    supplier = Supplier.query.filter_by(shop_id=shop_id, id=id).first_or_404()
    
    if request.method == 'POST':
        supplier.name = request.form.get('name')
        supplier.phone = request.form.get('phone')
        supplier.email = request.form.get('email')
        supplier.address = request.form.get('address')
        supplier.gstin = request.form.get('gstin')
        
        db.session.commit()
        flash('Supplier updated successfully', 'success')
        return redirect(url_for('suppliers.supplier_list'))
    
    return render_template('suppliers/form.html', supplier=supplier)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_supplier(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    supplier = Supplier.query.filter_by(shop_id=shop_id, id=id).first_or_404()
    db.session.delete(supplier)
    db.session.commit()
    flash('Supplier deleted successfully', 'success')
    return redirect(url_for('suppliers.supplier_list'))

@bp.route('/<int:id>')
@login_required
@admin_required
def supplier_detail(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    supplier = Supplier.query.filter_by(shop_id=shop_id, id=id).first_or_404()
    purchases = Purchase.query.filter_by(shop_id=shop_id, supplier_id=id).order_by(Purchase.purchase_date.desc()).all()
    return render_template('suppliers/detail.html', supplier=supplier, purchases=purchases)