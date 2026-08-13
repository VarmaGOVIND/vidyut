from app import db
from datetime import datetime

class Sale(db.Model):
    __tablename__ = 'sale'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    invoice_no = db.Column(db.String(50), unique=True, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=True)
    customer_name = db.Column(db.String(100), default='Walk-in Customer')
    status = db.Column(db.String(20), default='Paid')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    discount = db.Column(db.Float, default=0.0)
    tax = db.Column(db.Float, default=0.0)
    
    customer = db.relationship('Customer', backref='sales')
    items = db.relationship('SaleItem', backref='sale', lazy=True)
    shop = db.relationship('Shop', backref='sales')

class SaleItem(db.Model):
    __tablename__ = 'sale_item'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product')
    shop = db.relationship('Shop', backref='sale_items')