from app import db
from datetime import datetime

class SaleReturn(db.Model):
    __tablename__ = 'sale_return'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    original_sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    total_refund_amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    return_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    original_sale = db.relationship('Sale', backref='returns')
    items = db.relationship('SaleReturnItem', backref='return_ref', lazy=True)

class SaleReturnItem(db.Model):
    __tablename__ = 'sale_return_item'
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey('shop.id'), nullable=False)
    return_id = db.Column(db.Integer, db.ForeignKey('sale_return.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    refund_amount = db.Column(db.Float, nullable=False)
    
    product = db.relationship('Product')