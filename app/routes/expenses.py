from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db
from app.models.expense import Expense
from app.decorators import admin_required
from datetime import datetime

bp = Blueprint('expenses', __name__, url_prefix='/expenses')

@bp.route('/')
@login_required
@admin_required
def expense_list():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    expenses = Expense.query.filter_by(shop_id=shop_id).order_by(Expense.expense_date.desc()).all()
    return render_template('expenses/list.html', expenses=expenses)

@bp.route('/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_expense():
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    
    if request.method == 'POST':
        category = request.form.get('category')
        description = request.form.get('description')
        amount = float(request.form.get('amount'))
        date_str = request.form.get('expense_date')
        
        expense_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
        
        expense = Expense(
            shop_id=shop_id,
            category=category,
            description=description,
            amount=amount,
            expense_date=expense_date,
            created_by=current_user.id
        )
        db.session.add(expense)
        db.session.commit()
        
        flash('Expense added successfully!', 'success')
        return redirect(url_for('expenses.expense_list'))
        
    return render_template('expenses/add.html')

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_expense(id):
    if current_user.shop_id is None:
        return redirect(url_for('shop.create_shop'))
    
    shop_id = current_user.shop_id
    expense = Expense.query.filter_by(shop_id=shop_id, id=id).first_or_404()
    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('expenses.expense_list'))