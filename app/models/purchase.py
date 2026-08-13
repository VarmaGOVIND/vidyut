from app import db
from datetime import datetime

class Purchase(db.Model):
    __tablename__ = 'purchase'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    invoice_no = db.Column(db.String(50))
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='Paid')
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('PurchaseItem', backref='purchase', lazy=True)
    shop = db.relationship('Shop', backref='purchases')

class PurchaseItem(db.Model):
    __tablename__ = 'purchase_item'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchase.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Float, nullable=False)
    tax = db.Column(db.Float, default=0.0)
    discount = db.Column(db.Float, default=0.0)

    product = db.relationship('Product', backref='purchase_items', lazy=True)
    shop = db.relationship('Shop', backref='purchase_items')

class PurchaseReturn(db.Model):
    __tablename__ = 'purchase_return'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    return_date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    items = db.relationship('PurchaseReturnItem', backref='purchase_return', lazy=True)
    shop = db.relationship('Shop', backref='purchase_returns')

class PurchaseReturnItem(db.Model):
    __tablename__ = 'purchase_return_item'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    return_id = db.Column(db.Integer, db.ForeignKey('purchase_return.id'), nullable=False)
    inventory_batch_id = db.Column(db.Integer, db.ForeignKey('inventory_batch.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    return_rate = db.Column(db.Float, nullable=False)
    
    shop = db.relationship('Shop', backref='purchase_return_items')